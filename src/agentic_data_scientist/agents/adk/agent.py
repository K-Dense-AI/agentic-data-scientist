"""
Main ADK agent factory for Agentic Data Scientist.

This module creates the multi-agent system with planning, orchestration,
implementation, and verification agents.
"""

import logging
import warnings
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from dotenv import load_dotenv
from google.adk.agents import InvocationContext, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App
from google.adk.events import Event
from google.adk.planners import BuiltInPlanner
from google.adk.utils.context_utils import Aclosing
from google.genai import types
from pydantic import BaseModel, Field
from typing_extensions import override

from agentic_data_scientist.agents.adk.event_compression import create_compression_callback
from agentic_data_scientist.agents.adk.implementation_loop import make_implementation_agents
from agentic_data_scientist.agents.adk.loop_detection import LoopDetectionAgent
from agentic_data_scientist.agents.adk.review_confirmation import create_review_confirmation_agent
from agentic_data_scientist.agents.adk.utils import (
    DEFAULT_MODEL,
    REVIEW_MODEL,
    get_generate_content_config,
    is_network_disabled,
)
from agentic_data_scientist.prompts import load_prompt


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Suppress experimental feature warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.adk.tools.mcp_tool")

# Suppress verbose JSON Schema conversion logs
logging.getLogger("google_genai.types").setLevel(logging.WARNING)


# ========================= Output Schemas (Pydantic BaseModel) =========================


class Stage(BaseModel):
    """A high-level implementation stage."""

    title: str = Field(description="Stage title")
    description: str = Field(description="Detailed stage description")


class SuccessCriterion(BaseModel):
    """A success criterion for completion."""

    criteria: str = Field(description="Success criterion description")


class PlanParserOutput(BaseModel):
    """Parsed high-level plan into stages and success criteria."""

    stages: List[Stage] = Field(description="List of high-level stages to implement progressively")
    success_criteria: List[SuccessCriterion] = Field(description="Definitive checklist for overall analysis completion")


class CriteriaUpdate(BaseModel):
    """Update for a specific success criterion."""

    index: int = Field(description="Criterion index")
    met: bool = Field(description="Whether criterion is met")
    evidence: str = Field(description="Evidence or reason for the status (file paths, metrics, etc.)")


class CriteriaCheckerOutput(BaseModel):
    """Updated success criteria status."""

    criteria_updates: List[CriteriaUpdate] = Field(description="List of criteria with updated met status and evidence")


class StageModification(BaseModel):
    """Modification to an existing stage."""

    index: int = Field(description="Stage index to modify")
    new_description: str = Field(description="Updated stage description (or empty if no change)")


class NewStage(BaseModel):
    """A new stage to add."""

    title: str = Field(description="New stage title")
    description: str = Field(description="New stage description")


class StageReflectorOutput(BaseModel):
    """Reflection on remaining stages with optional modifications."""

    stage_modifications: List[StageModification] = Field(description="Modifications to existing uncompleted stages")
    new_stages: List[NewStage] = Field(description="New stages to add to the end of the stage list")


# Keep for backwards compatibility
PLAN_PARSER_OUTPUT_SCHEMA = PlanParserOutput
CRITERIA_CHECKER_OUTPUT_SCHEMA = CriteriaCheckerOutput
STAGE_REFLECTOR_OUTPUT_SCHEMA = StageReflectorOutput


# ========================= Callbacks =========================


def plan_parser_callback(callback_context: CallbackContext):
    """
    Transform parsed output into structured stage/criteria lists.

    This callback processes the plan parser output and initializes
    high_level_stages and high_level_success_criteria with proper tracking fields.

    Parameters
    ----------
    callback_context : CallbackContext
        The callback context with invocation context access
    """

    ctx = callback_context._invocation_context
    state = ctx.session.state

    # Get the output from the agent
    parsed_output = state.get("parsed_plan_output")

    if not parsed_output:
        logger.error("[PlanParser] No parsed output found in state")
        return

    # Validate structure
    if not isinstance(parsed_output, dict):
        logger.error(f"[PlanParser] Invalid parsed output type: {type(parsed_output)}")
        return

    stages_data = parsed_output.get("stages", [])
    criteria_data = parsed_output.get("success_criteria", [])

    if not isinstance(stages_data, list):
        logger.error(f"[PlanParser] stages is not a list: {type(stages_data)}")
        return

    if not isinstance(criteria_data, list):
        logger.error(f"[PlanParser] success_criteria is not a list: {type(criteria_data)}")
        return

    logger.info("[PlanParser] Processing parsed plan output")

    # Initialize stages with tracking fields
    stages = []
    for idx, stage in enumerate(stages_data):
        # Validate stage structure
        if not isinstance(stage, dict) or "title" not in stage or "description" not in stage:
            logger.error(f"[PlanParser] Invalid stage structure at index {idx}: {stage}")
            continue

        stages.append(
            {
                "index": idx,
                "title": stage["title"],
                "description": stage["description"],
                "completed": False,
                "implementation_result": None,
            }
        )

    # Initialize criteria with tracking fields
    criteria = []
    for idx, crit in enumerate(criteria_data):
        # Validate criterion structure
        if not isinstance(crit, dict) or "criteria" not in crit:
            logger.error(f"[PlanParser] Invalid criterion structure at index {idx}: {crit}")
            continue

        criteria.append(
            {
                "index": idx,
                "criteria": crit["criteria"],
                "met": False,
                "evidence": None,
            }
        )

    # Only update state if we have valid stages and criteria
    if not stages:
        logger.error("[PlanParser] No valid stages after parsing - not updating state")
        return

    if not criteria:
        logger.error("[PlanParser] No valid criteria after parsing - not updating state")
        return

    state["high_level_stages"] = stages
    state["high_level_success_criteria"] = criteria
    state["current_stage_index"] = 0

    logger.info(f"[PlanParser] Initialized {len(stages)} stages and {len(criteria)} criteria")


def criteria_checker_callback(callback_context: CallbackContext):
    """
    Update criteria met status based on checker output.

    This callback updates the high_level_success_criteria in state based on
    the criteria checker's assessment.

    Parameters
    ----------
    callback_context : CallbackContext
        The callback context with invocation context access
    """

    ctx = callback_context._invocation_context
    state = ctx.session.state

    criteria_output = state.get("criteria_checker_output")
    criteria = state.get("high_level_success_criteria", [])

    if not criteria_output:
        logger.error("[CriteriaChecker] No output found in state")
        return

    if not isinstance(criteria_output, dict) or "criteria_updates" not in criteria_output:
        logger.error("[CriteriaChecker] Invalid output structure")
        return

    updates = criteria_output["criteria_updates"]
    if not isinstance(updates, list):
        logger.error(f"[CriteriaChecker] criteria_updates is not a list: {type(updates)}")
        return

    logger.info("[CriteriaChecker] Updating criteria status")

    valid_updates = 0
    invalid_updates = 0

    for update in updates:
        # Validate update structure
        if not isinstance(update, dict):
            logger.warning(f"[CriteriaChecker] Invalid update structure (not dict): {update}")
            invalid_updates += 1
            continue

        if "index" not in update or "met" not in update or "evidence" not in update:
            logger.warning(f"[CriteriaChecker] Invalid update structure (missing fields): {update}")
            invalid_updates += 1
            continue

        idx = update["index"]
        if 0 <= idx < len(criteria):
            criteria[idx]["met"] = update["met"]
            criteria[idx]["evidence"] = update["evidence"]
            valid_updates += 1

            status = "✅ MET" if update["met"] else "❌ NOT MET"
            criteria_text = criteria[idx].get("criteria", "Unknown")
            evidence_text = update["evidence"]

            logger.info(f"[CriteriaChecker] Criterion {idx}: {status}")
            logger.info(f"[CriteriaChecker]   └─ Criteria: {criteria_text}")
            logger.info(f"[CriteriaChecker]   └─ Evidence: {evidence_text}")
        else:
            logger.warning(f"[CriteriaChecker] Invalid criterion index: {idx}")
            invalid_updates += 1

    if valid_updates == 0:
        logger.error("[CriteriaChecker] No valid updates processed")
    elif invalid_updates > len(criteria) // 2:
        # More than half of updates are invalid
        logger.error(
            f"[CriteriaChecker] Too many invalid updates ({invalid_updates}/{len(updates)}) - "
            "criteria check may be unreliable"
        )

    # Log summary of all criteria statuses
    met_count = sum(1 for c in criteria if c.get("met", False))
    logger.info(f"[CriteriaChecker] Summary: {met_count}/{len(criteria)} criteria met")

    state["high_level_success_criteria"] = criteria


def stage_reflector_callback(callback_context: CallbackContext):
    """
    Apply stage modifications and add new stages.

    This callback updates the high_level_stages in state based on the
    stage reflector's recommendations.

    Parameters
    ----------
    callback_context : CallbackContext
        The callback context with invocation context access
    """

    ctx = callback_context._invocation_context
    state = ctx.session.state

    reflector_output = state.get("stage_reflector_output")
    stages = state.get("high_level_stages", [])

    if not reflector_output:
        logger.error("[StageReflector] No output found in state")
        return

    if not isinstance(reflector_output, dict):
        logger.error(f"[StageReflector] Invalid output type: {type(reflector_output)}")
        return

    logger.info("[StageReflector] Processing stage reflections")

    # Apply modifications to existing stages
    modifications = reflector_output.get("stage_modifications", [])
    if not isinstance(modifications, list):
        logger.error(f"[StageReflector] stage_modifications is not a list: {type(modifications)}")
        modifications = []

    for mod in modifications:
        if not isinstance(mod, dict):
            logger.warning(f"[StageReflector] Invalid modification structure: {mod}")
            continue

        if "index" not in mod or "new_description" not in mod:
            logger.warning(f"[StageReflector] Missing fields in modification: {mod}")
            continue

        idx = mod["index"]
        new_desc = mod.get("new_description", "")

        if 0 <= idx < len(stages) and new_desc:
            # Check if stage is completed - don't modify completed stages
            if stages[idx].get("completed", False):
                logger.warning(f"[StageReflector] Cannot modify completed stage {idx} - ignoring")
                continue

            stages[idx]["description"] = new_desc
            logger.info(f"[StageReflector] Modified stage {idx} description")
        elif new_desc:
            logger.warning(f"[StageReflector] Invalid stage index for modification: {idx}")

    # Add new stages
    new_stages = reflector_output.get("new_stages", [])
    if not isinstance(new_stages, list):
        logger.error(f"[StageReflector] new_stages is not a list: {type(new_stages)}")
        new_stages = []

    for new_stage in new_stages:
        if not isinstance(new_stage, dict):
            logger.warning(f"[StageReflector] Invalid new stage structure: {new_stage}")
            continue

        if "title" not in new_stage or "description" not in new_stage:
            logger.warning(f"[StageReflector] Missing fields in new stage: {new_stage}")
            continue

        new_idx = len(stages)
        stages.append(
            {
                "index": new_idx,
                "title": new_stage["title"],
                "description": new_stage["description"],
                "completed": False,
                "implementation_result": None,
            }
        )
        logger.info(f"[StageReflector] Added new stage {new_idx}: {new_stage['title']}")

    state["high_level_stages"] = stages


class NonEscalatingLoopAgent(LoopAgent):
    """A loop agent that does not propagate escalate flags upward."""

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        times_looped = 0
        while not self.max_iterations or times_looped < self.max_iterations:
            for sub_agent in self.sub_agents:
                should_exit = False
                async with Aclosing(sub_agent.run_async(ctx)) as agen:
                    async for event in agen:
                        if event.actions.escalate:
                            event.actions.escalate = False
                            should_exit = True
                        yield event
                        if should_exit:
                            break

                if should_exit:
                    return
            times_looped += 1
        return


def create_agent(
    working_dir: Optional[str] = None,
    mcp_servers: Optional[List[str]] = None,
) -> LoopDetectionAgent:
    """
    Factory function to create an Agentic Data Scientist ADK agent.

    Parameters
    ----------
    working_dir : str, optional
        Working directory for the session
    mcp_servers : List[str], optional
        List of MCP servers to enable for tools

    Returns
    -------
    LoopDetectionAgent
        The configured root agent
    """
    # Create working directory if not provided
    if working_dir is None:
        import tempfile

        working_dir = tempfile.mkdtemp(prefix="agentic_ds_")

    working_dir = Path(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"[AgenticDS] Creating ADK agent with working_dir={working_dir}")

    # Create local tools with working_dir bound via wrapper functions
    from agentic_data_scientist.tools import (
        directory_tree,
        fetch_url,
        get_file_info,
        list_directory,
        read_file,
        read_media_file,
        search_files,
    )

    # Bind working_dir using wrapper functions that completely hide the parameter
    # This ensures ADK sees the correct signature without working_dir
    working_dir_str = str(working_dir)

    def read_file_bound(path: str, head: Optional[int] = None, tail: Optional[int] = None) -> str:
        """Read file contents with optional head/tail line limits."""
        return read_file(path, working_dir_str, head, tail)

    def read_media_file_bound(path: str) -> str:
        """Read binary/media files and return base64 encoded data."""
        return read_media_file(path, working_dir_str)

    def list_directory_bound(path: str = ".", show_sizes: bool = False, sort_by: str = "name") -> str:
        """List directory contents with optional size display and sorting."""
        return list_directory(path, working_dir_str, show_sizes, sort_by)

    def directory_tree_bound(path: str = ".", exclude_patterns: Optional[list[str]] = None) -> str:
        """Generate a recursive directory tree view."""
        return directory_tree(path, working_dir_str, exclude_patterns)

    def search_files_bound(pattern: str, path: str = ".", exclude_patterns: Optional[list[str]] = None) -> str:
        """Search for files matching a pattern."""
        return search_files(pattern, working_dir_str, path, exclude_patterns)

    def get_file_info_bound(path: str) -> str:
        """Get detailed metadata about a file."""
        return get_file_info(path, working_dir_str)

    tools = [
        read_file_bound,
        read_media_file_bound,
        list_directory_bound,
        directory_tree_bound,
        search_files_bound,
        get_file_info_bound,
    ]

    # Only add fetch_url if network access is not disabled
    if not is_network_disabled():
        tools.append(fetch_url)

    logger.info(f"[AgenticDS] Configured {len(tools)} local tools")

    # ------------------------- Implementation Loop -------------------------

    coding_agent, review_agent, review_confirmation = make_implementation_agents(str(working_dir), tools)

    # LoopAgent wrapper for implementation
    implementation_loop = NonEscalatingLoopAgent(
        name="implementation_loop",
        description="Iterative implementation-review-confirmation loop for each stage.",
        sub_agents=[coding_agent, review_agent, review_confirmation],
        max_iterations=5,
    )

    # ------------------------- Summary Agent -------------------------

    logger.info("[AgenticDS] Loading summary_agent prompt")
    summary_agent_instructions = load_prompt("summary")

    logger.info(f"[AgenticDS] Creating summary_agent with model={DEFAULT_MODEL}")

    summary_agent = LoopDetectionAgent(
        name="summary_agent",
        model=DEFAULT_MODEL,
        description="Summarizes results into a comprehensive pure text report.",
        instruction=summary_agent_instructions,
        tools=tools,  # Needs tools to read files
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.3),
    )

    # ------------------------- High Level Planning Agents -------------------------

    logger.info("[AgenticDS] Loading plan maker agent prompt")
    plan_maker_instructions = load_prompt("plan_maker")

    logger.info(f"[AgenticDS] Creating plan maker agent with model={DEFAULT_MODEL}")

    plan_maker_compression = create_compression_callback(event_threshold=40, overlap_size=20)

    plan_maker_agent = LoopDetectionAgent(
        name="plan_maker_agent",
        model=DEFAULT_MODEL,
        description="Plan maker agent - creates high-level plans for complex tasks.",
        instruction=plan_maker_instructions,
        tools=tools,
        output_key="high_level_plan",
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.6),
        after_agent_callback=plan_maker_compression,
    )

    logger.info("[AgenticDS] Loading plan reviewer agent prompt")
    plan_reviewer_instructions = load_prompt("plan_reviewer")

    logger.info(f"[AgenticDS] Creating plan reviewer agent with model={REVIEW_MODEL}")

    plan_reviewer_compression = create_compression_callback(event_threshold=40, overlap_size=20)

    plan_reviewer_agent = LoopDetectionAgent(
        name="plan_reviewer_agent",
        model=REVIEW_MODEL,
        description="Plan reviewer agent - reviews high-level plans for completeness and correctness.",
        instruction=plan_reviewer_instructions,
        tools=tools,
        output_key="plan_review_feedback",
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.3),
        after_agent_callback=plan_reviewer_compression,
    )

    high_level_planning_loop = NonEscalatingLoopAgent(
        name="high_level_planning_loop",
        description="Carries out high-level planning through multiple iterations.",
        sub_agents=[
            plan_maker_agent,
            plan_reviewer_agent,
            create_review_confirmation_agent(auto_exit_on_completion=True, prompt_name="plan_review_confirmation"),
        ],
        max_iterations=10,
    )

    # ------------------------- High Level Plan Parser -------------------------

    logger.info("[AgenticDS] Loading plan parser prompt")
    plan_parser_instructions = load_prompt("plan_parser")

    logger.info(f"[AgenticDS] Creating plan parser agent with model={DEFAULT_MODEL}")

    high_level_plan_parser = LoopDetectionAgent(
        name="high_level_plan_parser",
        model=DEFAULT_MODEL,
        description="Parses high-level plan into stages and success criteria.",
        instruction=plan_parser_instructions,
        tools=[],  # NO TOOLS - pure JSON parsing
        output_schema=PLAN_PARSER_OUTPUT_SCHEMA,
        output_key="parsed_plan_output",
        after_agent_callback=plan_parser_callback,
        generate_content_config=get_generate_content_config(temperature=0.0),
    )

    # ------------------------- Success Criteria Checker -------------------------

    logger.info("[AgenticDS] Loading criteria checker prompt")
    criteria_checker_instructions = load_prompt("criteria_checker")

    logger.info(f"[AgenticDS] Creating criteria checker agent with model={REVIEW_MODEL}")

    criteria_checker_compression = create_compression_callback(event_threshold=40, overlap_size=20)

    # Combine compression callback with criteria checker callback
    async def combined_criteria_callback(callback_context):
        # Run criteria checker callback first
        criteria_checker_callback(callback_context)
        # Then run compression callback (async)
        await criteria_checker_compression(callback_context)

    success_criteria_checker = LoopDetectionAgent(
        name="success_criteria_checker",
        model=REVIEW_MODEL,
        description="Checks which high-level success criteria have been met.",
        instruction=criteria_checker_instructions,
        tools=tools,  # NEEDS TOOLS to inspect files
        output_schema=CRITERIA_CHECKER_OUTPUT_SCHEMA,
        output_key="criteria_checker_output",
        after_agent_callback=combined_criteria_callback,
        generate_content_config=get_generate_content_config(temperature=0.0),
    )

    # ------------------------- Stage Reflector -------------------------

    logger.info("[AgenticDS] Loading stage reflector prompt")
    stage_reflector_instructions = load_prompt("stage_reflector")

    logger.info(f"[AgenticDS] Creating stage reflector agent with model={DEFAULT_MODEL}")

    stage_reflector_compression = create_compression_callback(event_threshold=40, overlap_size=20)

    # Combine compression callback with stage reflector callback
    async def combined_reflector_callback(callback_context):
        # Run stage reflector callback first
        stage_reflector_callback(callback_context)
        # Then run compression callback (async)
        await stage_reflector_compression(callback_context)

    stage_reflector = LoopDetectionAgent(
        name="stage_reflector",
        model=DEFAULT_MODEL,
        description="Reflects on and adapts remaining implementation stages.",
        instruction=stage_reflector_instructions,
        tools=tools,  # NEEDS TOOLS for context
        output_schema=STAGE_REFLECTOR_OUTPUT_SCHEMA,
        output_key="stage_reflector_output",
        after_agent_callback=combined_reflector_callback,
        generate_content_config=get_generate_content_config(temperature=0.4),
    )

    # ------------------------- Stage Orchestrator -------------------------

    logger.info("[AgenticDS] Creating stage orchestrator")

    from agentic_data_scientist.agents.adk.stage_orchestrator import StageOrchestratorAgent

    stage_orchestrator = StageOrchestratorAgent(
        implementation_loop=implementation_loop,
        criteria_checker=success_criteria_checker,
        stage_reflector=stage_reflector,
        name="stage_orchestrator",
        description="Orchestrates stage-by-stage implementation with adaptive planning.",
    )

    # ------------------------- Root Workflow -------------------------

    logger.info("[AgenticDS] Creating root workflow")

    workflow = SequentialAgent(
        name="agentic_data_scientist_workflow",
        description="Complete Agentic Data Scientist workflow with adaptive stage-wise implementation.",
        sub_agents=[
            high_level_planning_loop,
            high_level_plan_parser,
            stage_orchestrator,
            summary_agent,
        ],
    )

    logger.info("[AgenticDS] Agent creation complete")

    return workflow


def create_app(
    working_dir: Optional[str] = None,
    mcp_servers: Optional[List[str]] = None,
) -> App:
    """
    Create an App instance with context management for the ADK agent.

    Parameters
    ----------
    working_dir : str, optional
        Working directory for the session
    mcp_servers : List[str], optional
        List of MCP servers to enable for tools

    Returns
    -------
    App
        The configured App with context caching and compression
    """
    # Create the root agent
    root_agent = create_agent(working_dir=working_dir, mcp_servers=mcp_servers)

    # Configure context caching (just creating the config enables caching)
    cache_config = ContextCacheConfig()

    # Create App with context caching
    # Note: Event compression is now handled via custom callbacks
    app = App(
        name="agentic-data-scientist",
        root_agent=root_agent,
        context_cache_config=cache_config,
    )

    logger.info("[AgenticDS] Created App with context caching enabled")
    logger.info("[AgenticDS] Event compression will be handled via custom callbacks")

    return app
