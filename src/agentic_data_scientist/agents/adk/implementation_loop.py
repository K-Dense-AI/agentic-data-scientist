"""
Implementation loop agents for ADK system.

This module creates the coding and review agents that work together in an
iterative loop to implement and verify solutions.
"""

import logging
import os

from google.adk.planners import BuiltInPlanner
from google.adk.tools.tool_context import CallbackContext
from google.genai import types

from agentic_data_scientist.agents.adk.loop_detection import LoopDetectionAgent
from agentic_data_scientist.agents.adk.utils import REVIEW_MODEL, exit_loop_simple, get_generate_content_config
from agentic_data_scientist.prompts import load_prompt


logger = logging.getLogger(__name__)

# Configuration
TOOL_LOOP_LIMIT = 5
CODING_EVENT_LIMIT = 100
MAX_EVENTS_TO_KEEP = 20


def trim_history_to_recent_events(callback_context: CallbackContext, max_events: int = CODING_EVENT_LIMIT):
    """
    Simple callback to keep only the most recent events in history.

    This prevents token overflow by maintaining a fixed window of context.

    Parameters
    ----------
    callback_context : CallbackContext
        The callback context with session access
    max_events : int, optional
        Maximum number of events to keep (default: CODING_EVENT_LIMIT)
    """
    session = callback_context._invocation_context.session
    events = session.events

    logger.info(f"[DEBUG] trim_history_to_recent_events called: {len(events)} events, max={max_events}")

    if len(events) > max_events:
        # Keep only the most recent events
        events_to_remove = len(events) - max_events
        logger.info(f"[DEBUG] Trimming {events_to_remove} old events, keeping {max_events} most recent")

        # Remove oldest events
        for _ in range(events_to_remove):
            events.pop(0)

        logger.info(f"[DEBUG] After trimming: {len(events)} events remain")


def make_implementation_agents(working_dir: str, mcp_toolsets: list):
    """
    Create the implementation agents (coding + review).

    Parameters
    ----------
    working_dir : str
        Working directory for the session
    mcp_toolsets : list
        List of MCPToolset instances available to agents

    Returns
    -------
    tuple
        (coding_agent, review_agent)
    """
    logger.info(f"[AgenticDS] Initializing implementation agents with {len(mcp_toolsets)} MCP toolsets")

    # Always use ClaudeCodeAgent for coding
    from agentic_data_scientist.agents.claude_code import ClaudeCodeAgent

    model = os.getenv("CODING_MODEL", "claude-sonnet-4-5-latest")
    logger.info(f"[AgenticDS] Using ClaudeCodeAgent with model={model}")

    coding_agent = ClaudeCodeAgent(
        name="coding_agent",
        description="A coding agent that uses Claude Code SDK to implement plans.",
        working_dir=working_dir,
        model=model,
        output_key="implementation_summary",
    )

    # Review Agent - Uses ADK with loop detection
    logger.info("[AgenticDS] Creating review agent")

    # Load review prompt
    review_prompt = load_prompt("coding_review")

    review_agent = LoopDetectionAgent(
        name="review_agent",
        description="Reviews implementation and provides feedback or approval.",
        instruction=review_prompt,
        model=REVIEW_MODEL,
        tools=[exit_loop_simple],
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.0),
        output_key="review_feedback",
        # Loop detection settings
        min_pattern_length=200,
        max_pattern_length=1000,
        repetition_threshold=5,
        window_size=5000,
    )

    logger.info("[AgenticDS] Implementation agents created successfully")

    return coding_agent, review_agent
