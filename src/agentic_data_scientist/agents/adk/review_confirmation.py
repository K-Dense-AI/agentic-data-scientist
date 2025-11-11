"""
Review Confirmation Agent with structured output.

This module provides a specialized agent that determines whether to exit a review
loop based on the review feedback. It uses structured output (output_schema) instead
of normal text output and does not have access to any tools.
"""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.planners import BuiltInPlanner
from google.genai import types
from pydantic import BaseModel, Field

from agentic_data_scientist.agents.adk.loop_detection import LoopDetectionAgent
from agentic_data_scientist.agents.adk.utils import REVIEW_MODEL, get_generate_content_config
from agentic_data_scientist.prompts import load_prompt


logger = logging.getLogger(__name__)


def exit_loop_callback(callback_context: CallbackContext):
    """
    After-agent callback that conditionally exits the loop by escalating.

    This callback is invoked after the agent completes. It reads the agent's
    structured output and only sets the escalate flag if the agent decided to exit.

    To ensure the escalate flag is properly propagated, this callback returns
    an empty Content object, which triggers event creation in ADK's
    _handle_after_agent_callback method.

    Parameters
    ----------
    callback_context : CallbackContext
        The callback context with invocation context access

    Returns
    -------
    Optional[types.Content]
        Empty content to trigger event creation when exiting the loop
    """
    ctx = callback_context._invocation_context
    state = ctx.session.state

    # Get the review confirmation decision from state
    decision = state.get("review_confirmation_decision")

    if not decision:
        logger.warning("[ReviewConfirmation] No decision found in state - not exiting loop")
        return None

    # Validate that decision is a dictionary before calling .get()
    if not isinstance(decision, dict):
        logger.error(f"[ReviewConfirmation] Invalid decision type: {type(decision)} - not exiting loop")
        return None

    # Check if the agent decided to exit
    should_exit = decision.get("exit", False)
    reason = decision.get("reason", "No reason provided")

    if should_exit:
        logger.info(f"[ReviewConfirmation] Exiting loop - Reason: {reason}")
        # Set escalate flag on the event_actions
        if hasattr(callback_context, '_event_actions') and callback_context._event_actions:
            callback_context._event_actions.escalate = True
        else:
            logger.warning("[ReviewConfirmation] No event_actions available - cannot escalate")
            return None
        
        # Return empty content to trigger event creation with the escalate flag
        # This ensures NonEscalatingLoopAgent receives the escalate signal
        return types.Content(role="model", parts=[])
    else:
        logger.info(f"[ReviewConfirmation] Continuing loop - Reason: {reason}")
        return None


# Output schema for review confirmation (Pydantic BaseModel)
class ReviewConfirmationOutput(BaseModel):
    """Schema for review confirmation decision."""

    exit: bool = Field(
        description="Whether to exit the review loop. True if implementation is approved, False if more work is needed."
    )
    reason: str = Field(description="Brief explanation of the decision to exit or continue.")


# Keep for backwards compatibility
REVIEW_CONFIRMATION_OUTPUT_SCHEMA = ReviewConfirmationOutput


def create_review_confirmation_agent(
    auto_exit_on_completion: bool = False,
    prompt_name: str = "plan_review_confirmation",
) -> LoopDetectionAgent:
    """
    Create a review confirmation agent with structured output.

    This agent analyzes review feedback and determines whether the review loop
    should exit. It uses structured output (output_schema) to ensure consistent
    JSON responses and does not have access to any tools.

    Parameters
    ----------
    auto_exit_on_completion : bool, optional
        If True, automatically exit the loop after agent completion by escalating.
        This uses an after_agent_callback to set escalate=True. Defaults to False.
    prompt_name : str, optional
        Name of the prompt file to load (default: "plan_review_confirmation")

    Returns
    -------
    LoopDetectionAgent
        The configured review confirmation agent

    Examples
    --------
    >>> agent = create_review_confirmation_agent()
    >>> # Agent will output structured JSON like:
    >>> # {"exit": true, "reason": "All issues resolved"}
    >>> # or
    >>> # {"exit": false, "reason": "Critical bugs remain"}
    >>>
    >>> # With auto-exit enabled:
    >>> agent = create_review_confirmation_agent(auto_exit_on_completion=True)
    >>> # Agent will automatically exit the loop after completion
    """
    logger.info(f"[AgenticDS] Creating review confirmation agent (prompt={prompt_name})")

    instruction = load_prompt(prompt_name)

    agent = LoopDetectionAgent(
        name=f"{prompt_name}_agent",
        model=REVIEW_MODEL,
        description="Determines whether to exit the review loop based on implementation status.",
        instruction=instruction,
        tools=[],  # No tools - structured output only
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.0),
        output_schema=REVIEW_CONFIRMATION_OUTPUT_SCHEMA,  # Use output_schema for structured JSON
        output_key="review_confirmation_decision",  # Save decision to state
        after_agent_callback=exit_loop_callback if auto_exit_on_completion else None,
    )

    logger.info(
        f"[AgenticDS] Review confirmation agent created successfully "
        f"(prompt={prompt_name}, auto_exit_on_completion={auto_exit_on_completion})"
    )

    return agent
