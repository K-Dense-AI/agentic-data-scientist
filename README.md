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
# Simple query
agentic-data-scientist "Explain quantum computing"

# With file upload
agentic-data-scientist "Analyze this data" --files data.csv

# Use Claude Code agent
agentic-data-scientist "Write a Python script" --agent claude_code

# Stream responses
agentic-data-scientist "Complex analysis" --stream
```

#### Python API

```python
from agentic-data-scientist import Agentic Data ScientistCore

# Simple usage
core = Agentic Data ScientistCore()
result = core.run("What is machine learning?")
print(result.response)

# With streaming
async def analyze():
    core = Agentic Data ScientistCore(agent_type="adk")
    async for event in await core.run_async(
        "Analyze this dataset",
        files=[("data.csv", open("data.csv", "rb").read())],
        stream=True
    ):
        if event['type'] == 'message':
            print(f"[{event['author']}] {event['content']}")

# Multi-turn conversation
import asyncio

async def chat():
    core = Agentic Data ScientistCore()
    context = {}
    
    # First turn
    result1 = await core.run_async("What is Python?", context=context)
    
    # Second turn (maintains context)
    result2 = await core.run_async("Give me an example", context=context)

asyncio.run(chat())
```

## Architecture

Agentic Data Scientist uses a layered architecture:

```
┌─────────────────────────────────────┐
│         CLI / Python API            │
├─────────────────────────────────────┤
│         Agentic Data Scientist Core            │
│   (Session & Event Management)      │
├─────────────────────────────────────┤
│           Agent Layer               │
│   ┌──────────┬──────────────────┐  │
│   │   ADK    │   Claude Code    │  │
│   │  Agent   │   CLI Agent      │  │
│   └──────────┴──────────────────┘  │
├─────────────────────────────────────┤
│          MCP Tool Layer             │
│  (filesystem, git, fetch, context7) │
└─────────────────────────────────────┘
```

### Agent Types

**ADK Agent**
- Multi-agent orchestration
- Planning and verification
- Iterative implementation
- Best for: Complex multi-step tasks

**Claude Code CLI Agent**
- Direct Claude integration
- Code-focused tasks
- Streaming execution
- Best for: Coding and scripting

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
MCP_FILESYSTEM_ROOT=/tmp
MCP_GIT_ENABLED=true
MCP_FETCH_ENABLED=true
MCP_CONTEXT7_ENABLED=true
```

### MCP Servers

Agentic Data Scientist uses Model Context Protocol (MCP) servers for tool access:

- **filesystem**: Local file operations
- **git**: Git repository operations
- **fetch**: Web content fetching
- **context7**: Documentation access

See [docs/mcp_configuration.md](docs/mcp_configuration.md) for detailed configuration.

## Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [MCP Configuration](docs/mcp_configuration.md)
- [Extending Agentic Data Scientist](docs/extending.md)

## Examples

See the [examples/](examples/) directory for:
- Basic usage
- Streaming responses
- Multi-turn conversations
- File handling
- Custom configurations

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/K-Dense-AI/agentic-data-scientist-core.git
cd agentic-data-scientist-core

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
ruff format .

# Lint
ruff check --fix .
```

### Project Structure

```
agentic-data-scientist/
├── src/agentic-data-scientist/
│   ├── core/           # Core API and session management
│   ├── agents/         # Agent implementations
│   │   ├── adk/        # ADK agent system
│   │   └── claude_code/# Claude Code CLI agent
│   ├── prompts/        # Prompt templates
│   │   ├── base/       # General prompts
│   │   └── domain/     # Domain-specific prompts
│   ├── mcp/            # MCP integration
│   └── cli/            # CLI interface
├── tests/              # Test suite
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

- GitHub Issues: [Report bugs or request features](https://github.com/K-Dense-AI/agentic-data-scientist-core/issues)
- Documentation: [Full documentation](https://github.com/K-Dense-AI/agentic-data-scientist-core/blob/main/docs)

## Acknowledgments

Built with:
- [Google Agent Development Kit (ADK)](https://github.com/google/adk)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

Made with ❤️ by the K-Dense AI Team

