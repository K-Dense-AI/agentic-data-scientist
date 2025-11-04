"""
MCP tool registry for ADK integration using MCPToolset.

This module provides simplified access to MCP toolsets using ADK's built-in
MCPToolset integration, which handles connection management automatically.
"""

import logging
from typing import Optional

from agentic_data_scientist.mcp.config import get_default_mcp_toolsets


logger = logging.getLogger(__name__)


def get_mcp_toolsets(working_dir: Optional[str] = None) -> list:
    """
    Get configured MCP toolsets for ADK agents.

    This function returns a list of McpToolset instances that ADK agents
    can use directly. ADK's McpToolset handles all connection management,
    tool discovery, and lifecycle automatically.

    Parameters
    ----------
    working_dir : str, optional
        Working directory for filesystem MCP server

    Returns
    -------
    list[McpToolset]
        List of configured MCP toolsets ready to use with ADK agents
    """
    try:
        toolsets = get_default_mcp_toolsets(working_dir)
        logger.info(f"Configured {len(toolsets)} MCP toolsets")
        return toolsets
    except Exception as e:
        logger.error(f"Error configuring MCP toolsets: {e}")
        return []
