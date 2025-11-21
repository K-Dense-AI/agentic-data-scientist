# Tools Configuration

This guide explains the tools available to Agentic Data Scientist agents and how they work.

## Overview

The ADK multi-agent workflow uses local Python function tools to provide file system and web access to agents. Different agents have access to different toolsets:

- **Planning and Review Agents** (ADK): Use local file and web fetch tools for reading files and fetching web content
- **Coding Agent** (Claude Code): Has access to Context7 MCP (optional) for library documentation and 380+ scientific Skills (auto-loaded) for specialized tasks

## Local Tools

All ADK agents have access to a curated set of local Python tools with built-in security controls.

### Security Model

All file operations are **read-only** and enforce **working directory sandboxing**:

- Agents can only access files within their assigned `working_dir`
- Path traversal attempts (e.g., `../`) are blocked if they escape the working directory
- Absolute paths outside the working directory are rejected
- No write, delete, or edit operations are available

This ensures agents cannot modify files or access sensitive system data.

### File Operation Tools

#### read_file

Read text file contents with optional head/tail line limits.

**Parameters:**
- `path` (str): Path to file (relative to working_dir or absolute within working_dir)
- `head` (int, optional): Read only first N lines
- `tail` (int, optional): Read only last N lines

**Usage:**
```python
# Agents automatically use this tool
result = read_file("data/results.csv")
```

#### read_media_file

Read binary/media files (images, audio, etc.) with base64 encoding.

**Parameters:**
- `path` (str): Path to media file

**Returns:**
- JSON string with `data` (base64 encoded) and `mimeType` fields

**Usage:**
```python
# Agents can read and process images
result = read_media_file("plot.png")
```

#### list_directory

List directory contents with optional size display and sorting.

**Parameters:**
- `path` (str, optional): Directory path, default "."
- `show_sizes` (bool, optional): Display file sizes, default False
- `sort_by` (str, optional): Sort order: "name" or "size", default "name"

**Usage:**
```python
# List files in current directory
result = list_directory(".", show_sizes=True)
```

#### directory_tree

Generate a recursive directory tree view with exclusion patterns.

**Parameters:**
- `path` (str, optional): Directory path, default "."
- `exclude_patterns` (list[str], optional): Patterns to exclude (e.g., ["*.pyc", "__pycache__"])

**Returns:**
- JSON string representing the directory tree structure

**Usage:**
```python
# Get full directory tree
result = directory_tree(".", exclude_patterns=["*.pyc"])
```

#### search_files

Search for files matching a glob pattern.

**Parameters:**
- `pattern` (str): Glob pattern (e.g., "*.py", "test_*.txt")
- `path` (str, optional): Directory to search in, default "."
- `exclude_patterns` (list[str], optional): Patterns to exclude from results

**Usage:**
```python
# Find all Python files
result = search_files("*.py", path="src/")
```

#### get_file_info

Get detailed metadata about a file.

**Parameters:**
- `path` (str): Path to file

**Returns:**
- Formatted string with size, type, modified time, accessed time, permissions

**Usage:**
```python
# Get file metadata
result = get_file_info("data.csv")
```

### Web Operation Tools

#### fetch_url

Fetch content from a URL using HTTP GET.

**Parameters:**
- `url` (str): The URL to fetch
- `timeout` (int, optional): Request timeout in seconds, default 30
- `user_agent` (str, optional): Custom User-Agent header

**Returns:**
- Response text content or error message

**Usage:**
```python
# Agents can fetch web content
result = fetch_url("https://api.example.com/data")
```

## Usage in Workflows

### Basic File Access

```python
from agentic_data_scientist import DataScientist

# Files uploaded are stored in the session's working directory
# Planning and review agents can read these files using local tools
with DataScientist() as ds:
    result = ds.run(
        "Analyze trends in this data",
        files=[("data.csv", open("data.csv", "rb").read())]
    )
```

### Web Content Fetching

```python
# Agents can automatically fetch web content during analysis
with DataScientist() as ds:
    result = ds.run("Summarize the latest research on transformer architectures from ArXiv")
```

### Working with Multiple Files

```python
with DataScientist() as ds:
    result = ds.run(
        "Compare the metrics across all JSON files",
        files=[
            ("metrics_v1.json", open("metrics_v1.json", "rb").read()),
            ("metrics_v2.json", open("metrics_v2.json", "rb").read()),
            ("metrics_v3.json", open("metrics_v3.json", "rb").read()),
        ]
    )
```

## Claude Code Agent Tools

The Claude Code agent uses a different toolset configured through `.claude/settings.json`.

### Context7 MCP (Optional)

Provides documentation and context retrieval capabilities for various libraries and frameworks.

**Status:** Optional - The coding agent works without Context7, using Skills for most documentation needs.

**Available Tools:**
- `resolve-library-id`: Resolve a package name to a Context7-compatible library ID
- `get-library-docs`: Fetch up-to-date documentation for a library

**Configuration:**

If you want to enable Context7, configure it via the `.claude/settings.json` file in the project root:

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
# In .env file (optional)
CONTEXT7_API_KEY=your-api-key-here
```

### Claude Scientific Skills (Auto-Loaded)

The coding agent has access to 380+ scientific Skills automatically loaded from [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills).

**Status:** Automatic - No configuration needed. Skills are automatically loaded when the coding agent starts.

**Available Skill Categories:**

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

**How Skills Work:**

1. **Automatic Loading**: Skills are automatically cloned to `.claude/skills/` when the coding agent starts
2. **Agent Discovery**: The coding agent discovers available Skills at runtime
3. **Autonomous Usage**: The agent decides which Skills to use based on the task
4. **No Configuration**: No environment variables or setup required

## Tool Implementation Details

### Adding Custom Tools

You can add custom tools by defining Python functions and adding them to the agent configuration:

```python
from functools import partial
from agentic_data_scientist.agents.adk import create_agent

# Define your custom tool
def custom_analysis_tool(data: str, working_dir: str) -> str:
    """
    Custom analysis tool with working_dir parameter.
    
    Parameters
    ----------
    data : str
        Input data
    working_dir : str
        Working directory for security validation
        
    Returns
    -------
    str
        Analysis results
    """
    # Your custom logic here
    return f"Analyzed: {data}"

# Create agent with custom tools
agent = create_agent(working_dir="/tmp/session")

# To add custom tools, modify the tools list in agent.py
# by appending your partial-bound function:
# tools.append(partial(custom_analysis_tool, working_dir=str(working_dir)))
```

### Tool Function Signature

All file operation tools follow this pattern:

```python
def tool_function(
    # Tool-specific parameters
    path: str,
    # Other parameters...
    # Security parameter (always required for file ops)
    working_dir: str,
) -> str:
    """
    Tool description.
    
    Returns
    -------
    str
        Result or error message
    """
    # Implementation
    pass
```

The `working_dir` parameter is automatically bound using `functools.partial` when tools are configured for agents.

## Environment Variables

**Required for the Framework:**
- `OPENROUTER_API_KEY`: Required for planning/review agents
- `ANTHROPIC_API_KEY`: Required for coding agent

**Optional for Tools:**
- `CONTEXT7_API_KEY`: Optional, only if you want to enable Context7 MCP

**No Environment Variables Needed For:**
- Local file operation tools (work out of the box)
- Web fetch tool (works out of the box)
- Claude Scientific Skills (auto-loaded)

## Security Considerations

### File Access Security

- **Read-Only**: No write, delete, or edit operations available
- **Sandboxed**: All paths validated against working_dir
- **Path Traversal Protection**: Attempts to escape working_dir are blocked
- **Symlink Resolution**: Symlinks are resolved and validated

### Web Fetch Security

- **Protocol Restriction**: Only HTTP and HTTPS protocols allowed
- **Timeout Protection**: Default 30-second timeout prevents hanging
- **Error Handling**: Network errors return safe error messages

### Best Practices

1. **Minimal Permissions**: Agents only have read access to their working directory
2. **Isolated Sessions**: Each session gets its own working directory
3. **Clean Separation**: Planning agents cannot modify implementation files
4. **Audit Trail**: All tool calls are logged for review

## Troubleshooting

### "Access denied: outside working directory"

This error occurs when a tool tries to access a file outside the working directory. Ensure all file paths are:
- Relative to the working directory, or
- Absolute paths within the working directory

### "File does not exist"

The specified file cannot be found. Check:
- File path spelling and case sensitivity
- File was properly uploaded to the session
- Using correct directory structure

### "Request timed out"

Web fetch operation exceeded timeout. Solutions:
- Increase timeout parameter: `fetch_url(url, timeout=60)`
- Check URL is accessible
- Verify network connectivity

## Summary

**Built-in Tools (Planning/Review Agents):**
- File operations: Read-only, sandboxed to working directory
- Web operations: HTTP fetch with timeout protection
- No configuration needed

**Claude Code Tools (Coding Agent):**
- Context7 MCP: Optional, for library documentation
- Scientific Skills: Auto-loaded, 380+ skills for scientific computing
- No configuration needed for Skills

**Environment Variables:**
- Required: `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`
- Optional: `CONTEXT7_API_KEY` (only if using Context7)

