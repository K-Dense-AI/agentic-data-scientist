# Getting Started with Agentic Data Scientist

This guide will help you get up and running with Agentic Data Scientist quickly.

## Installation

### Using pip

```bash
pip install agentic-data-scientist
```

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Or use directly with uvx (no installation needed)
uvx agentic-data-scientist "your query here"
```

## Prerequisites

- Python 3.12 or later
- Node.js (for MCP servers)
- API keys:
  - `ANTHROPIC_API_KEY` for Claude Code agent
  - `GOOGLE_API_KEY` for ADK agents (optional)

## Quick Start

### 1. Set up environment variables

Create a `.env` file in your project root:

```bash
# Required: API keys
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here  # Optional, for ADK agents

# Optional: Model configuration
DEFAULT_MODEL=google/gemini-2.5-pro
CODING_MODEL=claude-sonnet-4-5-20250929

# Optional: MCP server configuration
MCP_FILESYSTEM_ROOT=/path/to/your/data
CLAUDE_SCIENTIFIC_SKILLS_URL=https://mcp.k-dense.ai/claude-scientific-skills/mcp
```

### 2. Simple CLI Usage

```bash
# Ask a simple question (uses orchestrated mode by default)
agentic-data-scientist "What is quantum computing?"

# Analyze a file
agentic-data-scientist "Analyze this data" --files data.csv

# Use simple mode (direct Claude Code without orchestration)
agentic-data-scientist "Write a Python script to parse CSV" --mode simple

# Stream responses for real-time output
agentic-data-scientist "Complex analysis task" --stream
```

### 3. Python API Usage

#### Basic Usage

```python
from agentic_data_scientist import DataScientist

# Create an instance
ds = DataScientist(agent_type="adk")

# Run a simple query
result = ds.run("What is machine learning?")
print(result.response)

# Clean up
ds.cleanup()
```

#### Using Context Manager

```python
from agentic_data_scientist import DataScientist

with DataScientist(agent_type="claude_code") as ds:
    result = ds.run("Write a function to calculate fibonacci numbers")
    print(result.response)
    print(f"Created files: {result.files_created}")
```

#### Async Usage with Streaming

```python
import asyncio
from agentic_data_scientist import DataScientist

async def analyze_data():
    async with DataScientist(agent_type="adk") as ds:
        async for event in await ds.run_async(
            "Analyze this dataset",
            files=[("data.csv", open("data.csv", "rb").read())],
            stream=True
        ):
            if event['type'] == 'message':
                print(f"[{event['author']}] {event['content']}")
            elif event['type'] == 'completed':
                print(f"Duration: {event['duration']}s")

asyncio.run(analyze_data())
```

#### Multi-turn Conversation

```python
import asyncio
from agentic_data_scientist import DataScientist

async def chat():
    async with DataScientist() as ds:
        context = {}
        
        # First turn
        result1 = await ds.run_async(
            "What is data science?",
            context=context
        )
        print("AI:", result1.response)
        
        # Second turn (maintains context)
        result2 = await ds.run_async(
            "What are the key skills needed?",
            context=context
        )
        print("AI:", result2.response)

asyncio.run(chat())
```

## Agent Types

### ADK Agent (`agent_type="adk"`)

- **Best for**: Complex multi-step tasks requiring planning
- **Features**:
  - Multi-agent orchestration
  - Automatic planning and verification
  - Iterative implementation with Claude Code
  - Access to MCP tools (filesystem, fetch, claude-scientific-skills)

### Claude Code Agent (`agent_type="claude_code"`)

- **Best for**: Direct coding and scripting tasks
- **Features**:
  - Direct Claude Sonnet 4.5 integration
  - Code execution capabilities
  - Real-time streaming
  - Access to claude-scientific-skills MCP

## Working with Files

```python
from agentic_data_scientist import DataScientist

# Upload files for analysis
with DataScientist() as ds:
    result = ds.run(
        "Analyze the trends in this data",
        files=[
            ("sales.csv", open("sales.csv", "rb").read()),
            ("inventory.csv", open("inventory.csv", "rb").read()),
        ]
    )
    
    # Files are available in the working directory
    print(f"Working directory: {ds.working_dir}")
    print(f"Files created: {result.files_created}")
```

## Next Steps

- [API Reference](api_reference.md) - Detailed API documentation
- [MCP Configuration](mcp_configuration.md) - Configure MCP servers
- [Extending](extending.md) - Customize and extend functionality
- [Examples](../examples/) - More usage examples

## Troubleshooting

### Common Issues

**ImportError: No module named 'agentic_data_scientist'**
- Make sure you've installed the package: `pip install agentic-data-scientist`
- Or use `uv sync` to install dependencies

**API Key Errors**
- Ensure your `.env` file is in the correct location
- Verify API keys are valid and have sufficient credits

**MCP Server Connection Failures**
- Ensure Node.js is installed: `node --version`
- Check MCP server URLs are accessible
- For local MCP servers, ensure they're running

### Getting Help

- Check the [documentation](../README.md)
- Open an issue on [GitHub](https://github.com/K-Dense-AI/agentic-data-scientist/issues)
- Review [examples](../examples/) for working code

