# Agentic Data Scientist

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/K-Dense-AI/agentic-data-scientist/pulls)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/agentic-data-scientist.svg?icon=si%3Apython)](https://badge.fury.io/py/agentic-data-scientist)
[![X](https://img.shields.io/badge/Follow_on_X-%40k__dense__ai-000000?logo=x)](https://x.com/k_dense_ai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-K--Dense_Inc.-0A66C2?logo=linkedin)](https://www.linkedin.com/company/k-dense-inc)
[![YouTube](https://img.shields.io/badge/YouTube-K--Dense_Inc.-FF0000?logo=youtube)](https://www.youtube.com/@K-Dense-Inc)

## K-Dense Web

For users requiring access to substantially more powerful capabilities, **K-Dense Web** is available. Visit [k-dense.ai](https://k-dense.ai) to learn more.

**An Adaptive Multi-Agent Framework for Data Science**

Agentic Data Scientist is an open-source framework that uses a sophisticated multi-agent workflow to tackle complex data science tasks. Built on Google's Agent Development Kit (ADK) and Claude Agent SDK, it separates planning from execution, validates work continuously, and adapts its approach based on progress.

> ⭐ **If Agentic Data Scientist saves you time or helps your work move faster, please [star this repository](https://github.com/K-Dense-AI/agentic-data-scientist).** A star helps other data scientists, engineers, and open-source contributors find the project, and gives us a clear reason to keep expanding it for the community.

> **Stay up to date:** Follow K-Dense on [X](https://x.com/k_dense_ai), [LinkedIn](https://www.linkedin.com/company/k-dense-inc), and [YouTube](https://www.youtube.com/@K-Dense-Inc) for new features, release announcements, walkthroughs, and research workflow demos.

## Features

- 🤖 **Adaptive Multi-Agent Workflow**: Iterative planning, execution, validation, and reflection
- 📋 **Intelligent Planning**: Creates comprehensive analysis plans before starting work
- 🔄 **Continuous Validation**: Tracks progress against success criteria at every step
- 🎯 **Self-Correcting**: Reviews and adapts the plan based on discoveries during execution
- 🔌 **MCP Integration**: Tool access via Model Context Protocol servers (Context7 for live library docs)
- 🧠 **Claude Scientific Skills Integration**: Access advanced Claude Skills directly within your workflows
- 📁 **File Handling**: Simple file upload and management
- 🛠️ **Extensible**: Customize prompts, agents, and workflows
- 📦 **Easy Installation**: Available via pip and uvx

## Quick Start

### Prerequisites

Before using Agentic Data Scientist, you must have:

1. **Claude Code CLI** installed
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
   Or visit [Claude Code Quickstart](https://code.claude.com/docs/en/quickstart)

2. **Required API Keys** configured (see Configuration section below)
   - OPENROUTER_API_KEY (for planning and review agents)
   - ANTHROPIC_API_KEY (for coding agent)

### Installation

```bash
# Install from PyPI
uv tool install agentic-data-scientist

# Or use with uvx (no installation needed)
uvx agentic-data-scientist --mode simple "your query here"
```

### Configuration

**API Keys**

You must configure two API keys:

1. **OpenRouter API Key** (required for planning and review agents):
   ```bash
   export OPENROUTER_API_KEY="your_key_here"
   ```
   Get your key at: https://openrouter.ai/keys

2. **Anthropic API Key** (required for coding agent):
   ```bash
   export ANTHROPIC_API_KEY="your_key_here"
   ```
   Get your key at: https://console.anthropic.com/

Alternatively, create a `.env` file in your project directory:
```bash
OPENROUTER_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

**Network Access Control** (Optional)

By default, agents have access to network tools (web search and URL fetching). To disable network access:

```bash
export DISABLE_NETWORK_ACCESS=true
```

This disables:
- `fetch_url` tool for ADK agents
- `WebFetch` and `WebSearch` tools for Claude Code agent

Network access is enabled by default. Set to "true" or "1" to disable.

### Basic Usage

**Important**: You must specify `--mode` to choose your execution strategy. This ensures you're aware of the complexity and API costs.

**Working Directory**: By default, files are saved to `./agentic_output/` in your current directory and preserved after completion. Use `--temp-dir` for temporary storage with auto-cleanup.

#### Orchestrated Mode (Full Multi-Agent Workflow)

```bash
# Complex analysis with planning, execution, and validation
agentic-data-scientist "Perform differential expression analysis" --mode orchestrated --files data.csv

# Multiple files with custom working directory
agentic-data-scientist "Compare datasets" --mode orchestrated -f data1.csv -f data2.csv --working-dir ./my_analysis

# Directory upload (recursive)
agentic-data-scientist "Analyze all data" --mode orchestrated --files data_folder/
```

#### Simple Mode (Direct Coding, No Planning)

```bash
# Quick coding tasks without planning overhead
agentic-data-scientist "Write a Python script to parse CSV files" --mode simple

# Question answering
agentic-data-scientist "Explain how gradient boosting works" --mode simple

# Fast analysis with temporary directory
agentic-data-scientist "Quick data exploration" --mode simple --files data.csv --temp-dir
```

#### Additional Options

```bash
# Custom log file location
agentic-data-scientist "Analyze data" --mode orchestrated --files data.csv --log-file ./analysis.log

# Verbose logging for debugging
agentic-data-scientist "Debug issue" --mode simple --files data.csv --verbose

# Keep files (override default preservation)
agentic-data-scientist "Generate report" --mode orchestrated --files data.csv --keep-files
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
        │             │                │
        │  ┌──────────▼────────────┐   │
        │  │ Plan Reviewer         │   │
        │  │ "Is this complete?"   │───┤
        │  └──────────┬────────────┘   │
        │             │                │
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
        │             │                │
        │  ┌──────────▼────────────┐   │
        │  │ Review Agent          │◄──┤ Iterates until
        │  │ "Was this done        │   │ implementation
        │  │  correctly?"          │───┤ is approved
        │  └──────────┬────────────┘   │
        │             │                │
        │  ┌──────────▼────────────┐   │
        │  │ Criteria Checker      │   │
        │  │ "What have we         │   │
        │  │  accomplished?"       │   │
        │  └──────────┬────────────┘   │
        │             │                │
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
- **Coding Agent**: Does the actual implementation work (powered by Claude Code SDK with access to 143 scientific Skills)
- **Review Agent**: "Was this done correctly?" - Validates implementations against requirements before proceeding
- **Criteria Checker**: "What have we accomplished?" - Objectively tracks progress against success criteria after each stage
- **Stage Reflector**: "What should we do next?" - Analyzes progress and adapts remaining stages based on what's been learned
- **Summary Agent**: Synthesizes all work into a comprehensive, publication-ready report

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CLI Interface                             │
├──────────────────────────────────────────────────────────────┤
│          Agentic Data Scientist Core                         │
│        (Session & Event Management)                          │
├──────────────────────────────────────────────────────────────┤
│               ADK Multi-Agent Workflow                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Planning Loop (Plan Maker → Reviewer → Parser)         │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Stage Orchestrator                                     │  |
│  │   ├─> Implementation Loop (Coding → Review)            │  │
│  │   ├─> Criteria Checker                                 │  │
│  │   └─> Stage Reflector                                  │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Summary Agent                                          │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                     Tool Layer                               │
│  • Built-in Tools: Read-only file ops, web fetch             │
│  • Claude Scientific Skills: 143 skills                      │
│  • MCP Servers: Context7 (library documentation)             │
└──────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required: API keys
ANTHROPIC_API_KEY=your_key_here       # Claude Agent SDK (coding agent)
OPENROUTER_API_KEY=your_key_here      # ADK planning and review agents

# Optional: Model configuration (defaults shown)
DEFAULT_MODEL=google/gemini-3.5-flash
REVIEW_MODEL=google/gemini-3.5-flash
CODING_MODEL=claude-opus-4-8          # Must be an Anthropic model available in Claude Code

# Optional: OpenRouter configuration (defaults shown)
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OR_SITE_URL=k-dense.ai
OR_APP_NAME=Agentic Data Scientist

# Optional: Context7 API key for enhanced library documentation access
CONTEXT7_API_KEY=your_key_here

# Optional: Disable network access (web search/fetch)
DISABLE_NETWORK_ACCESS=true
```

### Tools & Skills

**Built-in Tools** (planning/review agents):
- **File Operations**: Read-only file access within working directory
  - `read_file`, `read_media_file`, `list_directory`, `directory_tree`, `search_files`, `get_file_info`
- **Web Operations**: HTTP fetch for retrieving web content
  - `fetch_url`

**Claude Scientific Skills** (coding agent):
- **143 Scientific Skills** automatically loaded from [scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
  - Scientific databases: UniProt, PubChem, PDB, KEGG, PubMed, and more
  - Scientific packages: BioPython, RDKit, PyDESeq2, scanpy, and more
  - Auto-cloned to `.claude/skills/` at coding agent startup

**MCP Servers** (coding agent):
- **Context7**: Up-to-date library and framework documentation is available to the coding agent via the [Context7](https://context7.com/) MCP server (`https://mcp.context7.com/mcp`). Set `CONTEXT7_API_KEY` for higher rate limits.

All built-in tools are sandboxed to the working directory for security.

## Documentation

- [Getting Started Guide](docs/getting_started.md) - Learn how the workflow operates step by step
- [API Reference](docs/api_reference.md) - Complete API documentation
- [Tools Configuration](docs/tools_configuration.md) - Configure tools and skills
- [Extending](docs/extending.md) - Customize prompts, agents, and workflows

## Examples

### Orchestrated Mode Use Cases

**Complex Data Analysis**
```bash
# Differential expression analysis with multiple files
agentic-data-scientist "Perform DEG analysis comparing treatment vs control" \
  --mode orchestrated \
  --files treatment_data.csv \
  --files control_data.csv
```

**Multi-Step Workflows**
```bash
# Complete analysis pipeline with visualization
agentic-data-scientist "Analyze customer churn, create predictive model, and generate report" \
  --mode orchestrated \
  --files customers.csv \
  --working-dir ./churn_analysis
```

**Directory Processing**
```bash
# Process entire dataset directory
agentic-data-scientist "Analyze all CSV files and create summary statistics" \
  --mode orchestrated \
  --files ./raw_data/
```

### Simple Mode Use Cases

**Quick Scripts**
```bash
# Generate utility scripts
agentic-data-scientist "Write a Python script to merge CSV files by common column" \
  --mode simple
```

**Code Explanation**
```bash
# Technical questions
agentic-data-scientist "Explain the difference between Random Forest and Gradient Boosting" \
  --mode simple
```

**Fast Prototypes**
```bash
# Quick analysis with temporary workspace
agentic-data-scientist "Create a basic scatter plot from this data" \
  --mode simple \
  --files data.csv \
  --temp-dir
```

### Working Directory Examples

```bash
# Default behavior (./agentic_output/ with file preservation)
agentic-data-scientist "Analyze data" --mode orchestrated --files data.csv

# Temporary directory (auto-cleanup)
agentic-data-scientist "Quick test" --mode simple --files data.csv --temp-dir

# Custom location
agentic-data-scientist "Project analysis" --mode orchestrated --files data.csv --working-dir ./my_project

# Custom location with explicit cleanup
agentic-data-scientist "Temporary analysis" --mode simple --files data.csv --working-dir ./temp --keep-files=false
```

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
│   │   ├── api.py                    # DataScientist entry point
│   │   └── events.py                 # Event types and handling
│   ├── agents/         # Agent implementations
│   │   ├── adk/        # ADK multi-agent workflow
│   │   │   ├── agent.py              # Agent factory
│   │   │   ├── stage_orchestrator.py # Stage-by-stage execution
│   │   │   ├── implementation_loop.py# Coding + review loop
│   │   │   ├── loop_detection.py     # Loop detection agent
│   │   │   ├── review_confirmation.py# Review decision logic
│   │   │   ├── event_compression.py  # Context window management
│   │   │   └── utils.py              # Model config & shared helpers
│   │   └── claude_code/# Claude Code integration
│   │       ├── agent.py              # Claude Agent SDK wrapper
│   │       └── templates.py          # Prompt/context templates
│   ├── prompts/        # Prompt templates
│   │   ├── base/       # Agent role prompts
│   │   └── domain/     # Domain-specific prompts (e.g. bioinformatics)
│   ├── tools/          # Built-in tools (file ops, web fetch)
│   └── cli/            # CLI interface
├── tests/              # Test suite (unit + integration)
└── docs/               # Documentation
```

## Requirements

- Python 3.12+
- Node.js (for Claude Code)
- API keys for Anthropic and OpenRouter

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
# Fork and clone, then:
uv sync --extra dev
# Make changes, add tests
uv run pytest tests/ -v
# Submit PR
```

## Release Process

For maintainers:

1. **Create and push tag:**
   ```bash
   ./scripts/release.sh 0.2.0
   ```

2. **Create GitHub release:**
   - Go to https://github.com/K-Dense-AI/agentic-data-scientist/releases/new?tag=v0.2.0
   - Click "Generate release notes" for automatic changelog
   - Publish release
   - Package automatically publishes to PyPI

**One-time PyPI Setup:** Configure [trusted publishing](https://docs.pypi.org/trusted-publishers/) on PyPI with repo `K-Dense-AI/agentic-data-scientist` and workflow `pypi-publish.yml`.

Use conventional commits (`feat:`, `fix:`, `docs:`, etc.) for clean changelogs.

## Technical Notes

### Context Window Management

The framework implements aggressive event compression to manage context window usage during long-running analyses:

#### Event Compression Strategy

- **Automatic Compression**: Events are automatically compressed when count exceeds threshold (default: 40 events)
- **LLM-based Summarization**: Old events are summarized using LLM before removal to preserve critical context
- **Aggressive Truncation**: Large text content (>10KB) is truncated to prevent token overflow
- **Direct Event Queue Manipulation**: Uses direct assignment to `session.events` to ensure changes take effect

#### Preventing Token Overflow

The system employs multiple layers of protection:

- **Callback-based compression**: Triggers automatically after each agent turn
- **Manual compression**: Triggered at key orchestration points (e.g., after implementation loop)
- **Hard limit trimming**: Emergency fallback that discards old events if count exceeds maximum
- **Large text truncation**: Prevents individual events from consuming excessive tokens

These mechanisms work together to keep the total context under 1M tokens even during complex multi-stage analyses.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/K-Dense-AI/agentic-data-scientist/issues)
- Join our Slack Community: [K-Dense Community](https://join.slack.com/t/k-densecommunity/shared_invite/zt-3iajtyls1-EwmkwIZk0g_o74311Tkf5g)
- Documentation: [Full documentation](https://github.com/K-Dense-AI/agentic-data-scientist/blob/main/docs)
- Updates and demos: Follow us on [X](https://x.com/k_dense_ai), [LinkedIn](https://www.linkedin.com/company/k-dense-inc), and [YouTube](https://www.youtube.com/@K-Dense-Inc) to keep up with new features, tutorials, and releases

## Acknowledgments

Built with:
- [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills)

## License

MIT License - see [LICENSE](LICENSE) for details.

Copyright © 2025 K-Dense Inc. ([k-dense.ai](https://k-dense.ai))

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=K-Dense-AI/agentic-data-scientist&type=date&legend=top-left)](https://www.star-history.com/#K-Dense-AI/agentic-data-scientist&type=date&legend=top-left)
