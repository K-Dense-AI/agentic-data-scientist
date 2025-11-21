# API Reference

Complete API reference for Agentic Data Scientist.

## Core API

### `DataScientist`

Main class for interacting with the Agentic Data Scientist multi-agent workflow.

```python
from agentic_data_scientist import DataScientist

ds = DataScientist(
    agent_type="adk",           # "adk" (recommended) or "claude_code" (direct mode)
    mcp_servers=None,           # Optional: list of MCP servers
)
```

#### Parameters

- **agent_type** (str, default="adk"): Type of agent to use
  - `"adk"`: **(Recommended)** Full multi-agent workflow with planning, validation, and adaptive execution
  - `"claude_code"`: Direct mode - bypasses workflow for simple scripting tasks
  
- **mcp_servers** (list, optional): List of MCP servers to enable (currently not used; see tools_configuration.md)

**Note**: The multi-agent ADK workflow (`agent_type="adk"`) is the primary mode and recommended for most use cases. Direct mode is only for simple tasks that don't benefit from planning and validation.

**Model Configuration**: Models are configured via environment variables and routed through OpenRouter:
  - ADK agents: `DEFAULT_MODEL` (default: `google/gemini-2.5-pro`)
  - Coding agent: `CODING_MODEL` (default: `claude-sonnet-4-5-20250929`)
  - Models with provider prefixes (e.g., `google/`, `anthropic/`) are automatically routed through OpenRouter

#### Attributes

- **session_id** (str): Unique session identifier
- **working_dir** (Path): Temporary working directory for the session
- **config** (SessionConfig): Session configuration

#### Methods

##### `run(message, files=None, **kwargs) -> Result`

Synchronous method to run a query through the workflow.

**Parameters:**
- **message** (str): The user's query or instruction
- **files** (list[tuple], optional): List of (filename, content) tuples
- **kwargs**: Additional arguments

**Returns:**
- Result object with response, files_created, duration, etc.

**Example:**
```python
with DataScientist() as ds:
    result = ds.run("Analyze trends in this data", files=[("data.csv", data)])
    print(result.response)
    print(f"Status: {result.status}")  # "completed" or "error"
```

##### `run_async(message, files=None, stream=False, context=None) -> Union[Result, AsyncGenerator]`

Asynchronous method to run a query through the workflow.

**Parameters:**
- **message** (str): The user's query or instruction
- **files** (list[tuple], optional): List of (filename, content) tuples
- **stream** (bool, default=False): If True, returns an async generator for streaming events
- **context** (dict, optional): Conversation context for multi-turn interactions

**Returns:**
- If stream=False: Result object
- If stream=True: AsyncGenerator yielding event dictionaries

**Example (non-streaming):**
```python
import asyncio

async def main():
    async with DataScientist() as ds:
        result = await ds.run_async("Explain gradient boosting")
        print(result.response)

asyncio.run(main())
```

**Example (streaming):**
```python
async def stream_example():
    async with DataScientist() as ds:
        async for event in await ds.run_async(
            "Analyze this dataset",
            files=[("data.csv", data)],
            stream=True
        ):
            if event['type'] == 'message':
                print(f"[{event['author']}] {event['content']}")

asyncio.run(stream_example())
```

##### `save_files(files) -> List[FileInfo]`

Save files to the working directory.

**Parameters:**
- **files** (list[tuple]): List of (filename, content) tuples

**Returns:**
- List of FileInfo objects with name, path, and size

##### `prepare_prompt(message, file_info=None) -> str`

Prepare a prompt with optional file information.

**Parameters:**
- **message** (str): User's message
- **file_info** (list[FileInfo], optional): List of uploaded files

**Returns:**
- Complete prompt string

##### `cleanup()`

Clean up temporary working directory.

## Data Classes

### `SessionConfig`

Configuration for an agent session.

```python
from agentic_data_scientist.core.api import SessionConfig

config = SessionConfig(
    agent_type="adk",
    mcp_servers=["filesystem", "fetch"],
    max_llm_calls=1024,
    session_id=None,
    working_dir=None,
)
```

#### Attributes

- **agent_type** (str): "adk" or "claude_code"
- **mcp_servers** (list, optional): List of MCP servers (currently not used)
- **max_llm_calls** (int): Maximum LLM calls per session
- **session_id** (str, optional): Custom session ID
- **working_dir** (str, optional): Custom working directory
- **auto_cleanup** (bool): Whether to cleanup working directory after completion

**Note**: Models are configured via environment variables (OPENROUTER_API_KEY, DEFAULT_MODEL, CODING_MODEL), not in the SessionConfig.

### `Result`

Result from running the workflow.

```python
result = ds.run("Query")

# Access result attributes
print(result.session_id)       # Session ID
print(result.status)           # "completed" or "error"
print(result.response)         # Agent's response text
print(result.error)            # Error message (if status="error")
print(result.files_created)    # List of created files
print(result.duration)         # Execution time in seconds
print(result.events_count)     # Number of events processed
```

### `FileInfo`

Information about an uploaded file.

```python
file_info = FileInfo(
    name="data.csv",
    path="/path/to/data.csv",
    size_kb=10.5
)
```

## Event System

When using streaming mode (`stream=True`), the workflow emits events as it progresses.

### Workflow Event Flow

For the ADK multi-agent workflow, you'll see events in roughly this order:

```
Planning Phase:
  plan_maker_agent → plan_reviewer_agent → plan_review_confirmation_agent →
  high_level_plan_parser

Execution Phase (repeated for each stage):
  stage_orchestrator → coding_agent → review_agent →
  implementation_review_confirmation_agent → success_criteria_checker →
  stage_reflector

Summary Phase:
  summary_agent
```

### Event Types

#### MessageEvent

Regular text output from agents.

```python
{
    'type': 'message',
    'content': 'Text content',
    'author': 'plan_maker_agent',  # Which agent produced this
    'timestamp': '12:34:56.789',
    'is_thought': False,             # Internal reasoning vs. output
    'is_partial': False,             # Streaming chunk vs. complete
    'event_number': 1
}
```

**Common Authors in Workflow:**
- `plan_maker_agent`: Creating the analysis plan
- `plan_reviewer_agent`: Reviewing the plan
- `plan_review_confirmation_agent`: Deciding if plan is approved
- `high_level_plan_parser`: Structuring the plan
- `stage_orchestrator`: Managing stage execution
- `coding_agent`: Implementing each stage
- `review_agent`: Reviewing implementation
- `implementation_review_confirmation_agent`: Deciding if implementation is approved
- `success_criteria_checker`: Updating progress
- `stage_reflector`: Adapting remaining stages
- `summary_agent`: Creating final report

#### FunctionCallEvent

Agent is using a tool.

```python
{
    'type': 'function_call',
    'name': 'read_file',
    'arguments': {'path': 'data.csv'},
    'author': 'review_agent',
    'timestamp': '12:34:56.789',
    'event_number': 2
}
```

#### FunctionResponseEvent

Tool returned a result.

```python
{
    'type': 'function_response',
    'name': 'read_file',
    'response': {'content': '...file contents...'},
    'author': 'review_agent',
    'timestamp': '12:34:56.789',
    'event_number': 3
}
```

#### UsageEvent

Token usage information.

```python
{
    'type': 'usage',
    'usage': {
        'total_input_tokens': 1500,
        'cached_input_tokens': 200,
        'output_tokens': 500
    },
    'timestamp': '12:34:56.789'
}
```

#### ErrorEvent

An error occurred during execution.

```python
{
    'type': 'error',
    'content': 'Error message describing what went wrong',
    'timestamp': '12:34:56.789'
}
```

#### CompletedEvent

Workflow finished successfully.

```python
{
    'type': 'completed',
    'session_id': 'session_123',
    'duration': 45.2,
    'total_events': 150,
    'files_created': ['results.csv', 'plot.png', 'summary.md'],
    'files_count': 3,
    'timestamp': '12:34:56.789'
}
```

### Workflow-Specific Events

#### Stage Transition Events

When the orchestrator moves between stages:

```python
{
    'type': 'message',
    'author': 'stage_orchestrator',
    'content': '### Stage 2: Data Preprocessing\n\nBeginning implementation...',
    # ...
}
```

#### Criteria Update Events

After the criteria checker runs:

```python
{
    'type': 'message',
    'author': 'success_criteria_checker',
    'content': '{...JSON with criteria updates...}',
    # The checker outputs structured JSON
}
```

#### Planning Loop Events

During iterative plan refinement:

```python
# Plan created
{'author': 'plan_maker_agent', 'content': '### Analysis Stages:\n1. ...'}

# Review feedback
{'author': 'plan_reviewer_agent', 'content': 'This plan looks good...'}

# Decision
{'author': 'plan_review_confirmation_agent', 'content': '{"exit": true, "reason": "..."}'}
```

### Example: Processing Events

```python
async def process_workflow_events(ds, query):
    """Track workflow progress through events."""
    
    current_phase = None
    current_stage = None
    
    async for event in await ds.run_async(query, stream=True):
        event_type = event.get('type')
        author = event.get('author', '')
        
        # Track workflow phase
        if 'plan_maker' in author:
            if current_phase != 'planning':
                current_phase = 'planning'
                print("\n=== PLANNING PHASE ===")
        elif 'stage_orchestrator' in author:
            if current_phase != 'execution':
                current_phase = 'execution'
                print("\n=== EXECUTION PHASE ===")
        elif 'summary' in author:
            if current_phase != 'summary':
                current_phase = 'summary'
                print("\n=== SUMMARY PHASE ===")
        
        # Handle different event types
        if event_type == 'message':
            content = event['content']
            
            # Track stage transitions
            if 'Stage' in content and 'Beginning implementation' in content:
                print(f"\n→ Starting new stage")
            
            print(f"[{author}] {content[:100]}...")
            
        elif event_type == 'function_call':
            tool_name = event['name']
            print(f"  → Using tool: {tool_name}")
            
        elif event_type == 'usage':
            usage = event['usage']
            print(f"  📊 Tokens: {usage.get('total_input_tokens', 0)} in, "
                  f"{usage.get('output_tokens', 0)} out")
            
        elif event_type == 'error':
            error_msg = event['content']
            print(f"  ❌ Error: {error_msg}")
            
        elif event_type == 'completed':
            duration = event['duration']
            files = event['files_created']
            print(f"\n✓ Completed in {duration:.1f}s")
            print(f"✓ Created {len(files)} files: {', '.join(files)}")
```

## CLI Usage

For complete CLI documentation including all options, working directory behavior, and extensive examples, see `cli_reference.md`.

## Environment Variables

### Required

- **ANTHROPIC_API_KEY**: Anthropic API key for Claude (coding agent)
- **OPENROUTER_API_KEY**: OpenRouter API key for planning/review agents

### Optional

- **DEFAULT_MODEL**: Model for planning and review agents (default: `google/gemini-2.5-pro`, routed through OpenRouter)
- **REVIEW_MODEL**: Model for review agents (default: same as DEFAULT_MODEL)
- **CODING_MODEL**: Model for coding agent (default: `claude-sonnet-4-5-20250929`)
- **OPENROUTER_API_BASE**: OpenRouter API base URL (default: `https://openrouter.ai/api/v1`)
- **OR_SITE_URL**: Site URL for OpenRouter (default: `k-dense.ai`)
- **OR_APP_NAME**: App name for OpenRouter (default: `Agentic Data Scientist`)

## Error Handling

```python
from agentic_data_scientist import DataScientist

with DataScientist() as ds:
    result = ds.run("Query")
    
    if result.status == "error":
        print(f"Error occurred: {result.error}")
        # Handle error appropriately
    else:
        print(f"Success: {result.response}")
        print(f"Created files: {result.files_created}")
```

## Best Practices

1. **Use context managers** to ensure cleanup:
   ```python
   with DataScientist() as ds:
       # Your code here
   ```

2. **Handle errors gracefully**:
   ```python
   result = ds.run("Query")
   if result.status != "error":
       # Process result
   ```

3. **Use streaming for long tasks** to monitor progress:
   ```python
   async for event in await ds.run_async("Task", stream=True):
       # Process events in real-time
   ```

4. **Provide context for multi-turn conversations**:
   ```python
   context = {}
   result1 = await ds.run_async("First query", context=context)
   result2 = await ds.run_async("Follow-up", context=context)
   ```

5. **Use ADK workflow for complex tasks**:
   ```python
   # Recommended for most use cases
   with DataScientist(agent_type="adk") as ds:
       result = ds.run("Complex analysis task")
   ```

6. **Reserve direct mode for simple tasks**:
   ```python
   # Only for straightforward scripting
   with DataScientist(agent_type="claude_code") as ds:
       result = ds.run("Write a simple function")
   ```

## See Also

See the `docs/` folder for additional guides on getting started, CLI usage, customization, and technical architecture.
