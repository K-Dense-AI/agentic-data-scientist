"""
Custom stage orchestrator agent for Agentic Data Scientist.

This module provides a custom orchestrator that feeds high-level stages one at a time
to the implementation loop, checks success criteria after each stage, and adapts
remaining stages through reflection.
"""

import logging
from typing import Any, AsyncGenerator, Dict, List

from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types
from pydantic import PrivateAttr

from agentic_data_scientist.agents.adk.event_compression import compress_events_manually


logger = logging.getLogger(__name__)


def format_criteria_status(criteria: List[Dict], max_length: int = 80) -> str:
    """
    Format criteria list for readable logging.

    Parameters
    ----------
    criteria : List[Dict]
        List of criteria dictionaries with 'index', 'criteria', and 'met' fields
    max_length : int, optional
        Maximum length for criteria text before truncation (default: 80)

    Returns
    -------
    str
        Formatted multi-line string showing each criterion with status
    """
    if not criteria:
        return "  (No criteria defined)"

    lines = []
    for c in criteria:
        status = "✅ MET" if c.get("met", False) else "❌ NOT MET"
        criteria_text = c.get("criteria", "Unknown criterion")

        # Truncate long criteria text
        if len(criteria_text) > max_length:
            criteria_text = criteria_text[:max_length] + "..."

        lines.append(f"  [{status}] Criterion {c.get('index', '?')}: {criteria_text}")

    return "\n".join(lines)


class StageOrchestratorAgent(BaseAgent):
    """
    Custom orchestrator that manages stage-by-stage implementation.

    This agent feeds high-level stages one at a time to the implementation loop,
    then checks success criteria and reflects on remaining stages after each iteration.
    The workflow exits when all success criteria are met.

    Parameters
    ----------
    implementation_loop : BaseAgent
        The agent that implements each stage (coding + review loop)
    criteria_checker : BaseAgent
        Agent that checks which success criteria have been met
    stage_reflector : BaseAgent
        Agent that reflects on and adapts remaining stages
    name : str, optional
        Agent name (default: "stage_orchestrator")
    description : str, optional
        Agent description
    """

    # Use PrivateAttr for agent references since they shouldn't be serialized
    _implementation_loop: Any = PrivateAttr()
    _criteria_checker: Any = PrivateAttr()
    _stage_reflector: Any = PrivateAttr()

    def __init__(
        self,
        implementation_loop: BaseAgent,
        criteria_checker: BaseAgent,
        stage_reflector: BaseAgent,
        name: str = "stage_orchestrator",
        description: str = "Orchestrates stage-by-stage implementation with criteria checking",
    ):
        super().__init__(name=name, description=description)
        self._implementation_loop = implementation_loop
        self._criteria_checker = criteria_checker
        self._stage_reflector = stage_reflector

    @property
    def implementation_loop(self) -> BaseAgent:
        """Get the implementation loop agent."""
        return self._implementation_loop

    @property
    def criteria_checker(self) -> BaseAgent:
        """Get the criteria checker agent."""
        return self._criteria_checker

    @property
    def stage_reflector(self) -> BaseAgent:
        """Get the stage reflector agent."""
        return self._stage_reflector

    def _apply_terminal_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute the terminal run status from the current state and persist it.

        The status reflects what actually happened rather than always reporting
        success:

        - ``completed``: every success criterion was met and every attempted
          stage was approved by review.
        - ``completed_with_warnings``: every success criterion was met, but at
          least one stage finished without explicit review approval.
        - ``incomplete``: at least one success criterion was not met.

        Writes ``run_status`` plus human-readable ``unmet_criteria_summary`` and
        ``unapproved_stages_summary`` keys to state so downstream agents (the
        summary agent) and the API layer can surface them.

        Parameters
        ----------
        state : Dict[str, Any]
            The mutable session state.

        Returns
        -------
        Dict[str, Any]
            ``{"run_status": str, "unmet": List[Dict], "unapproved": List[Dict]}``
        """
        criteria: List[Dict] = state.get("high_level_success_criteria", []) or []
        stages: List[Dict] = state.get("high_level_stages", []) or []

        unmet = [c for c in criteria if not c.get("met", False)]
        # Only stages that were actually attempted carry an "approved" flag.
        attempted = [s for s in stages if "approved" in s]
        unapproved = [s for s in attempted if not s.get("approved", False)]

        all_criteria_met = bool(criteria) and not unmet
        if all_criteria_met and not unapproved:
            run_status = "completed"
        elif all_criteria_met and unapproved:
            run_status = "completed_with_warnings"
        else:
            run_status = "incomplete"

        state["run_status"] = run_status
        state["unmet_criteria_summary"] = (
            "\n".join(f"  - Criterion {c.get('index', '?')}: {c.get('criteria', 'Unknown criterion')}" for c in unmet)
            if unmet
            else "None - all success criteria were met."
        )
        state["unapproved_stages_summary"] = (
            "\n".join(f"  - Stage {s.get('index', '?')}: {s.get('title', 'Unknown')}" for s in unapproved)
            if unapproved
            else "None - all attempted stages were approved by review."
        )

        logger.info(
            f"[StageOrchestrator] Terminal run status: {run_status} "
            f"({len(unmet)} unmet criteria, {len(unapproved)} unapproved stages)"
        )
        return {"run_status": run_status, "unmet": unmet, "unapproved": unapproved}

    @staticmethod
    def _format_status_block(info: Dict[str, Any]) -> str:
        """Build a user-facing text block listing unmet criteria and unapproved stages."""
        lines: List[str] = []
        unmet = info.get("unmet", [])
        unapproved = info.get("unapproved", [])

        if unmet:
            lines.append(f"Unmet success criteria ({len(unmet)}):")
            lines.extend(f"  - {c.get('criteria', 'Unknown criterion')}" for c in unmet)
        if unapproved:
            if lines:
                lines.append("")
            lines.append(f"Stages completed without review approval ({len(unapproved)}):")
            lines.extend(f"  - Stage {s.get('index', '?')}: {s.get('title', 'Unknown')}" for s in unapproved)

        return "\n".join(lines)

    @staticmethod
    def _status_state_delta(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a state_delta of status keys for the terminal event.

        Direct mutations to ``ctx.session.state`` are only visible within the
        running invocation; persisting the status through ``EventActions.state_delta``
        ensures the API layer can read it from the session service after the run.
        """
        delta: Dict[str, Any] = {}
        for key in ("run_status", "unmet_criteria_summary", "unapproved_stages_summary"):
            if key in state:
                delta[key] = state[key]
        return delta

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Main orchestration logic.

        Implements the core control flow:
        1. Check if all criteria are met -> exit if yes
        2. Get next uncompleted stage
        3. Run implementation_loop for that stage
        4. Run criteria_checker to update criteria status
        5. Run stage_reflector to adapt remaining stages
        6. Repeat

        Parameters
        ----------
        ctx : InvocationContext
            The invocation context with session access

        Yields
        ------
        Event
            Events from sub-agents and orchestration status updates
        """
        state = ctx.session.state

        # Initialize/clear stage-specific state keys
        if "current_stage" not in state:
            state["current_stage"] = None
        if "current_stage_index" not in state:
            state["current_stage_index"] = 0
        if "stage_implementations" not in state:
            state["stage_implementations"] = []

        # Get stages and criteria from state
        stages: List[Dict] = state.get("high_level_stages", [])
        criteria: List[Dict] = state.get("high_level_success_criteria", [])

        # Validate stages
        if not stages or len(stages) == 0:
            logger.error("[StageOrchestrator] No stages found in state!")
            state["run_status"] = "incomplete"
            error_event = Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="\n\n[ERROR] No high-level stages found in state. "
                            "Cannot proceed with orchestration.\n\n"
                        )
                    ],
                ),
                actions=EventActions(state_delta=self._status_state_delta(state)),
                turn_complete=True,
            )
            yield error_event
            return

        # Validate stages structure (check first few stages)
        stages_to_check = min(3, len(stages))
        for i in range(stages_to_check):
            stage = stages[i]
            if not isinstance(stage, dict) or "index" not in stage or "title" not in stage:
                logger.error(f"[StageOrchestrator] Stages have invalid structure at index {i}!")
                state["run_status"] = "incomplete"
                error_event = Event(
                    author=self.name,
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=f"\n\n[ERROR] High-level stages have invalid structure. "
                                f"Stage at index {i} is missing required fields.\n\n"
                            )
                        ],
                    ),
                    actions=EventActions(state_delta=self._status_state_delta(state)),
                    turn_complete=True,
                )
                yield error_event
                return

        # Validate criteria
        if not criteria or len(criteria) == 0:
            logger.error("[StageOrchestrator] No success criteria found in state!")
            state["run_status"] = "incomplete"
            error_event = Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="\n\n[ERROR] No success criteria found in state. "
                            "Cannot proceed with orchestration.\n\n"
                        )
                    ],
                ),
                actions=EventActions(state_delta=self._status_state_delta(state)),
                turn_complete=True,
            )
            yield error_event
            return

        # Validate criteria structure (check first few criteria)
        criteria_to_check = min(3, len(criteria))
        for i in range(criteria_to_check):
            criterion = criteria[i]
            if not isinstance(criterion, dict) or "index" not in criterion or "criteria" not in criterion:
                logger.error(f"[StageOrchestrator] Criteria have invalid structure at index {i}!")
                state["run_status"] = "incomplete"
                error_event = Event(
                    author=self.name,
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=f"\n\n[ERROR] Success criteria have invalid structure. "
                                f"Criterion at index {i} is missing required fields.\n\n"
                            )
                        ],
                    ),
                    actions=EventActions(state_delta=self._status_state_delta(state)),
                    turn_complete=True,
                )
                yield error_event
                return

        logger.info(f"[StageOrchestrator] Starting orchestration with {len(stages)} stages")
        logger.info(f"[StageOrchestrator] Success criteria count: {len(criteria)}")

        # Log all success criteria at the start for visibility
        logger.info("[StageOrchestrator] Success Criteria (End-State Goals):")
        logger.info(format_criteria_status(criteria))
        logger.info(
            "[StageOrchestrator] Note: These are end-state goals that will be progressively "
            "met as stages complete. Early 'NOT MET' status is expected and normal."
        )

        # Initialize stage_implementations if not exists
        if "stage_implementations" not in state:
            state["stage_implementations"] = []

        # Main orchestration loop
        iteration = 0
        max_iterations = 50  # Safety limit to prevent infinite loops

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"[StageOrchestrator] === Orchestration iteration {iteration} ===")

            # Refresh state objects (they may have been modified by callbacks)
            stages = state.get("high_level_stages", [])
            criteria = state.get("high_level_success_criteria", [])

            # Check exit condition: all criteria met?
            criteria_met_count = sum(1 for c in criteria if c.get("met", False))
            logger.info(f"[StageOrchestrator] Criteria status: {criteria_met_count}/{len(criteria)} met")

            if all(c.get("met", False) for c in criteria):
                info = self._apply_terminal_status(state)
                run_status = info["run_status"]
                logger.info(
                    f"[StageOrchestrator] 🎉 All success criteria met! Exiting to summary (status={run_status})."
                )

                status_block = self._format_status_block(info)
                if run_status == "completed":
                    header = (
                        f"\n\n✅ All {len(criteria)} high-level success criteria have been met. "
                        "Proceeding to final summary generation.\n\n"
                    )
                else:
                    header = (
                        f"\n\n✅ All {len(criteria)} high-level success criteria have been met, but some stages "
                        f"completed without explicit review approval (status: {run_status}). "
                        "Proceeding to final summary generation.\n\n"
                    )

                # Create completion event
                completion_event = Event(
                    author=self.name,
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=header + (status_block + "\n\n" if status_block else ""))],
                    ),
                    actions=EventActions(state_delta=self._status_state_delta(state)),
                    turn_complete=True,
                )
                yield completion_event
                return

            # Get next uncompleted stage
            remaining_stages = [s for s in stages if not s.get("completed", False)]

            if not remaining_stages:
                logger.warning(
                    "[StageOrchestrator] No remaining stages but criteria not met. Asking reflector to extend stages."
                )

                # Run reflector to extend stages if needed
                logger.info("[StageOrchestrator] Running stage_reflector to extend plan...")
                async for event in self.stage_reflector.run_async(ctx):
                    yield event

                # Refresh stages from state (reflector may have modified them)
                stages = state.get("high_level_stages", [])
                remaining_stages = [s for s in stages if not s.get("completed", False)]

                if not remaining_stages:
                    info = self._apply_terminal_status(state)
                    logger.error(
                        "[StageOrchestrator] Still no stages after reflection. "
                        f"Exiting despite incomplete criteria (status={info['run_status']})."
                    )
                    status_block = self._format_status_block(info)
                    warning_event = Event(
                        author=self.name,
                        content=types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text="\n\n⚠️ No remaining stages to implement, but not all "
                                    f"success criteria are met (status: {info['run_status']}). "
                                    "Proceeding to summary.\n\n" + (status_block + "\n\n" if status_block else "")
                                )
                            ],
                        ),
                        actions=EventActions(state_delta=self._status_state_delta(state)),
                        turn_complete=True,
                    )
                    yield warning_event
                    return

            # Get next stage to implement
            next_stage = remaining_stages[0]
            stage_idx = next_stage["index"]

            logger.info(f"[StageOrchestrator] 📍 Starting stage {stage_idx}: {next_stage['title']}")

            # Create stage start event
            stage_start_event = Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=f"\n\n### Stage {stage_idx + 1}: {next_stage['title']}\n\n"
                            f"{next_stage['description']}\n\n"
                            "Beginning implementation...\n\n"
                        )
                    ],
                ),
                partial=False,
            )
            yield stage_start_event

            # Set current stage in state (for implementation loop to read)
            state["current_stage"] = {
                "index": next_stage["index"],
                "title": next_stage["title"],
                "description": next_stage["description"],
            }

            # Clear previous implementation outputs (including the prior stage's
            # review-approval decision, so a stale approval can't bleed into this stage).
            state.pop("implementation_summary", None)
            state.pop("review_feedback", None)
            state.pop("implementation_review_confirmation_decision", None)

            # === Run Implementation Loop ===
            logger.info("")
            logger.info("")
            logger.info("")
            logger.info(f"[StageOrchestrator] Running implementation_loop for stage {stage_idx}")

            try:
                async for event in self.implementation_loop.run_async(ctx):
                    yield event

                logger.info(f"[StageOrchestrator] Completed implementation_loop for stage {stage_idx}")

                # === Manual Event Compression After Implementation Loop ===
                logger.info("[StageOrchestrator] Running manual event compression after implementation loop")
                try:
                    await compress_events_manually(
                        ctx=ctx,
                        event_threshold=40,
                        overlap_size=20,
                    )
                except Exception as compress_err:
                    logger.warning(f"[StageOrchestrator] Manual compression failed: {compress_err}")

            except Exception as e:
                logger.error(
                    f"[StageOrchestrator] Implementation loop failed for stage {stage_idx}: {e}",
                    exc_info=True,
                )
                error_event = Event(
                    author=self.name,
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=f"\n\n❌ Implementation loop failed for stage {stage_idx} "
                                f"({next_stage['title']}): {str(e)}\n\n"
                                "Skipping to next stage...\n\n"
                            )
                        ],
                    ),
                    turn_complete=True,
                )
                yield error_event
                # Skip this stage and continue to next
                continue

            # Determine whether the implementation review actually approved this stage.
            # The implementation_review_confirmation agent writes its decision to
            # "implementation_review_confirmation_decision" as {"exit": bool, "reason": str}.
            # exit=True means review approved and the loop exited; a missing decision or
            # exit=False means the loop exhausted its iterations (or was halted) without approval.
            decision = state.get("implementation_review_confirmation_decision")
            stage_approved = isinstance(decision, dict) and decision.get("exit", False) is True
            approval_reason = decision.get("reason", "") if isinstance(decision, dict) else ""
            if stage_approved:
                logger.info(
                    f"[StageOrchestrator] Stage {stage_idx} implementation approved by review. "
                    f"Reason: {approval_reason}"
                )
            else:
                logger.warning(
                    f"[StageOrchestrator] Stage {stage_idx} implementation NOT approved by review "
                    "(implementation loop exhausted its iterations or was halted). "
                    f"Reason: {approval_reason or 'no approval recorded'}"
                )

            # Store implementation result and approval outcome (but don't mark as completed yet)
            next_stage["implementation_result"] = state.get("implementation_summary", "")
            next_stage["approved"] = stage_approved
            next_stage["status"] = "approved" if stage_approved else "needs_work"

            # Add to completed stages history BEFORE running checker/reflector
            # so they can see the current stage in their prompts
            stage_implementations = state.get("stage_implementations", [])
            stage_implementations.append(
                {
                    "stage_index": next_stage["index"],
                    "stage_title": next_stage["title"],
                    "implementation_summary": next_stage["implementation_result"],
                    "approved": stage_approved,
                }
            )
            state["stage_implementations"] = stage_implementations

            # === Run Success Criteria Checker ===
            logger.info("")
            logger.info("")
            logger.info("")
            logger.info(f"[StageOrchestrator] Running criteria_checker after stage {stage_idx}")

            try:
                async for event in self.criteria_checker.run_async(ctx):
                    yield event

                # Criteria checker updates state["high_level_success_criteria"] via callback
                criteria = state.get("high_level_success_criteria", [])

                criteria_met_count = sum(1 for c in criteria if c.get("met", False))
                logger.info(
                    f"[StageOrchestrator] Criteria status after check: {criteria_met_count}/{len(criteria)} met"
                )
            except Exception as e:
                logger.error(
                    f"[StageOrchestrator] Criteria checker failed for stage {stage_idx}: {e}",
                    exc_info=True,
                )
                # Log error but continue - criteria check is not mandatory for workflow
                error_event = Event(
                    author=self.name,
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=f"\n\n⚠️ Criteria checker failed for stage {stage_idx}: {str(e)}\n"
                                "Continuing without criteria update...\n\n"
                            )
                        ],
                    ),
                    turn_complete=False,
                )
                yield error_event

            # === Run Stage Reflector ===
            logger.info("")
            logger.info("")
            logger.info("")
            logger.info(f"[StageOrchestrator] Running stage_reflector after stage {stage_idx}")

            try:
                async for event in self.stage_reflector.run_async(ctx):
                    yield event

                # Reflector may modify state["high_level_stages"] via callback
                stages = state.get("high_level_stages", [])
            except Exception as e:
                logger.error(
                    f"[StageOrchestrator] Stage reflector failed for stage {stage_idx}: {e}",
                    exc_info=True,
                )
                # Log error but continue - reflection is not mandatory for workflow
                error_event = Event(
                    author=self.name,
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=f"\n\n⚠️ Stage reflector failed for stage {stage_idx}: {str(e)}\n"
                                "Continuing without stage modifications...\n\n"
                            )
                        ],
                    ),
                    turn_complete=False,
                )
                yield error_event
                # Refresh stages anyway
                stages = state.get("high_level_stages", [])

            # Mark the stage's cycle as finished so orchestration advances to the next stage.
            # NOTE: "completed" means the stage was attempted and its cycle ran to the end, not
            # that review approved it - see next_stage["approved"] / next_stage["status"].
            next_stage["completed"] = True

            # Update stages in state
            state["high_level_stages"] = stages

            logger.info(f"[StageOrchestrator] Stage {stage_idx} cycle complete. Continuing to next iteration.")

            # Update current_stage_index for tracking (keep 0-indexed for consistency)
            state["current_stage_index"] = stage_idx

        # Safety exit if max iterations reached
        info = self._apply_terminal_status(state)
        logger.error(
            f"[StageOrchestrator] Reached maximum iterations ({max_iterations}). "
            f"Exiting orchestration (status={info['run_status']})."
        )
        status_block = self._format_status_block(info)
        timeout_event = Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text=f"\n\n⚠️ Reached maximum orchestration iterations ({max_iterations}) "
                        f"(status: {info['run_status']}). Proceeding to summary with current progress.\n\n"
                        + (status_block + "\n\n" if status_block else "")
                    )
                ],
            ),
            actions=EventActions(state_delta=self._status_state_delta(state)),
            turn_complete=True,
        )
        yield timeout_event

    async def _run_live_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Live mode not supported for orchestrator."""
        raise NotImplementedError("Live mode is not supported for StageOrchestratorAgent. Use async mode instead.")
