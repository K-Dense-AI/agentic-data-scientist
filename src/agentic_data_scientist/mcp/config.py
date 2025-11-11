"""
MCP server configuration and discovery using ADK's MCPToolset.

This module defines the configuration for Model Context Protocol (MCP) servers
that provide tools to the agents using ADK's built-in MCPToolset integration.
"""

import os
from typing import Optional

from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StdioConnectionParams,
    StdioServerParameters,
    StreamableHTTPConnectionParams,
)


MCP_CONNECTION_TIMEOUT = float(os.getenv("MCP_CONNECTION_TIMEOUT", "60.0"))


def get_filesystem_toolset(working_dir: Optional[str] = None) -> McpToolset:
    """
    Get McpToolset for filesystem with read-only access.

    Parameters
    ----------
    working_dir : str, optional
        Working directory root for filesystem access (default: /tmp)

    Returns
    -------
    McpToolset
        Configured filesystem McpToolset with read-only filter
    """
    root_dir = working_dir or os.getenv("MCP_FILESYSTEM_ROOT", "/tmp")

    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", root_dir],
            ),
            timeout=MCP_CONNECTION_TIMEOUT,
        ),
        tool_filter=[
            "read_text_file",
            "read_media_file",
            "read_multiple_files",
            "list_directorylist_directory_with_sizes",
            "search_files",
            "directory_tree",
            "get_file_info",
            "list_allowed_directories",
        ],
    )


def get_fetch_toolset() -> McpToolset:
    """
    Get McpToolset for web content fetching.

    Returns
    -------
    McpToolset
        Configured fetch McpToolset
    """
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="docker",
                args=["run", "-i", "--rm", "mcp/fetch"],
            ),
            timeout=MCP_CONNECTION_TIMEOUT,
        ),
    )


def get_claude_scientific_skills_toolset() -> McpToolset:
    """
    Get McpToolset for Claude Scientific Skills hosted MCP server.

    Returns
    -------
    McpToolset
        Configured Claude Scientific Skills McpToolset using SSE connection
    """
    mcp_url = os.getenv("CLAUDE_SCIENTIFIC_SKILLS_URL", "https://mcp.k-dense.ai/claude-scientific-skills/mcp")

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=mcp_url,
        ),
    )


def get_default_mcp_toolsets(working_dir: Optional[str] = None) -> list[McpToolset]:
    """
    Get default list of MCP toolsets for ADK agents.

    Note: Scientific skills are now provided via Claude native Skills
    loaded from .claude/skills/ rather than MCP.

    Parameters
    ----------
    working_dir : str, optional
        Working directory for filesystem MCP

    Returns
    -------
    list[McpToolset]
        List of configured MCP toolsets
    """
    return [
        get_filesystem_toolset(working_dir),
        get_fetch_toolset(),
    ]
