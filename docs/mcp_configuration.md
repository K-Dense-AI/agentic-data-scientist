# MCP Configuration Guide

This guide explains how to configure Model Context Protocol (MCP) servers with Agentic Data Scientist.

## Overview

Agentic Data Scientist uses MCP servers to provide tools to agents. The framework comes with three pre-configured MCP servers:

1. **filesystem**: Read-only file system access
2. **fetch**: Web content fetching
3. **claude-scientific-skills**: Advanced scientific computing tools (hosted)

## Pre-configured MCP Servers

### Filesystem MCP (Read-Only)

Provides read-only access to the file system for ADK agents.

**Allowed Operations:**
- `read_file` - Read file contents
- `read_multiple_files` - Read multiple files at once
- `list_directory` - List directory contents
- `search_files` - Search for files by pattern
- `get_file_info` - Get file metadata
- `list_allowed_directories` - List accessible directories

**Configuration:**
```bash
# Set the root directory (default: /tmp)
export MCP_FILESYSTEM_ROOT=/path/to/your/data
```

**Note:** Write operations (`write_file`, `delete_file`, etc.) are intentionally disabled for security.

### Fetch MCP

Provides web content fetching capabilities.

**Operations:**
- Fetch web pages
- Download content
- Process HTTP requests

**Note:** No additional configuration required. Works out of the box.

### Claude Scientific Skills MCP (Hosted)

Provides advanced scientific computing and analysis tools via a hosted MCP server.

**Configuration:**
```bash
# Default URL (provided by K-Dense AI)
export CLAUDE_SCIENTIFIC_SKILLS_URL=https://mcp.k-dense.ai/claude-scientific-skills/mcp
```

**Features:**
- Advanced mathematical computations
- Scientific data analysis
- Statistical tools
- And more scientific capabilities

## Agent-Specific MCP Configuration

### ADK Agents

ADK agents have access to all three MCP servers:
- **filesystem** (read-only)
- **fetch**
- **claude-scientific-skills**

These are configured automatically when creating an ADK agent.

### Claude Code Agents

Claude Code agents have access to:
- **claude-scientific-skills** (hosted MCP via Claude Agent SDK)

Configuration is handled automatically through the Claude Agent SDK's MCP support.

## Environment Variables

### MCP Server URLs

```bash
# Claude Scientific Skills URL (default shown)
CLAUDE_SCIENTIFIC_SKILLS_URL=https://mcp.k-dense.ai/claude-scientific-skills/mcp
```

### Filesystem Configuration

```bash
# Root directory for filesystem MCP (default: /tmp)
MCP_FILESYSTEM_ROOT=/path/to/your/data

# Example: Use current project directory
MCP_FILESYSTEM_ROOT=$(pwd)
```

## Advanced Configuration

### Custom MCP Toolsets

You can customize MCP toolsets in your code:

```python
from agentic_data_scientist.mcp import (
    get_filesystem_toolset,
    get_fetch_toolset,
    get_claude_scientific_skills_toolset,
)

# Get individual toolsets
fs_toolset = get_filesystem_toolset(working_dir="/custom/path")
fetch_toolset = get_fetch_toolset()
css_toolset = get_claude_scientific_skills_toolset()

# Use with custom agent configuration
# (Advanced use case - see extending.md)
```

### Custom Tool Filters

The filesystem toolset uses a tool filter to restrict operations to read-only:

```python
from agentic_data_scientist.mcp.config import filesystem_tool_filter

# The filter allows only these operations:
allowed_operations = [
    "read_file",
    "read_multiple_files",
    "list_directory",
    "search_files",
    "get_file_info",
    "list_allowed_directories",
]
```

To create a custom filter:

```python
def my_custom_filter(tool):
    """Custom tool filter."""
    tool_name = getattr(tool, 'name', tool.get('name') if isinstance(tool, dict) else None)
    # Add your filtering logic
    return tool_name in my_allowed_operations
```

## Troubleshooting

### Common Issues

#### MCP Server Connection Failures

**Problem:** Cannot connect to MCP server

**Solutions:**
1. Check that Node.js is installed:
   ```bash
   node --version
   ```

2. Verify the MCP server URL is accessible:
   ```bash
   curl https://mcp.k-dense.ai/claude-scientific-skills/mcp
   ```

3. Check network connectivity and firewall settings

#### Filesystem Access Denied

**Problem:** Cannot access files in a directory

**Solutions:**
1. Ensure `MCP_FILESYSTEM_ROOT` is set correctly:
   ```bash
   echo $MCP_FILESYSTEM_ROOT
   ```

2. Check file permissions on the target directory

3. Verify the path is absolute, not relative

#### Tool Not Available

**Problem:** Expected MCP tool is not available

**Solutions:**
1. Verify the MCP server is running and accessible

2. Check that the tool is not filtered out (for filesystem MCP)

3. Review agent logs for tool loading errors

### Debugging

Enable debug logging to see MCP tool loading:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

You should see log messages like:
```
INFO: Configured 3 MCP toolsets
DEBUG: Loading MCP tools from filesystem
DEBUG: Loading MCP tools from fetch
DEBUG: Loading MCP tools from claude-scientific-skills
```

## Security Considerations

### Read-Only Filesystem Access

The filesystem MCP is intentionally configured as read-only for ADK agents to prevent:
- Accidental file modifications
- Data loss
- Security vulnerabilities

If you need write access, you should:
1. Use Claude Code agent with appropriate permissions
2. Implement custom tool filtering
3. Use a dedicated working directory

### Data Privacy

When using hosted MCP servers:
- Be aware that data may be sent to external services
- Review the hosted MCP server's privacy policy
- Use environment-specific configuration for sensitive data

### Network Security

For production deployments:
- Use HTTPS for hosted MCP servers
- Implement authentication where supported
- Consider using private/internal MCP servers

## MCP Server Development

### Creating Custom MCP Servers

You can create custom MCP servers for specific use cases. See the [MCP Specification](https://modelcontextprotocol.io/) for details.

Basic structure:
```python
# custom_mcp_server.py
from mcp.server import Server
from mcp import StdioServerParameters

app = Server("my-custom-server")

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "my_tool",
            "description": "Custom tool",
            "inputSchema": { ... }
        }
    ]

@app.call_tool()
async def call_tool(name, arguments):
    if name == "my_tool":
        # Tool implementation
        return result
```

### Integrating Custom MCP Servers

To integrate a custom MCP server:

```python
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams, StdioServerParameters

custom_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["custom_mcp_server.py"],
        ),
    ),
)
```

## Best Practices

1. **Use appropriate MCP servers** for your use case
   - Filesystem for data access
   - Fetch for web content
   - Claude Scientific Skills for scientific computing

2. **Configure working directories carefully**
   - Use absolute paths
   - Ensure proper permissions
   - Isolate sessions with temp directories

3. **Monitor MCP server health**
   - Check logs for connection issues
   - Implement retry logic for transient failures
   - Use timeout configuration

4. **Secure sensitive data**
   - Don't expose credentials in MCP configurations
   - Use environment variables
   - Implement access controls

## See Also

- [Getting Started Guide](getting_started.md)
- [API Reference](api_reference.md)
- [Extending Guide](extending.md)
- [MCP Specification](https://modelcontextprotocol.io/)

