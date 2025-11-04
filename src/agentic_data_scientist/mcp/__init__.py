"""MCP (Model Context Protocol) integration for Agentic Data Scientist."""

from agentic_data_scientist.mcp.config import (
    get_claude_scientific_skills_toolset,
    get_default_mcp_toolsets,
    get_fetch_toolset,
    get_filesystem_toolset,
)
from agentic_data_scientist.mcp.registry import get_mcp_toolsets


__all__ = [
    "get_filesystem_toolset",
    "get_fetch_toolset",
    "get_claude_scientific_skills_toolset",
    "get_default_mcp_toolsets",
    "get_mcp_toolsets",
]
