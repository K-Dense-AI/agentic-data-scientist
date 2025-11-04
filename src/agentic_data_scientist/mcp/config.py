"""
MCP server configuration and discovery.

This module defines the configuration for Model Context Protocol (MCP) servers
that provide tools to the agents.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class MCPServerConfig:
    """
    Configuration for an MCP server.

    Parameters
    ----------
    name : str
        Server name/identifier
    command : str
        Command to run the server
    args : List[str]
        Command-line arguments
    env : Dict[str, str], optional
        Environment variables for the server
    """

    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


# Default MCP server configurations
DEFAULT_MCP_SERVERS = {
    "filesystem": MCPServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", os.getenv("MCP_FILESYSTEM_ROOT", "/tmp")],
        env=None,
    ),
    "git": MCPServerConfig(
        name="git",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-git"],
        env=None,
    ),
    "fetch": MCPServerConfig(
        name="fetch",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"],
        env=None,
    ),
    "markitdown": MCPServerConfig(
        name="markitdown",
        command="uvx",
        args=["markitdown-mcp"],
        env=None,
    ),
    "claude_scientific_skills": MCPServerConfig(
        name="claude_scientific_skills",
        command="npx",
        args=["-y", "@k-dense-ai/claude-scientific-skills-mcp"],
        env=None,
    ),
    "context7": MCPServerConfig(
        name="context7",
        command="npx",
        args=["-y", "@context7/mcp-server"],
        env=None,
    ),
}


def get_server_config(server_name: str) -> MCPServerConfig:
    """
    Get configuration for a specific MCP server.

    Parameters
    ----------
    server_name : str
        Name of the server

    Returns
    -------
    MCPServerConfig
        Server configuration

    Raises
    ------
    ValueError
        If server_name is not recognized
    """
    config = DEFAULT_MCP_SERVERS.get(server_name)
    if not config:
        raise ValueError(f"Unknown MCP server: {server_name}. Available: {list(DEFAULT_MCP_SERVERS.keys())}")
    return config


def get_enabled_servers() -> List[str]:
    """
    Get list of enabled MCP servers from environment variables.

    Returns
    -------
    List[str]
        List of enabled server names
    """
    enabled = []

    # Check environment variables for each server
    for server_name in DEFAULT_MCP_SERVERS.keys():
        env_var = f"MCP_{server_name.upper()}_ENABLED"
        if os.getenv(env_var, "true").lower() in ("true", "1", "yes"):
            enabled.append(server_name)

    return enabled if enabled else list(DEFAULT_MCP_SERVERS.keys())
