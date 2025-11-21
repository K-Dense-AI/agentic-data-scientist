# Extending Agentic Data Scientist

This guide explains how to customize and extend the Agentic Data Scientist multi-agent workflow.

## Table of Contents

- [Understanding the Agent Hierarchy](#understanding-the-agent-hierarchy)
- [Custom Prompts](#custom-prompts)
- [Custom Agents](#custom-agents)
- [Custom MCP Toolsets](#custom-mcp-toolsets)
- [Custom Event Handlers](#custom-event-handlers)
- [Integration Examples](#integration-examples)

## Understanding the Agent Hierarchy

The ADK workflow consists of multiple specialized agents organized into phases:

```
Workflow Root (SequentialAgent)
├── Planning Loop (NonEscalatingLoopAgent)
│   ├── Plan Maker (LoopDetectionAgent)
│   ├── Plan Reviewer (LoopDetectionAgent)
│   └── Review Confirmation (LoopDetectionAgent)
├── Plan Parser (LoopDetectionAgent)
├── Stage Orchestrator (Custom Agent)
│   └── For each stage:
│       ├── Implementation Loop (NonEscalatingLoopAgent)
│       │   ├── Coding Agent (ClaudeCodeAgent)
│       │   ├── Review Agent (LoopDetectionAgent)
│       │   └── Review Confirmation (LoopDetectionAgent)
│       ├── Criteria Checker (LoopDetectionAgent)
│       └── Stage Reflector (LoopDetectionAgent)
└── Summary Agent (LoopDetectionAgent)
```

### Key Agent Types

**LoopDetectionAgent**: Extends ADK's LlmAgent with loop detection to prevent infinite generation
**ClaudeCodeAgent**: Wraps Claude Code SDK for implementation with tool access
**NonEscalatingLoopAgent**: Manages iteration without propagating escalation flags upward
**StageOrchestratorAgent**: Custom orchestrator managing stage-by-stage execution

## Custom Prompts

Each agent in the workflow is driven by a prompt template. You can customize these to change agent behavior.

### Prompt Structure

Prompts are stored in `src/agentic_data_scientist/prompts/`:

```
prompts/
├── base/
│   ├── plan_maker.md               # Creates analysis plans
│   ├── plan_reviewer.md            # Reviews plans for completeness
│   ├── plan_review_confirmation.md # Decides if plan is approved
│   ├── plan_parser.md              # Structures plan into stages
│   ├── coding_review.md            # Reviews implementations
│   ├── implementation_review_confirmation.md  # Decides if implementation is approved
│   ├── criteria_checker.md         # Checks success criteria
│   ├── stage_reflector.md          # Adapts remaining stages
│   ├── summary.md                  # Generates final report
│   └── global_preamble.md          # Shared context for all agents
└── domain/
    └── bioinformatics/             # Domain-specific customizations
        ├── science_methodology.md
        └── interactive_base.md
```

### Loading Custom Prompts

```python
from agentic_data_scientist.prompts import load_prompt

# Load a base prompt
plan_maker_prompt = load_prompt("plan_maker")

# Load a domain-specific prompt
bio_prompt = load_prompt("science_methodology", domain="bioinformatics")
```

### Creating Custom Prompts

1. **Create a new prompt file** in `prompts/base/` or `prompts/domain/your_domain/`

Example: `prompts/base/custom_plan_maker.md`

```markdown
$global_preamble

You are a specialized planning agent for [your domain].

# Your Role

Create detailed analysis plans for [specific task type].

# Output Format

Provide structured plans containing:
1. **Analysis Stages** - Step-by-step breakdown
2. **Success Criteria** - How to verify completion
3. **Recommended Approaches** - Domain-specific methods

# Domain Knowledge

[Include specific expertise, methodologies, or considerations]

# Context

**User Request:**
{original_user_input?}
```

2. **Use the custom prompt** by loading it:

```python
from agentic_data_scientist.prompts import load_prompt

custom_prompt = load_prompt("custom_plan_maker")
```

### Customizing Specific Agent Prompts

To customize a specific agent's behavior, modify its prompt:

**Example: Customize Plan Maker for Financial Analysis**

Create `prompts/domain/finance/plan_maker.md`:

```markdown
$global_preamble

You are a financial data science strategist specializing in quantitative analysis.

# Your Role

Transform financial analysis requests into comprehensive, risk-aware plans.

# Financial Analysis Stages

Focus on:
1. Data quality and compliance verification
2. Risk assessment and statistical validation  
3. Regulatory compliance checks
4. Backtesting and validation strategies

# Success Criteria Requirements

Every plan must include:
- Data quality thresholds
- Statistical significance requirements
- Risk metrics and controls
- Audit trail requirements

[... rest of customized prompt ...]
```

Then load it:

```python
financial_prompt = load_prompt("plan_maker", domain="finance")
```

**Note**: Models are configured via environment variables (`OPENROUTER_API_KEY`, `DEFAULT_MODEL`) and routed through OpenRouter.

### Prompt Variables

Prompts can include dynamic variables that are interpolated at runtime:

- `{original_user_input?}`: The user's query
- `{high_level_plan?}`: The current plan
- `{high_level_stages?}`: List of stages
- `{high_level_success_criteria?}`: Success criteria
- `{stage_implementations?}`: Completed stage summaries
- `{current_stage?}`: Current stage being implemented
- `{implementation_summary?}`: Implementation output
- `{review_feedback?}`: Review agent feedback

## Custom Agents

### Extending Existing Agents

You can customize existing agent roles by creating modified versions:

```python
from google.adk.agents import LlmAgent
from google.genai import types
from agentic_data_scientist.agents.adk.loop_detection import LoopDetectionAgent
from agentic_data_scientist.agents.adk.utils import DEFAULT_MODEL, get_generate_content_config
from agentic_data_scientist.prompts import load_prompt

def create_custom_plan_maker(tools):
    """Create a custom plan maker with specialized behavior."""
    
    # Load custom prompt
    custom_instructions = load_prompt("custom_plan_maker", domain="finance")
    
    # DEFAULT_MODEL is a LiteLLM model instance configured to use OpenRouter
    return LoopDetectionAgent(
        name="custom_plan_maker",
        model=DEFAULT_MODEL,  # Automatically routed through OpenRouter
        description="Custom financial planning agent",
        instruction=custom_instructions,
        tools=tools,
        output_key="high_level_plan",
        generate_content_config=get_generate_content_config(temperature=0.4),
        # Custom loop detection thresholds
        min_pattern_length=300,
        repetition_threshold=4,
    )
```

### Creating New Agent Roles

You can add entirely new agents to the workflow:

```python
from google.adk.agents import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator

class ValidationAgent(LoopDetectionAgent):
    """Custom validation agent for specific checks."""
    
    def __init__(self, validation_rules, **kwargs):
        super().__init__(**kwargs)
        self.validation_rules = validation_rules
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Custom validation logic."""
        state = ctx.session.state
        
        # Get implementation results
        implementation = state.get("implementation_summary", "")
        
        # Apply custom validation rules
        validation_results = []
        for rule_name, rule_fn in self.validation_rules.items():
            passed = rule_fn(implementation)
            validation_results.append({
                'rule': rule_name,
                'passed': passed
            })
        
        # Store results
        state["validation_results"] = validation_results
        
        # Yield results as event
        summary = f"Validation: {sum(r['passed'] for r in validation_results)}/{len(validation_results)} checks passed"
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=summary)]
            ),
        )
```

### Modifying the Workflow

To integrate custom agents into the workflow, you'll need to modify the agent factory:

```python
from agentic_data_scientist.agents.adk.agent import create_agent
import logging

logger = logging.getLogger(__name__)

def create_custom_workflow(working_dir, mcp_servers=None):
    """Create workflow with custom agents."""
    
    # Get standard agents
    from agentic_data_scientist.agents.adk.agent import (
        create_agent as base_create_agent
    )
    
    # Create base workflow
    workflow = base_create_agent(working_dir, mcp_servers)
    
    # Or build custom workflow from scratch
    from google.adk.agents import SequentialAgent
    
    custom_workflow = SequentialAgent(
        name="custom_workflow",
        description="Workflow with custom agents",
        sub_agents=[
            # Your custom agent composition
        ]
    )
    
    return custom_workflow
```

## Custom Tools

Tools provide functionality to agents. You can create custom tools by defining simple Python functions.

### Creating Custom Tools

Custom tools are regular Python functions that follow a simple signature pattern:

```python
from functools import partial
from pathlib import Path

def custom_data_analysis(
    query: str,
    working_dir: str,
) -> str:
    """
    Perform custom data analysis.
    
    Parameters
    ----------
    query : str
        Analysis query
    working_dir : str
        Working directory for security validation
        
    Returns
    -------
    str
        Analysis results or error message
    """
    try:
        # Your custom logic here
        # Validate paths against working_dir for security
        work_path = Path(working_dir).resolve()
        
        # Perform analysis
        result = f"Analysis for: {query}"
        return result
    except Exception as e:
        return f"Error: {e}"

def fetch_custom_api(endpoint: str, timeout: int = 30) -> str:
    """
    Fetch data from a custom API.
    
    Parameters
    ----------
    endpoint : str
        API endpoint path
    timeout : int, optional
        Request timeout in seconds
        
    Returns
    -------
    str
        API response or error message
    """
    import requests
    
    try:
        base_url = "https://api.example.com"
        response = requests.get(f"{base_url}/{endpoint}", timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {e}"
```

### Adding Custom Tools to Agents

Modify the agent creation to include your custom tools:

```python
from functools import partial
from agentic_data_scientist.agents.adk.agent import create_agent
from agentic_data_scientist.tools import (
    read_file,
    list_directory,
    fetch_url,
)

def create_agent_with_custom_tools(working_dir: str):
    """Create agent with custom tools."""
    
    # Import your custom tools
    from my_tools import custom_data_analysis, fetch_custom_api
    
    # Create tools list with working_dir bound
    tools = [
        # Standard file tools
        partial(read_file, working_dir=working_dir),
        partial(list_directory, working_dir=working_dir),
        
        # Custom tools
        partial(custom_data_analysis, working_dir=working_dir),
        
        # Web tools (no working_dir needed)
        fetch_url,
        fetch_custom_api,
    ]
    
    # Create agent with custom tools
    # Note: You'll need to modify agent.py to accept tools parameter
    # or directly instantiate agents with your tools list
    return tools
```

### Tool Design Best Practices

1. **Return String Results**: Tools should return string results or error messages for compatibility with ADK
2. **Include Security Parameters**: File operation tools should include `working_dir` parameter
3. **Handle Errors Gracefully**: Return error messages as strings instead of raising exceptions
4. **Use Type Hints**: Include type hints for all parameters and return values
5. **Write Docstrings**: Use NumPy-style docstrings for documentation
6. **Keep It Simple**: Each tool should do one thing well

### Example: Custom Database Tool

```python
from functools import partial
import sqlite3
from pathlib import Path

def query_database(
    query: str,
    working_dir: str,
    db_name: str = "data.db",
) -> str:
    """
    Execute a read-only SQL query on a database.
    
    Parameters
    ----------
    query : str
        SQL query (SELECT only)
    working_dir : str
        Working directory containing the database
    db_name : str, optional
        Database filename, default "data.db"
        
    Returns
    -------
    str
        Query results as formatted string
    """
    try:
        # Security: Validate database is in working_dir
        work_path = Path(working_dir).resolve()
        db_path = (work_path / db_name).resolve()
        
        if not db_path.is_relative_to(work_path):
            return f"Error: Database must be in working directory"
        
        # Security: Only allow SELECT queries
        if not query.strip().upper().startswith("SELECT"):
            return "Error: Only SELECT queries allowed"
        
        # Execute query
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        # Format results
        if not results:
            return "No results found"
        
        # Simple formatting
        return "\n".join(str(row) for row in results)
        
    except Exception as e:
        return f"Error executing query: {e}"

# Usage in agent configuration
tools = [
    partial(query_database, working_dir="/path/to/session"),
]
```

## Custom Event Handlers

### Processing Streaming Events

Create custom handlers to process workflow events:

```python
async def custom_event_processor(ds, query):
    """Custom event processing with metrics."""
    
    metrics = {
        'plan_iterations': 0,
        'implementation_iterations': 0,
        'stages_completed': 0,
        'tools_used': set(),
    }
    
    async for event in await ds.run_async(query, stream=True):
        event_type = event.get('type')
        author = event.get('author', '')
        
        # Track metrics
        if 'plan_maker' in author:
            metrics['plan_iterations'] += 1
        elif 'coding_agent' in author:
            metrics['implementation_iterations'] += 1
        elif 'Stage' in event.get('content', ''):
            metrics['stages_completed'] += 1
        
        if event_type == 'function_call':
            metrics['tools_used'].add(event['name'])
        
        # Custom handling
        if event_type == 'message':
            # Filter or transform messages
            content = event['content']
            if 'ERROR' in content:
                logger.error(f"Error in {author}: {content}")
        
        elif event_type == 'completed':
            # Log metrics
            logger.info(f"Workflow Metrics: {metrics}")
            print(f"\n📊 Workflow completed with:")
            print(f"  - {metrics['plan_iterations']} planning iterations")
            print(f"  - {metrics['implementation_iterations']} implementation iterations")
            print(f"  - {metrics['stages_completed']} stages completed")
            print(f"  - {len(metrics['tools_used'])} unique tools used")
```

### Custom Event Transformations

Transform events before processing:

```python
from agentic_data_scientist.core.events import event_to_dict

def transform_event(event):
    """Add custom fields to events."""
    event_dict = event_to_dict(event)
    
    # Add custom metadata
    event_dict['processed_at'] = time.time()
    event_dict['workflow_phase'] = detect_phase(event_dict['author'])
    
    # Enhance with additional info
    if event_dict['type'] == 'message':
        event_dict['word_count'] = len(event_dict['content'].split())
    
    return event_dict

def detect_phase(author):
    """Detect which workflow phase an event belongs to."""
    if 'plan_maker' in author or 'plan_reviewer' in author:
        return 'planning'
    elif 'stage_orchestrator' in author or 'coding_agent' in author:
        return 'execution'
    elif 'summary' in author:
        return 'summary'
    return 'unknown'
```

## Integration Examples

### Integrating with FastAPI

```python
from fastapi import FastAPI, WebSocket, HTTPException
from agentic_data_scientist import DataScientist
import asyncio
import json

app = FastAPI()

@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analysis."""
    await websocket.accept()
    
    try:
        # Receive request
        data = await websocket.receive_json()
        query = data.get('query')
        files = data.get('files', [])
        
        # Run workflow with streaming
        async with DataScientist() as ds:
            async for event in await ds.run_async(
                query,
                files=[(f['name'], f['content']) for f in files],
                stream=True
            ):
                # Send events to client
                await websocket.send_json(event)
                
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'content': str(e)
        })
    finally:
        await websocket.close()

@app.post("/api/analyze")
async def analyze_endpoint(query: str, files: list = None):
    """REST endpoint for analysis."""
    async with DataScientist() as ds:
        result = await ds.run_async(query, files=files)
        
        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            'response': result.response,
            'files_created': result.files_created,
            'duration': result.duration
        }
```

### Integrating with Jupyter Notebooks

```python
from agentic_data_scientist import DataScientist
from IPython.display import display, Markdown, HTML
import asyncio

async def notebook_analysis(query, files=None):
    """Run analysis in Jupyter with rich formatting."""
    display(Markdown(f"## Analysis Request\n\n{query}"))
    
    async with DataScientist() as ds:
        display(Markdown("### Workflow Progress"))
        
        current_phase = None
        async for event in await ds.run_async(
            query,
            files=files,
            stream=True
        ):
            author = event.get('author', '')
            
            # Track phase changes
            if 'plan_maker' in author and current_phase != 'Planning':
                current_phase = 'Planning'
                display(Markdown(f"**Phase: {current_phase}**"))
            elif 'coding_agent' in author and current_phase != 'Execution':
                current_phase = 'Execution'
                display(Markdown(f"**Phase: {current_phase}**"))
            elif 'summary' in author and current_phase != 'Summary':
                current_phase = 'Summary'
                display(Markdown(f"**Phase: {current_phase}**"))
            
            if event['type'] == 'message':
                content = event['content']
                # Display formatted messages
                if len(content) < 200:
                    display(Markdown(f"*{author}*: {content}"))
                    
            elif event['type'] == 'completed':
                files = event['files_created']
                display(Markdown(f"### Results\n\n**Files Created:**"))
                for f in files:
                    display(Markdown(f"- `{f}`"))

# Usage in notebook
await notebook_analysis("Analyze customer churn", files=[('data.csv', data)])
```

### Custom Session Management

```python
from agentic_data_scientist import DataScientist
import json
from pathlib import Path

class PersistentDataScientist:
    """DataScientist with session persistence."""
    
    def __init__(self, session_dir="./sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.ds = None
        self.session_id = None
    
    async def start_session(self, session_id=None):
        """Start or resume a session."""
        self.ds = DataScientist()
        await self.ds.__aenter__()
        
        if session_id:
            # Resume existing session
            self.session_id = session_id
            context = self.load_context(session_id)
        else:
            # New session
            self.session_id = self.ds.session_id
            context = {}
        
        return context
    
    def load_context(self, session_id):
        """Load session context."""
        context_file = self.session_dir / f"{session_id}.json"
        if context_file.exists():
            with open(context_file) as f:
                return json.load(f)
        return {}
    
    def save_context(self, context):
        """Save session context."""
        context_file = self.session_dir / f"{self.session_id}.json"
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)
    
    async def run(self, query, context=None):
        """Run query with persistent context."""
        if context is None:
            context = self.load_context(self.session_id)
        
        result = await self.ds.run_async(query, context=context)
        self.save_context(context)
        
        return result
    
    async def close(self):
        """Close session."""
        if self.ds:
            await self.ds.__aexit__(None, None, None)

# Usage
pds = PersistentDataScientist()
context = await pds.start_session()

# Run queries
result1 = await pds.run("Analyze this dataset", context)
result2 = await pds.run("What are the key trends?", context)

await pds.close()
```

## Environment Configuration

When extending the system, be aware of these environment variables:

**Required:**
- `OPENROUTER_API_KEY`: For ADK agents using DEFAULT_MODEL
- `ANTHROPIC_API_KEY`: For Claude Code agent

**Optional:**
- `DEFAULT_MODEL`: Model for planning/review (default: `google/gemini-2.5-pro`)
- `REVIEW_MODEL`: Model for review agents (default: same as DEFAULT_MODEL)
- `CODING_MODEL`: Model for coding agent (default: `claude-sonnet-4-5-20250929`)

Models with provider prefixes (e.g., `google/`, `anthropic/`) are automatically routed through OpenRouter via LiteLLM.

## Best Practices

1. **Test Custom Prompts Thoroughly**: Validate prompt changes with diverse queries
2. **Use Type Hints**: Always include type hints in custom code
3. **Handle Errors**: Implement proper error handling in custom agents
4. **Document Customizations**: Add docstrings explaining custom behavior
5. **Keep Prompts Modular**: Break complex prompts into reusable components
6. **Version Control Prompts**: Track prompt changes like code
7. **Monitor Agent Behavior**: Log and analyze agent outputs during development
8. **Model Configuration**: Use environment variables for model configuration rather than hardcoding

## See Also

See the `docs/` folder for additional guides on getting started, API reference, CLI usage, tools configuration, and technical architecture.
