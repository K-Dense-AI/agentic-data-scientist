# Getting Started with Agentic Data Scientist

This guide will help you understand and use the Agentic Data Scientist multi-agent workflow.

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

- Python 3.11 or later
- Node.js (for MCP servers)
- API keys:
  - `ANTHROPIC_API_KEY` for Claude (required)
  - `GOOGLE_API_KEY` for Gemini models (required)

## Quick Start

### 1. Set up environment variables

Create a `.env` file in your project root:

```bash
# Required: API keys
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# Optional: Model configuration
DEFAULT_MODEL=google/gemini-2.5-pro
CODING_MODEL=claude-sonnet-4-5-20250929

# Optional: MCP server configuration
MCP_FILESYSTEM_ROOT=/path/to/your/data
```

### 2. Run your first query

```bash
# Ask a question
agentic-data-scientist "What is machine learning?"

# Analyze a file
agentic-data-scientist "Analyze trends in this dataset" --files data.csv

# Stream to see progress in real-time
agentic-data-scientist "Perform differential expression analysis" --files data1.csv --files data2.csv --stream
```

## Understanding the Workflow

When you submit a query, Agentic Data Scientist goes through a multi-phase workflow designed to produce high-quality, validated results.

### What Happens When You Run a Query

```
USER QUERY: "Analyze customer churn patterns in this dataset"
     |
     v
┌────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING (Iterative)                         │
├────────────────────────────────────────────────────────┤
│ 1. Plan Maker creates comprehensive analysis plan     │
│    - Breaks down task into logical stages             │
│    - Defines clear success criteria                   │
│    - Recommends appropriate methodologies             │
│                                                        │
│ 2. Plan Reviewer validates the plan                   │
│    - Checks completeness                              │
│    - Verifies all requirements are addressed          │
│    - Provides feedback if improvements needed         │
│                                                        │
│ 3. Loop repeats until plan is approved                │
│                                                        │
│ 4. Plan Parser structures it for execution            │
│    - Converts to executable stages                    │
│    - Sets up success criteria tracking                │
│                                                        │
│ RESULT: Validated, comprehensive execution plan       │
└────────────────────────────────────────────────────────┘
     |
     v
┌────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION (Stage by Stage)                   │
├────────────────────────────────────────────────────────┤
│ For each stage in the plan:                           │
│                                                        │
│ A. IMPLEMENTATION LOOP (Iterative)                    │
│    1. Coding Agent implements the stage               │
│       - Has access to 380+ scientific Skills          │
│       - Can read/write files, run code                │
│       - Creates scripts, analyses, visualizations     │
│                                                        │
│    2. Review Agent validates implementation           │
│       - Checks code quality and correctness           │
│       - Verifies stage requirements are met           │
│       - Provides specific feedback if issues found    │
│                                                        │
│    3. Loop repeats until approved                     │
│                                                        │
│ B. PROGRESS VALIDATION                                │
│    4. Criteria Checker updates progress               │
│       - Inspects generated files and results          │
│       - Updates which success criteria are now met    │
│       - Provides objective evidence                   │
│                                                        │
│ C. ADAPTIVE REPLANNING                                │
│    5. Stage Reflector adapts remaining work           │
│       - Considers what's been accomplished            │
│       - Identifies what still needs to be done        │
│       - Modifies or extends remaining stages          │
│                                                        │
│ Then proceeds to next stage...                        │
│                                                        │
│ RESULT: All stages implemented and validated          │
└────────────────────────────────────────────────────────┘
     |
     v
┌────────────────────────────────────────────────────────┐
│ PHASE 3: SUMMARY                                       │
├────────────────────────────────────────────────────────┤
│ Summary Agent creates final report                     │
│ - Synthesizes all work performed                      │
│ - Documents key findings and results                  │
│ - Lists all generated files and outputs               │
│ - Provides comprehensive analysis narrative           │
│                                                        │
│ RESULT: Publication-ready comprehensive report        │
└────────────────────────────────────────────────────────┘
```

### Key Workflow Characteristics

**Iterative Refinement**
- Plans are reviewed and refined before execution begins
- Implementations are validated before proceeding to the next stage
- Multiple opportunities to catch and fix issues early

**Adaptive Execution**
- Discoveries during implementation inform subsequent stages
- Plan adapts based on actual progress and findings
- Flexible enough to handle unexpected insights

**Continuous Validation**
- Success criteria tracked objectively throughout execution
- Clear visibility into what's been accomplished vs. what remains
- Objective evidence for each criterion's status

**Separation of Concerns**
- Planning agents focus on strategy without implementation details
- Coding agent focuses on implementation without planning burden
- Review agents provide independent validation

## Python API Usage

### Basic Usage

```python
from agentic_data_scientist import DataScientist

# Create an instance and run a query
with DataScientist() as ds:
    result = ds.run("What is data science?")
    print(result.response)
    
# Access results
print(f"Status: {result.status}")
print(f"Duration: {result.duration}s")
print(f"Files created: {result.files_created}")
```

### With File Upload

```python
from agentic_data_scientist import DataScientist

with DataScientist() as ds:
    result = ds.run(
        "Analyze trends in this time series data",
        files=[
            ("sales.csv", open("sales.csv", "rb").read()),
            ("inventory.csv", open("inventory.csv", "rb").read()),
        ]
    )
    print(result.response)
    print(f"Working directory: {ds.working_dir}")
```

### Async Usage with Streaming

```python
import asyncio
from agentic_data_scientist import DataScientist

async def analyze_data():
    async with DataScientist() as ds:
        async for event in await ds.run_async(
            "Perform differential expression analysis",
            files=[("data.csv", open("data.csv", "rb").read())],
            stream=True
        ):
            # Watch the workflow in real-time
            if event['type'] == 'message':
                author = event['author']
                content = event['content']
                print(f"[{author}] {content}")
            elif event['type'] == 'completed':
                print(f"✓ Completed in {event['duration']}s")

asyncio.run(analyze_data())
```

### Multi-turn Conversation

```python
import asyncio
from agentic_data_scientist import DataScientist

async def chat():
    async with DataScientist() as ds:
        context = {}
        
        # First turn
        result1 = await ds.run_async(
            "What are the main techniques for dimensionality reduction?",
            context=context
        )
        print("AI:", result1.response)
        
        # Second turn (maintains context)
        result2 = await ds.run_async(
            "Which one would you recommend for high-dimensional gene expression data?",
            context=context
        )
        print("AI:", result2.response)

asyncio.run(chat())
```

## Understanding Streaming Events

When using `stream=True`, you'll receive events as the workflow progresses:

```python
async for event in await ds.run_async("Your query", stream=True):
    event_type = event['type']
    
    if event_type == 'message':
        # Regular text output from agents
        print(f"[{event['author']}] {event['content']}")
        
    elif event_type == 'function_call':
        # Agent is using a tool
        print(f"Calling {event['name']}...")
        
    elif event_type == 'function_response':
        # Tool returned a result
        print(f"Tool {event['name']} completed")
        
    elif event_type == 'usage':
        # Token usage information
        tokens = event['usage']
        print(f"Tokens: {tokens['total_input_tokens']} in, {tokens['output_tokens']} out")
        
    elif event_type == 'completed':
        # Workflow finished
        print(f"Done in {event['duration']}s")
        print(f"Created {len(event['files_created'])} files")
```

## Alternative: Direct Mode

For simple tasks that don't require planning and validation, you can use direct mode:

### When to Use Direct Mode

- **Quick scripting tasks** without complex requirements
- **Straightforward code generation** where planning overhead isn't needed
- **Rapid prototyping** where you want immediate results

### When NOT to Use Direct Mode

- **Complex analyses** with multiple stages
- **Tasks requiring validation** and quality assurance
- **Data science workflows** where planning improves outcomes
- **Tasks where requirements might evolve** during execution

### Using Direct Mode

```python
from agentic_data_scientist import DataScientist

# Python API
with DataScientist(agent_type="claude_code") as ds:
    result = ds.run("Write a Python function to parse JSON files")
    print(result.response)
```

```bash
# CLI
agentic-data-scientist "Write a script to merge CSV files" --mode simple
```

**Note**: Direct mode bypasses the entire multi-agent workflow - no planning, no reviews, no validation, no adaptive replanning. Use it only when you're confident you don't need these features.

## Next Steps

- [API Reference](api_reference.md) - Detailed API documentation
- [MCP Configuration](mcp_configuration.md) - Configure tools and skills
- [Extending](extending.md) - Customize prompts and workflows
- [Examples](../examples/) - More usage examples

## Troubleshooting

### Common Issues

**ImportError: No module named 'agentic_data_scientist'**
- Install the package: `pip install agentic-data-scientist` or `uv sync`

**API Key Errors**
- Ensure your `.env` file is in the correct location
- Verify API keys are valid and active
- Check that keys have sufficient credits

**MCP Server Connection Failures**
- Ensure Node.js is installed: `node --version`
- Check that MCP servers are accessible
- Verify `MCP_FILESYSTEM_ROOT` points to a valid directory

**Workflow Seems Stuck**
- Enable streaming to see progress: `--stream` or `stream=True`
- Check logs for error messages
- Workflow may be running long computations - be patient

### Getting Help

- Check the [full documentation](../README.md)
- Review [examples](../examples/) for working code
- Open an issue on [GitHub](https://github.com/K-Dense-AI/agentic-data-scientist/issues)
