# MCP Configuration

This guide explains how to configure Model Context Protocol (MCP) servers for Agentic Data Scientist.

## Overview

The ADK multi-agent workflow uses MCP servers to provide tools to agents. Different agents have access to different toolsets:

- **Planning and Review Agents** (ADK): Use filesystem and fetch MCP servers for reading files and fetching web content
- **Coding Agent** (Claude Code): Has access to Context7 MCP for library documentation and 380+ scientific Skills for specialized tasks

## MCP Servers

### Filesystem Server

Provides read-only file operations to planning and review agents.

**Available Tools:**
- `read_file`: Read file contents
- `list_directory`: List directory contents
- `search_files`: Search for files by pattern
- `get_file_info`: Get file metadata

**Security:** Write operations are blocked (`write_file`, `delete_file`, `edit_file`) for safety.

**Configuration:**

```bash
# In .env file
MCP_FILESYSTEM_ROOT=/path/to/your/data
```

The filesystem server is restricted to this root directory and cannot access files outside it.

**Usage in Workflow:**

```python
from agentic_data_scientist import DataScientist

# Files uploaded are stored in the session's working directory
# Planning and review agents can read these files using MCP
with DataScientist() as ds:
    result = ds.run(
        "Analyze trends in this data",
        files=[("data.csv", open("data.csv", "rb").read())]
    )
```

### Fetch Server

Provides web content fetching capabilities to agents.

**Available Tools:**
- `fetch`: Fetch content from URLs
- `fetch_html`: Fetch and parse HTML content

**Usage:**

```python
# Agents can automatically fetch web content during analysis
with DataScientist() as ds:
    result = ds.run("Summarize the latest research on transformer architectures from ArXiv")
```

### Context7 Server

Provides documentation and context retrieval capabilities for various libraries and frameworks.

**Available Tools:**
- `resolve-library-id`: Resolve a package name to a Context7-compatible library ID
- `get-library-docs`: Fetch up-to-date documentation for a library

**Configuration:**

Context7 is configured via the `.claude/settings.json` file in the project root:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

**Environment Variable:**

```bash
# In .env file
CONTEXT7_API_KEY=your-api-key-here
```

**Usage:**

```python
# The coding agent can automatically query library documentation
with DataScientist(agent_type="claude_code") as ds:
    result = ds.run("Show me how to use the latest features in pandas 2.0")
```

## Claude Scientific Skills

The coding agent has access to 380+ scientific Skills automatically loaded from [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills).

### Available Skill Categories

**Scientific Databases:**
- UniProt, PubChem, PDB, KEGG, PubMed
- COSMIC, ClinVar, GEO, ENA, Ensembl
- STRING, Reactome, DrugBank, ChEMBL
- And many more...

**Scientific Packages:**
- BioPython, RDKit, PyDESeq2, scanpy, anndata
- MDAnalysis, scikit-learn, PyTorch, TensorFlow
- statsmodels, matplotlib, seaborn, polars
- And many more...

### How Skills Work

1. **Automatic Loading**: Skills are automatically cloned to `.claude/skills/` when the coding agent starts
2. **Agent Discovery**: The coding agent discovers available Skills at runtime
3. **Autonomous Usage**: The agent decides which Skills to use based on the task

### Skill Configuration

Skills are loaded automatically. No configuration needed, but you can customize:

```bash
# In .env file (optional)
CLAUDE_SCIENTIFIC_SKILLS_URL=https://mcp.k-dense.ai/claude-scientific-skills/mcp
```

### Using Skills in Analysis

Skills are used transparently by the coding agent:

```python
from agentic_data_scientist import DataScientist

# The coding agent will automatically use relevant Skills
with DataScientist() as ds:
    result = ds.run(
        "Perform differential expression analysis on this RNA-seq data",
        files=[
            ("sample1.csv", open("sample1.csv", "rb").read()),
            ("sample2.csv", open("sample2.csv", "rb").read())
        ]
    )
    # Coding agent may use: pydeseq2, scanpy, matplotlib, seaborn, etc.
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                ADK Multi-Agent Workflow                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Planning & Review Agents (ADK)                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ • Plan Maker                                 │          │
│  │ • Plan Reviewer                              │          │
│  │ • Review Agent                               │          │
│  │ • Criteria Checker                           │          │
│  │ • Stage Reflector                            │          │
│  │ • Summary Agent                              │          │
│  └────────────────────┬─────────────────────────┘          │
│                       │                                     │
│                       ├─── MCP: filesystem (read-only)      │
│                       └─── MCP: fetch (web content)         │
│                                                             │
│  Coding Agent (Claude Code)                                 │
│  ┌──────────────────────────────────────────────┐          │
│  │ • Implementation                             │          │
│  │ • Code execution                             │          │
│  │ • File operations (read/write)               │          │
│  └────────────────────┬─────────────────────────┘          │
│                       │                                     │
│                       ├─── MCP: context7 (docs)             │
│                       └─── Claude Skills (380+)             │
│                              ├─ Scientific DBs              │
│                              └─ Scientific Packages         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Custom MCP Servers

You can add custom MCP servers for specialized functionality.

### Creating a Custom MCP Server

Example: Database query server

```javascript
// database-mcp-server.js
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import pg from "pg";

const { Pool } = pg;

// Create database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// Create MCP server
const server = new Server(
  {
    name: "database-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tools
server.setRequestHandler("tools/list", async () => {
  return {
    tools: [
      {
        name: "query_select",
        description: "Execute a SELECT query on the database",
        inputSchema: z.object({
          query: z.string().describe("SQL SELECT query to execute"),
        }),
      },
      {
        name: "list_tables",
        description: "List all tables in the database",
        inputSchema: z.object({}),
      },
    ],
  };
});

// Implement tools
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case "query_select": {
      if (!args.query.trim().toUpperCase().startsWith("SELECT")) {
        throw new Error("Only SELECT queries are allowed");
      }
      const result = await pool.query(args.query);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result.rows, null, 2),
          },
        ],
      };
    }
    
    case "list_tables": {
      const result = await pool.query(`
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
      `);
      return {
        content: [
          {
            type: "text",
            text: result.rows.map(r => r.table_name).join("\n"),
          },
        ],
      };
    }
    
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Integrating Custom MCP Server

```python
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StdioConnectionParams,
    StdioServerParameters
)

def get_database_toolset():
    """Create MCP toolset for database access."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="node",
                args=["path/to/database-mcp-server.js"],
                env={"DATABASE_URL": "postgresql://localhost/mydb"}
            ),
        ),
    )

def get_custom_mcp_toolsets(working_dir):
    """Get all MCP toolsets including custom ones."""
    from agentic_data_scientist.mcp import get_mcp_toolsets
    
    # Standard toolsets
    standard = get_mcp_toolsets(working_dir)
    
    # Add custom toolset
    custom = [get_database_toolset()]
    
    return standard + custom
```

Then modify the agent creation to use custom toolsets:

```python
from agentic_data_scientist.agents.adk import create_agent

# Create agent with custom toolsets
agent = create_agent(
    working_dir="/path/to/working/dir",
    mcp_servers=["filesystem", "fetch", "database"]  # Add your custom server
)
```

## Tool Filtering

You can filter which tools are available to agents:

```python
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

def safe_tool_filter(tool) -> bool:
    """Only allow read operations."""
    tool_name = getattr(tool, 'name', None)
    
    # Block write/delete operations
    blocked = ['write_file', 'delete_file', 'drop_table', 'delete_record']
    return tool_name not in blocked

toolset = McpToolset(
    connection_params=connection_params,
    tool_filter=safe_tool_filter,
)
```

## Environment Variables

All MCP-related environment variables:

```bash
# Filesystem MCP
MCP_FILESYSTEM_ROOT=/path/to/data

# Context7 MCP (for documentation retrieval)
CONTEXT7_API_KEY=your-context7-api-key

# Claude Skills (optional, auto-configured)
CLAUDE_SCIENTIFIC_SKILLS_URL=https://mcp.k-dense.ai/claude-scientific-skills/mcp

# Custom MCP servers
CUSTOM_MCP_SERVER_URL=https://your-server.com/mcp
DATABASE_URL=postgresql://localhost/mydb
```

## Security Considerations

### Filesystem Access

The filesystem MCP is configured for **read-only access**:
- Agents can read files but cannot write, edit, or delete
- Access is restricted to `MCP_FILESYSTEM_ROOT` directory
- Cannot access files outside the root directory

### API Access

When using custom MCP servers for API access:
- Store API keys in environment variables, not code
- Use tool filters to restrict dangerous operations
- Implement rate limiting to prevent abuse
- Log all API calls for audit purposes

### Database Access

For database MCP servers:
- Only allow SELECT queries, block INSERT/UPDATE/DELETE
- Use read-only database credentials
- Implement query timeouts
- Filter sensitive tables from access

## Troubleshooting

### MCP Server Connection Issues

**Problem:** "Failed to connect to MCP server"

**Solutions:**
1. Verify Node.js is installed: `node --version`
2. Check server script path is correct
3. Ensure environment variables are set
4. Check server logs for errors

### Filesystem Access Issues

**Problem:** "Permission denied" when reading files

**Solutions:**
1. Verify `MCP_FILESYSTEM_ROOT` is set correctly
2. Check file permissions
3. Ensure path is within the root directory
4. Try absolute paths instead of relative paths

### Skills Not Loading

**Problem:** Scientific Skills not available to coding agent

**Solutions:**
1. Check internet connection (Skills are cloned from GitHub)
2. Verify `ANTHROPIC_API_KEY` is set
3. Check `.claude/skills/` directory exists in working directory
4. Review logs for cloning errors

### Custom MCP Server Issues

**Problem:** Custom tools not appearing

**Solutions:**
1. Verify server implements MCP protocol correctly
2. Check server is running and accessible
3. Review tool registration code
4. Enable debug logging to see tool discovery

## Examples

### Example 1: Analysis with File Upload

```python
from agentic_data_scientist import DataScientist

# Planning agents use filesystem MCP to read uploaded files
# Coding agent uses Skills for implementation
with DataScientist() as ds:
    result = ds.run(
        "Perform PCA on this gene expression dataset",
        files=[("expression_data.csv", open("data.csv", "rb").read())]
    )
```

**What Happens:**
1. Files uploaded to session working directory
2. Plan Maker uses filesystem MCP to inspect data structure
3. Coding Agent uses scanpy/anndata Skills for PCA implementation
4. Review Agent uses filesystem MCP to verify outputs

### Example 2: Web Content Analysis

```python
# Agents use fetch MCP to retrieve web content
with DataScientist() as ds:
    result = ds.run(
        "Summarize recent papers on CRISPR from PubMed"
    )
```

**What Happens:**
1. Plan includes fetching papers from PubMed
2. Agents use fetch MCP or pubmed-database Skill to get papers
3. Coding Agent processes and summarizes content

### Example 3: Database Analysis

```python
# With custom database MCP server
with DataScientist() as ds:
    result = ds.run(
        "Analyze sales trends from the company database"
    )
```

**What Happens:**
1. Agents use custom database MCP to query data
2. Data retrieved and analyzed
3. Results summarized in report

## See Also

- [Getting Started Guide](getting_started.md) - Basic usage
- [API Reference](api_reference.md) - Complete API docs
- [Extending Guide](extending.md) - Custom toolsets
- [MCP Specification](https://modelcontextprotocol.io/) - Protocol details
