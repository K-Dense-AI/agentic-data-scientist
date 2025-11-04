# Agentic Data Scientist

**A General-Purpose Multi-Agent Framework**

Agentic Data Scientist is a streamlined, open-source framework for building and deploying multi-agent AI systems. It provides a clean Python API and CLI for orchestrating complex tasks using Google's Agent Development Kit (ADK) and Claude Code CLI agents.

## Features

- 🤖 **Multi-Agent Architecture**: Hierarchical agent orchestration with ADK
- 💬 **Multiple Agent Types**: Support for ADK agents and Claude Code CLI
- 🔌 **MCP Integration**: Tool access via Model Context Protocol servers
- 📁 **File Handling**: Simple file upload and management
- 🔄 **Session Management**: In-memory conversation context
- 🎯 **Stateless API**: Clean, simple API design
- 🛠️ **Extensible**: Plugin architecture for custom prompts and agents
- 📦 **Easy Installation**: Available via pip and uvx

## Quick Start

### Installation

```bash
# Install from PyPI
pip install agentic-data-scientist

# Or use with uvx (no installation needed)
uvx agentic-data-scientist "your query here"
```

### Basic Usage

#### CLI

```bash
# Simple query (uses orchestrated mode by default)
agentic-data-scientist "Explain quantum computing"

# With file upload
agentic-data-scientist "Analyze this data" --files data.csv

# Simple mode (direct Claude Code without orchestration)
agentic-data-scientist "Write a Python script" --mode simple

# Stream responses in real-time
agentic-data-scientist "Complex analysis" --stream
```

#### Python API

```python
from agentic_data_scientist import DataScientist

# Simple usage
with DataScientist() as ds:
    result = ds.run("What is machine learning?")
    print(result.response)

# With streaming
async def analyze():
    async with DataScientist(agent_type="adk") as ds:
        async for event in await ds.run_async(
            "Analyze this dataset",
            files=[("data.csv", open("data.csv", "rb").read())],
            stream=True
        ):
            if event['type'] == 'message':
                print(f"[{event['author']}] {event['content']}")

# Multi-turn conversation
import asyncio

async def chat():
    async with DataScientist() as ds:
        context = {}
        
        # First turn
        result1 = await ds.run_async("What is Python?", context=context)
        
        # Second turn (maintains context)
        result2 = await ds.run_async("Give me an example", context=context)

asyncio.run(chat())
```

## Architecture

Agentic Data Scientist uses a layered architecture:

```
┌──────────────────────────────────────────┐
│          CLI / Python API                │
├──────────────────────────────────────────┤
│      Agentic Data Scientist Core         │
│    (Session & Event Management)          │
├──────────────────────────────────────────┤
│            Agent Layer                   │
│  ┌────────────────────────────────────┐ │
│  │  ADK Orchestration (Planning +     │ │
│  │  Verification + Implementation)    │ │
│  │    └─> Claude Code (Implementation)│ │
│  │                                    │ │
│  │  Or: Claude Code Direct            │ │
│  └────────────────────────────────────┘ │
├──────────────────────────────────────────┤
│           MCP Tool Layer                 │
│  • filesystem (read-only for ADK)        │
│  • fetch                                 │
│  • claude-scientific-skills (hosted)     │
└──────────────────────────────────────────┘
```

### Agent Types

**ADK Agent** (`agent_type="adk"`)
- Multi-agent orchestration with planning and verification
- Uses Claude Code for implementation tasks
- Access to MCP tools: filesystem (read-only), fetch, claude-scientific-skills
- Best for: Complex multi-step tasks requiring planning

**Claude Code Agent** (`agent_type="claude_code"`)
- Direct Claude Sonnet 4.5 integration
- Code execution and development capabilities
- Access to claude-scientific-skills MCP via Claude Agent SDK
- Streaming execution support
- Best for: Direct coding, scripting, and development tasks

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required: API keys
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Optional: Model configuration
DEFAULT_MODEL=google/gemini-2.5-pro
CODING_MODEL=claude-sonnet-4-5-latest

# Optional: MCP server configuration
MCP_FILESYSTEM_ROOT=/path/to/your/data
CLAUDE_SCIENTIFIC_SKILLS_URL=https://mcp.k-dense.ai/claude-scientific-skills/mcp
```

### MCP Servers

Agentic Data Scientist uses Model Context Protocol (MCP) servers for tool access:

- **filesystem**: Read-only file operations (for ADK agents)
  - Allowed: read_file, list_directory, search_files, get_file_info
  - Blocked: write_file, delete_file, edit_file (for security)
- **fetch**: Web content fetching and HTTP requests
- **claude-scientific-skills**: Hosted scientific computing tools
  - URL: https://mcp.k-dense.ai/claude-scientific-skills/mcp
  - Available to both ADK and Claude Code agents

See [docs/mcp_configuration.md](docs/mcp_configuration.md) for detailed configuration.

## Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [MCP Configuration](docs/mcp_configuration.md)
- [Extending Agentic Data Scientist](docs/extending.md)

## Examples

The [examples/](examples/) directory contains practical, working examples:

### Quick Examples

**Basic Usage** (`examples/basic_usage.py`)
```python
from agentic_data_scientist import DataScientist

with DataScientist(agent_type="adk") as ds:
    result = ds.run("What is machine learning?")
    print(result.response)
```

**Streaming** (`examples/streaming_example.py`)
```python
async with DataScientist(agent_type="adk") as ds:
    async for event in await ds.run_async("Complex task", stream=True):
        if event['type'] == 'message':
            print(f"[{event['author']}] {event['content']}")
```

**Multi-turn Conversation** (`examples/multi_turn_conversation.py`)
```python
async with DataScientist() as ds:
    context = {}
    result1 = await ds.run_async("What is Python?", context=context)
    result2 = await ds.run_async("Give me an example", context=context)
```

Run any example with:
```bash
uv run python examples/basic_usage.py
```

See [examples/README.md](examples/README.md) for detailed information.

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/K-Dense-AI/agentic-data-scientist.git
cd agentic-data-scientist

# Install with dev dependencies using uv
uv sync --extra dev

# Run tests
uv run pytest tests/

# Format code
uv run ruff format .

# Lint
uv run ruff check --fix .
```

### Project Structure

```
agentic-data-scientist/
├── src/agentic_data_scientist/
│   ├── core/           # Core API and session management
│   ├── agents/         # Agent implementations
│   │   ├── adk/        # ADK agent system (orchestration + planning)
│   │   └── claude_code/# Claude Code agent (implementation)
│   ├── prompts/        # Prompt templates
│   │   ├── base/       # General prompts
│   │   └── domain/     # Domain-specific prompts
│   ├── mcp/            # MCP integration (filesystem, fetch, claude-scientific-skills)
│   └── cli/            # CLI interface
├── tests/              # Test suite
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── examples/           # Usage examples
└── docs/               # Documentation
```

## Requirements

- Python 3.11+
- Node.js (for MCP servers)
- API keys for Google AI and/or Anthropic

## Contributing

Contributions are welcome! Please see our contributing guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/K-Dense-AI/agentic-data-scientist/issues)
- Documentation: [Full documentation](https://github.com/K-Dense-AI/agentic-data-scientist/blob/main/docs)

## Acknowledgments

Built with:
- [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

Made with ❤️ by the K-Dense AI Team

