"""
Main ADK agent factory for Agentic Data Scientist.

This module creates the multi-agent system with planning, orchestration,
implementation, and verification agents.
"""

import logging
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from dotenv import load_dotenv
from google.adk.agents import InvocationContext, LoopAgent, SequentialAgent
from google.adk.events import Event
from google.adk.planners import BuiltInPlanner
from google.adk.utils.context_utils import Aclosing
from google.genai import types
from typing_extensions import override

from agentic_data_scientist.agents.adk.implementation_loop import make_implementation_agents
from agentic_data_scientist.agents.adk.loop_detection import LoopDetectionAgent
from agentic_data_scientist.agents.adk.utils import (
    DEFAULT_MODEL,
    REVIEW_MODEL,
    exit_loop_simple,
    get_generate_content_config,
)
from agentic_data_scientist.prompts import load_prompt


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


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
    model: Optional[str] = None,
    mcp_servers: Optional[List[str]] = None,
) -> LoopDetectionAgent:
    """
    Factory function to create an Agentic Data Scientist ADK agent.

    Parameters
    ----------
    working_dir : str, optional
        Working directory for the session
    model : str, optional
        Model to use for the agents
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

    # Get MCP toolsets using ADK's MCPToolset
    from agentic_data_scientist.mcp import get_mcp_toolsets

    # Get toolsets (MCPToolset handles connection management automatically)
    mcp_toolsets = []
    try:
        mcp_toolsets = get_mcp_toolsets(working_dir=str(working_dir))
        logger.info(f"[AgenticDS] Configured {len(mcp_toolsets)} MCP toolsets")
    except Exception as e:
        logger.warning(f"[AgenticDS] Failed to configure MCP toolsets: {e}")

    # ------------------------- Implementation Loop -------------------------

    coding_agent, review_agent = make_implementation_agents(str(working_dir), mcp_toolsets)

    # LoopAgent wrapper for implementation
    implementation_loop = NonEscalatingLoopAgent(
        name="implementation_loop",
        description="Implements tasks through iterative coding and review cycles.",
        sub_agents=[coding_agent, review_agent],
        max_iterations=10,
    )

    # ------------------------- Plan Orchestrator -------------------------

    logger.info("[AgenticDS] Loading plan_orchestrator prompt")
    plan_orchestrator_instructions = load_prompt("plan_orchestrator")

    logger.info(f"[AgenticDS] Creating plan_orchestrator with model={model or DEFAULT_MODEL}")

    plan_orchestrator = LoopDetectionAgent(
        name="plan_orchestrator",
        model=model or DEFAULT_MODEL,
        description="Orchestrates the implementation of multi-step plans.",
        instruction=plan_orchestrator_instructions,
        tools=mcp_toolsets + [exit_loop_simple],
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.5),
        output_key="implementation_task",
    )

    plan_orchestrator_loop = NonEscalatingLoopAgent(
        name="plan_orchestrator_loop",
        description="Orchestrates implementation through multiple iterations.",
        sub_agents=[plan_orchestrator, implementation_loop],
        max_iterations=10,
    )

    # ------------------------- Plan Verifier -------------------------

    logger.info("[AgenticDS] Loading plan_verifier prompt")
    plan_verifier_instructions = load_prompt("plan_verifier")

    logger.info(f"[AgenticDS] Creating plan_verifier with model={REVIEW_MODEL}")

    plan_verifier = LoopDetectionAgent(
        name="plan_verifier",
        model=REVIEW_MODEL,
        description="Verifies that implementation meets success criteria.",
        instruction=plan_verifier_instructions,
        tools=mcp_toolsets + [exit_loop_simple],
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        output_key="plan_verdict",
        include_contents='none',
    )

    # LoopAgent wrapper for planning
    planning_loop = LoopAgent(
        name="planning_loop",
        description="Carries out plans until verification succeeds.",
        sub_agents=[plan_orchestrator_loop, plan_verifier],
        max_iterations=10,
    )

    # ------------------------- Summary Agent -------------------------

    logger.info("[AgenticDS] Loading summary_agent prompt")
    summary_agent_instructions = load_prompt("summary")

    logger.info(f"[AgenticDS] Creating summary_agent with model={model or DEFAULT_MODEL}")

    summary_agent = LoopDetectionAgent(
        name="summary_agent",
        model=model or DEFAULT_MODEL,
        description="Summarizes results into a comprehensive report.",
        instruction=summary_agent_instructions,
        tools=mcp_toolsets,
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.3),
    )

    # ------------------------- Plan Generator -------------------------

    logger.info("[AgenticDS] Loading plan_generator prompt")
    plan_generator_instructions = load_prompt("plan_generator")

    logger.info(f"[AgenticDS] Creating plan_generator with model={model or DEFAULT_MODEL}")

    plan_generator = LoopDetectionAgent(
        name="plan_generator",
        model=model or DEFAULT_MODEL,
        description="Generates high-level plans for complex tasks.",
        instruction=plan_generator_instructions,
        tools=mcp_toolsets,
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.7),
        output_key="plan",
    )

    # ------------------------- Root Agent -------------------------

    logger.info("[AgenticDS] Loading root agent prompt")
    root_instructions = load_prompt("agent_base")

    logger.info(f"[AgenticDS] Creating root agent with model={model or DEFAULT_MODEL}")

    root_agent = LoopDetectionAgent(
        name="agentic_data_scientist_agent",
        model=model or DEFAULT_MODEL,
        description="Agentic Data Scientist root agent - orchestrates the entire workflow.",
        instruction=root_instructions,
        tools=mcp_toolsets,
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=-1,
            ),
        ),
        generate_content_config=get_generate_content_config(temperature=0.3),
    )

    # Create sequential workflow
    workflow = SequentialAgent(
        name="agentic_data_scientist_workflow",
        description="Complete Agentic Data Scientist workflow from planning to summary.",
        sub_agents=[
            root_agent,
            plan_generator,
            planning_loop,
            summary_agent,
        ],
    )

    logger.info("[AgenticDS] Agent creation complete")

    return workflow
