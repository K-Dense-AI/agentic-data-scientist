"""Claude Code CLI agent."""

from agentic_data_scientist.agents.claude_code.agent import ClaudeCodeAgent, setup_working_directory
from agentic_data_scientist.agents.claude_code.templates import (
    get_claude_context,
    get_claude_instructions,
    get_minimal_pyproject,
)


__all__ = [
    "ClaudeCodeAgent",
    "setup_working_directory",
    "get_claude_context",
    "get_claude_instructions",
    "get_minimal_pyproject",
]
