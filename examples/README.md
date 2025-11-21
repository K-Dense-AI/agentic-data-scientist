# Examples

This directory contains practical examples showing how to use Agentic Data Scientist.

## Available Examples

### Basic Usage
**File:** `basic_usage.py`

Simple synchronous example showing:
- Creating a DataScientist instance with context manager
- Running a basic query
- Checking results and handling errors

**Run:**
```bash
uv run python examples/basic_usage.py
```

### Streaming
**File:** `streaming_example.py`

Asynchronous example demonstrating:
- Real-time event streaming
- Processing different event types (messages, function calls, completions)
- Async context manager usage

**Run:**
```bash
uv run python examples/streaming_example.py
```

### Multi-turn Conversation
**File:** `multi_turn_conversation.py`

Shows conversation context management:
- Maintaining context across multiple queries
- Building on previous responses
- Session management

**Run:**
```bash
uv run python examples/multi_turn_conversation.py
```

### Context7 Documentation Retrieval
**File:** `context7_example.py`

Demonstrates using Context7 MCP for library documentation:
- Querying up-to-date library documentation
- Getting examples for latest features
- Using Context7 with Claude Code agent

**Requirements:**
- `CONTEXT7_API_KEY` environment variable
- Manual configuration in `.claude/settings.json`:
  ```json
  {
    "mcpServers": {
      "context7": {
        "command": "npx",
        "args": ["-y", "@context7/mcp-server"],
        "env": {
          "CONTEXT7_API_KEY": "your_key_here"
        }
      }
    }
  }
  ```

**Run:**
```bash
uv run python examples/context7_example.py
```

## Sample Data

**File:** `test_data.csv`

Sample dataset for testing data analysis queries. Contains sales data by month, product, and region.

## Prerequisites

Before running examples, ensure you have:

1. **API Keys** set in your environment:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   export GOOGLE_API_KEY=your_key_here  # Optional, for ADK agents
   ```

2. **Dependencies** installed:
   ```bash
   uv sync
   ```

## Example Output

Each example includes detailed output showing:
- Query being processed
- Agent responses
- Duration and session information
- Any files created

## More Examples

For more advanced usage, see:
- [Getting Started Guide](../docs/getting_started.md) - Comprehensive tutorials
- [API Reference](../docs/api_reference.md) - Complete API documentation
- [Extending Guide](../docs/extending.md) - Customization examples

## Modifying Examples

Feel free to modify these examples to test different:
- Queries and prompts
- Agent types (`adk` vs `claude_code`)
- Models and configurations
- File uploads and data processing

All examples use the same `DataScientist` API, so you can easily adapt them for your needs.

