"""
MCP tool registry for ADK integration.

This module provides functions to connect to MCP servers and expose their tools
to ADK agents.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from google.adk.tools import FunctionTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agentic_data_scientist.mcp.config import get_server_config


logger = logging.getLogger(__name__)

# Global registry of active MCP clients
_mcp_clients: Dict[str, ClientSession] = {}
_mcp_contexts: Dict[str, Any] = {}


async def _start_mcp_server(server_name: str) -> Optional[ClientSession]:
    """
    Start an MCP server and return the client session.

    Parameters
    ----------
    server_name : str
        Name of the MCP server to start

    Returns
    -------
    Optional[ClientSession]
        Client session if successful, None otherwise
    """
    try:
        config = get_server_config(server_name)
        logger.info(f"Starting MCP server: {config.name}")

        # Create server parameters
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )

        # Start the server and create client session
        # stdio_client returns an async context manager, so we need to enter it
        stdio_context = stdio_client(server_params)
        read, write = await stdio_context.__aenter__()
        session = ClientSession(read, write)

        # Initialize the session
        await session.initialize()

        # Store in global registry
        _mcp_clients[server_name] = session
        _mcp_contexts[server_name] = (stdio_context, read, write)

        logger.info(f"Successfully started MCP server: {server_name}")
        return session

    except Exception as e:
        logger.error(f"Failed to start MCP server {server_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_mcp_tools(server_names: List[str]) -> List[FunctionTool]:
    """
    Get ADK-compatible tools from MCP servers.

    This function:
    1. Starts requested MCP servers
    2. Queries their tool schemas
    3. Wraps them as ADK FunctionTool objects
    4. Returns list of tools for agent registration

    Parameters
    ----------
    server_names : List[str]
        List of MCP server names to connect to

    Returns
    -------
    List[FunctionTool]
        List of ADK-compatible function tools
    """
    tools = []

    for server_name in server_names:
        try:
            # Skip if already connected
            if server_name in _mcp_clients:
                session = _mcp_clients[server_name]
                logger.info(f"Using existing MCP client for: {server_name}")
            else:
                # Start the server
                session = await _start_mcp_server(server_name)
                if not session:
                    logger.warning(f"Skipping {server_name} - failed to start")
                    continue

            # List available tools from the server
            result = await session.list_tools()

            logger.info(f"Found {len(result.tools)} tools from {server_name}")

            # Convert each MCP tool to ADK Tool
            for mcp_tool in result.tools:
                try:
                    adk_tool = create_adk_tool_from_mcp(
                        mcp_tool_dict=mcp_tool.model_dump(),
                        server_name=server_name,
                        session=session
                    )
                    tools.append(adk_tool)
                    logger.debug(f"Added tool: {mcp_tool.name} from {server_name}")
                except Exception as e:
                    logger.error(f"Failed to convert tool {mcp_tool.name}: {e}")

        except ValueError as e:
            logger.warning(f"Unknown MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Error getting tools from {server_name}: {e}")

    logger.info(f"Total MCP tools loaded: {len(tools)}")
    return tools


def create_adk_tool_from_mcp(
    mcp_tool_dict: dict,
    server_name: str,
    session: ClientSession
) -> FunctionTool:
    """
    Create an ADK FunctionTool from an MCP tool schema.

    Parameters
    ----------
    mcp_tool_dict : dict
        MCP tool schema definition
    server_name : str
        Name of the MCP server providing this tool
    session : ClientSession
        Active MCP client session for calling the tool

    Returns
    -------
    FunctionTool
        ADK-compatible function tool
    """
    tool_name = mcp_tool_dict.get("name")
    tool_description = mcp_tool_dict.get("description", "")
    input_schema = mcp_tool_dict.get("inputSchema", {})

    # Create the tool execution function
    async def tool_function(**kwargs) -> dict:
        """Execute the MCP tool with given arguments."""
        try:
            # Call the MCP tool
            result = await session.call_tool(tool_name, arguments=kwargs)

            # Extract content from result
            if hasattr(result, 'content') and len(result.content) > 0:
                # Get the first content item
                content_item = result.content[0]
                if hasattr(content_item, 'text'):
                    return {"result": content_item.text}
                elif hasattr(content_item, 'data'):
                    return {"result": str(content_item.data)}
                else:
                    return {"result": str(content_item)}
            else:
                return {"result": str(result)}

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"error": str(e)}

    # Create ADK FunctionTool
    adk_tool = FunctionTool(
        name=f"mcp_{server_name}_{tool_name}",
        description=f"[MCP:{server_name}] {tool_description}",
        func=tool_function,
    )

    return adk_tool


async def cleanup_mcp_clients() -> None:
    """
    Clean up all active MCP client sessions.

    This should be called when shutting down the application.
    """
    for server_name in list(_mcp_clients.keys()):
        try:
            logger.info(f"Closing MCP client: {server_name}")
            
            # Get the context manager and exit it
            if server_name in _mcp_contexts:
                stdio_context, read, write = _mcp_contexts[server_name]
                await stdio_context.__aexit__(None, None, None)
                
        except Exception as e:
            logger.error(f"Error closing MCP client {server_name}: {e}")

    _mcp_clients.clear()
    _mcp_contexts.clear()
