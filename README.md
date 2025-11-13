# Agentic Data Scientist

**An Adaptive Multi-Agent Framework for Data Science**

Agentic Data Scientist is an open-source framework that uses a sophisticated multi-agent workflow to tackle complex data science tasks. Built on Google's Agent Development Kit (ADK) and Claude, it separates planning from execution, validates work continuously, and adapts its approach based on progress.

## Features

- 🤖 **Adaptive Multi-Agent Workflow**: Iterative planning, execution, validation, and reflection
- 📋 **Intelligent Planning**: Creates comprehensive analysis plans before starting work
- 🔄 **Continuous Validation**: Tracks progress against success criteria at every step
- 🎯 **Self-Correcting**: Reviews and adapts the plan based on discoveries during execution
- 🔌 **MCP Integration**: Tool access via Model Context Protocol servers
- 📁 **File Handling**: Simple file upload and management
- 🛠️ **Extensible**: Customize prompts, agents, and workflows
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
# Analyze data with automatic planning and execution
agentic-data-scientist "Perform differential expression analysis on this RNA-seq data" --files data.csv

# Stream responses to see progress in real-time
agentic-data-scientist "Analyze customer churn patterns" --files customers.csv --stream

# Ask questions
agentic-data-scientist "Explain how gradient boosting works"
```

#### Python API

```python
from agentic_data_scientist import DataScientist

# Simple usage
with DataScientist() as ds:
    result = ds.run("What is machine learning?")
    print(result.response)

# With file upload and streaming
async def analyze():
    async with DataScientist() as ds:
        async for event in await ds.run_async(
            "Analyze this dataset and identify key trends",
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

## How It Works

Agentic Data Scientist uses a multi-phase workflow designed to produce high-quality, reliable results:

### Workflow Design Rationale

**Why separate planning from execution?**
- Thorough analysis of requirements before starting reduces errors and rework
- Clear success criteria established upfront ensure all requirements are met
- Plans can be validated and refined before committing resources to implementation

**Why use iterative refinement?**
- Multiple review loops catch issues early when they're easier to fix
- Both plans and implementations are validated before proceeding
- Continuous feedback improves quality at every step

**Why adapt during execution?**
- Discoveries during implementation often reveal new requirements
- Rigid plans can't accommodate unexpected insights or challenges
- Adaptive replanning ensures the final deliverable meets actual needs

**Why continuous validation?**
- Success criteria tracking provides objective progress measurement
- Early detection of issues prevents wasted effort
- Clear visibility into what's been accomplished and what remains

### The Multi-Agent Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUERY                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │   PLANNING PHASE             │
        │  ┌───────────────────────┐   │
        │  │ Plan Maker            │◄──┤ Iterative refinement
        │  │ "What needs to be     │   │ until plan is complete
        │  │  done?"               │   │ and validated
        │  └──────────┬────────────┘   │
        │             │                 │
        │  ┌──────────▼────────────┐   │
        │  │ Plan Reviewer         │   │
        │  │ "Is this complete?"   │───┤
        │  └──────────┬────────────┘   │
        │             │                 │
        │  ┌──────────▼────────────┐   │
        │  │ Plan Parser           │   │
        │  │ Structures into       │   │
        │  │ executable stages     │   │
        │  └──────────┬────────────┘   │
        └─────────────┼────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │   EXECUTION PHASE            │
        │   (Repeated for each stage)  │
        │                              │
        │  ┌───────────────────────┐   │
        │  │ Coding Agent          │   │
        │  │ Implements the stage  │   │  Stage-by-stage
        │  │ (uses Claude Code)    │   │  implementation with
        │  └──────────┬────────────┘   │  continuous validation
        │             │                 │
        │  ┌──────────▼────────────┐   │
        │  │ Review Agent          │◄──┤ Iterates until
        │  │ "Was this done        │   │ implementation
        │  │  correctly?"          │───┤ is approved
        │  └──────────┬────────────┘   │
        │             │                 │
        │  ┌──────────▼────────────┐   │
        │  │ Criteria Checker      │   │
        │  │ "What have we         │   │
        │  │  accomplished?"       │   │
        │  └──────────┬────────────┘   │
        │             │                 │
        │  ┌──────────▼────────────┐   │
        │  │ Stage Reflector       │   │
        │  │ "What should we do    │   │
        │  │  next?" Adapts plan   │   │
        │  └──────────┬────────────┘   │
        └─────────────┼────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │   SUMMARY PHASE              │
        │  ┌───────────────────────┐   │
        │  │ Summary Agent         │   │
        │  │ Creates comprehensive │   │
        │  │ final report          │   │
        │  └───────────────────────┘   │
        └──────────────────────────────┘
```

### Agent Roles

Each agent in the workflow has a specific responsibility:

- **Plan Maker**: "What needs to be done?" - Creates comprehensive analysis plans with clear stages and success criteria
- **Plan Reviewer**: "Is this plan complete?" - Validates that plans address all requirements before execution begins
- **Plan Parser**: Converts natural language plans into structured, executable stages with trackable success criteria
- **Stage Orchestrator**: Manages the execution cycle - runs stages one at a time, validates progress, and adapts as needed
- **Coding Agent**: Does the actual implementation work (powered by Claude Code SDK with access to 380+ scientific Skills)
- **Review Agent**: "Was this done correctly?" - Validates implementations against requirements before proceeding
- **Criteria Checker**: "What have we accomplished?" - Objectively tracks progress against success criteria after each stage
- **Stage Reflector**: "What should we do next?" - Analyzes progress and adapts remaining stages based on what's been learned
- **Summary Agent**: Synthesizes all work into a comprehensive, publication-ready report

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               CLI / Python API                               │
├──────────────────────────────────────────────────────────────┤
│          Agentic Data Scientist Core                         │
│        (Session & Event Management)                          │
├──────────────────────────────────────────────────────────────┤
│               ADK Multi-Agent Workflow                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Planning Loop (Plan Maker → Reviewer → Parser)         │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Stage Orchestrator                                     │ │
│  │   ├─> Implementation Loop (Coding → Review)           │ │
│  │   ├─> Criteria Checker                                │ │
│  │   └─> Stage Reflector                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Summary Agent                                          │ │
│  └────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                     Tool Layer                               │
│  • MCP: filesystem (read-only), fetch, context7             │
│  • Claude Skills: 380+ scientific databases and packages    │
└──────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required: API keys
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Optional: Model configuration
DEFAULT_MODEL=google/gemini-2.5-pro
CODING_MODEL=claude-sonnet-4-5-20250929

# Optional: MCP server configuration
MCP_FILESYSTEM_ROOT=/path/to/your/data
CONTEXT7_API_KEY=your_context7_key_here
```

### Tools & Skills

**MCP Servers**:
- **filesystem** (planning/review agents): Read-only file operations (read_file, list_directory, search_files, get_file_info)
- **fetch** (planning/review agents): Web content fetching and HTTP requests
- **context7** (coding agent): Library documentation and context retrieval

**Claude Skills** (used by coding agent):
- **380+ Scientific Skills** automatically loaded from [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills)
  - Scientific databases: UniProt, PubChem, PDB, KEGG, PubMed, and more
  - Scientific packages: BioPython, RDKit, PyDESeq2, scanpy, and more
  - Auto-cloned to `.claude/skills/` at agent startup

See [docs/mcp_configuration.md](docs/mcp_configuration.md) for detailed configuration.

## Documentation

- [Getting Started Guide](docs/getting_started.md) - Learn how the workflow operates step by step
- [API Reference](docs/api_reference.md) - Complete API documentation
- [MCP Configuration](docs/mcp_configuration.md) - Configure MCP servers and tools
- [Extending](docs/extending.md) - Customize prompts, agents, and workflows

## Examples

The [examples/](examples/) directory contains practical examples:

**Basic Usage** (`examples/basic_usage.py`)
```python
from agentic_data_scientist import DataScientist

with DataScientist() as ds:
    result = ds.run("What is machine learning?")
    print(result.response)
```

**Streaming** (`examples/streaming_example.py`)
```python
async with DataScientist() as ds:
    async for event in await ds.run_async("Analyze this data", stream=True):
        if event['type'] == 'message':
            print(f"[{event['author']}] {event['content']}")
```

Run examples with:
```bash
uv run python examples/basic_usage.py
```

See [examples/README.md](examples/README.md) for more information.

## Advanced Usage

### Direct Mode (Without Multi-Agent Orchestration)

For simple scripting tasks that don't require planning and validation, you can use direct mode:

```python
from agentic_data_scientist import DataScientist

with DataScientist(agent_type="claude_code") as ds:
    result = ds.run("Write a Python script to parse CSV files")
    print(result.response)
```

Or via CLI:
```bash
agentic-data-scientist "Write a Python script" --mode simple
```

**Note**: Direct mode bypasses the planning and validation workflow, making it suitable only for straightforward coding tasks where you don't need adaptive planning or progress validation.

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
│   │   ├── adk/        # ADK multi-agent workflow
│   │   │   ├── agent.py              # Agent factory
│   │   │   ├── stage_orchestrator.py # Stage-by-stage execution
│   │   │   ├── implementation_loop.py# Coding + review loop
│   │   │   ├── loop_detection.py     # Loop detection agent
│   │   │   └── review_confirmation.py# Review decision logic
│   │   └── claude_code/# Claude Code integration
│   ├── prompts/        # Prompt templates
│   │   ├── base/       # Agent role prompts
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
- API keys for Google AI and Anthropic

## Contributing

Contributions are welcome! Please see our contributing guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

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
