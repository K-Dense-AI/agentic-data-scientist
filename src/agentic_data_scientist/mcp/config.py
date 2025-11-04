"""
MCP server configuration and discovery using ADK's MCPToolset.

This module defines the configuration for Model Context Protocol (MCP) servers
that provide tools to the agents using ADK's built-in MCPToolset integration.
"""

import os
from typing import Any, Optional

from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    SseConnectionParams,
    StdioConnectionParams,
    StdioServerParameters,
)


def filesystem_tool_filter(tool: Any) -> bool:
    """
    Filter function for filesystem MCP tools to allow only read-only operations.

    Parameters
    ----------
    tool : Any
        The tool to filter

    Returns
    -------
    bool
        True if the tool is allowed (read-only), False otherwise
    """
    # Allow only read-only operations
    allowed_operations = [
        "read_file",
        "read_multiple_files",
        "list_directory",
        "search_files",
        "get_file_info",
        "list_allowed_directories",
    ]
    # Tool might be an object with a name attribute or a dict
    tool_name = getattr(tool, 'name', tool.get('name') if isinstance(tool, dict) else None)
    return tool_name in allowed_operations


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
        ),
        tool_filter=filesystem_tool_filter,
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
                command="npx",
                args=["-y", "@modelcontextprotocol/server-fetch"],
            ),
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
        connection_params=SseConnectionParams(
            url=mcp_url,
        ),
    )


def get_default_mcp_toolsets(working_dir: Optional[str] = None) -> list[McpToolset]:
    """
    Get default list of MCP toolsets for ADK agents.

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
        get_claude_scientific_skills_toolset(),
    ]
