"""
Templates for Claude Code agent configuration.

This module provides functions to generate instructions and context
for the Claude Code agent.
"""

import logging
from string import Template
from typing import Any, Dict


logger = logging.getLogger(__name__)


def get_claude_instructions(state: Dict[str, Any], working_dir: str) -> str:
    """
    Generate system instructions for Claude Code agent.

    Parameters
    ----------
    state : dict
        The state dictionary containing variables for template substitution.
        Common variables include:
        - implementation_task: The user's request/task to implement
        - implementation_plan: The detailed implementation plan
    working_dir : str
        The working directory path where execution will occur.

    Returns
    -------
    str
        The complete system instructions with substituted variables.
    """
    # Load the coding base prompt
    try:
        from agentic_data_scientist.prompts import load_prompt

        base_content = load_prompt("coding_base")
    except FileNotFoundError:
        # Fallback to a simple default
        base_content = """You are a coding assistant. Implement the given task completely and thoroughly.

Working directory: $working_dir

Task: $implementation_task

Plan: $implementation_plan

Requirements:
1. Complete ALL steps in the plan
2. Save all outputs with descriptive filenames
3. Print progress updates after each step
4. Generate comprehensive documentation
5. Create final execution summary when done"""

    # Create substitutions dictionary
    substitutions = {'working_dir': working_dir}

    # Add all state variables
    for key, value in state.items():
        if value is None:
            value = ""
        elif not isinstance(value, str):
            value = str(value)

        # Truncate very long values
        MAX_CHARS = 40000
        if len(value) > MAX_CHARS:
            substitutions[key] = value[:MAX_CHARS] + "\n\n[... truncated for length ...]"
        else:
            substitutions[key] = value

    # Substitute variables
    template = Template(base_content)
    result = template.safe_substitute(**substitutions)

    return result


def get_claude_context(implementation_plan: str, working_dir: str) -> str:
    """
    Generate the initial user context/prompt for Claude.

    Parameters
    ----------
    implementation_plan : str
        The implementation plan to execute.
    working_dir : str
        The working directory path.

    Returns
    -------
    str
        The initial user message for Claude.
    """
    # Truncate plan if too long
    MAX_PLAN_LENGTH = 100000
    truncated_plan = implementation_plan

    if len(implementation_plan) > MAX_PLAN_LENGTH:
        keep_start = MAX_PLAN_LENGTH * 3 // 4
        keep_end = MAX_PLAN_LENGTH // 4
        truncated_plan = (
            implementation_plan[:keep_start]
            + "\n\n[... middle section truncated to prevent token limit errors ...]\n\n"
            + implementation_plan[-keep_end:]
        )
        logger.warning(
            f"Implementation plan truncated from {len(implementation_plan)} to {len(truncated_plan)} characters"
        )

    context = f"""Execute the following implementation plan COMPLETELY and STRICTLY.

IMPORTANT: You have scientific Skills available in .claude/skills/. 
Start by asking "What Skills are available?" to discover specialized tools for your task.

Parse this plan into discrete steps and execute EVERY step in order. Do not exit until ALL steps are completed.

Working directory: {working_dir}

IMPLEMENTATION PLAN TO EXECUTE:
{truncated_plan}

CRITICAL REQUIREMENTS:
1. Discover and use available Skills for specialized tasks
2. Complete EVERY step in the plan - no partial execution allowed
3. Save all outputs with descriptive filenames using {working_dir}/ prefix
4. Print progress updates after each step
5. Update README.md incrementally - DO NOT create separate summary files
6. Document which Skills were used in README

You MUST implement the entire plan. Parse it, execute it step by step, and verify completion."""

    return context


def get_minimal_pyproject() -> str:
    """
    Get a minimal pyproject.toml content for the session.

    Returns
    -------
    str
        The pyproject.toml content.
    """
    return """[project]
name = "agentic-data-scientist-session"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    # Core scientific computing
    "numpy>=2.0.0",
    "pandas>=2.0.0",
    "matplotlib>=3.8.0",
    "scipy>=1.11.0",
    "seaborn>=0.13.0",
    "scikit-learn>=1.3.0",
    
    # Data formats and utilities
    "pyyaml>=6.0.0",
    "pillow>=10.0.0",
    "requests>=2.31.0",
    
    # Notebooks support
    "jupyter>=1.0.0",
    "ipykernel>=6.25.0",
    
    # Additional utilities
    "tqdm>=4.66.0",
    "plotly>=5.17.0",
    
    # Environment management
    "python-dotenv>=1.0.0",
]
"""
