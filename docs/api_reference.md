# API Reference

Complete API reference for Agentic Data Scientist.

## Core API

### `DataScientist`

Main class for interacting with Agentic Data Scientist agents.

```python
from agentic_data_scientist import DataScientist

ds = DataScientist(
    agent_type="adk",           # "adk" or "claude_code"
    model=None,                  # Optional: specific model to use
    mcp_servers=None,           # Optional: list of MCP servers
)
```

#### Parameters

- **agent_type** (str, default="adk"): Type of agent to use
  - `"adk"`: Multi-agent system with planning, orchestration, and Claude Code implementation
  - `"claude_code"`: Direct Claude Code agent for coding tasks
  
- **model** (str, optional): Specific model to use. Defaults:
  - ADK: `google/gemini-2.5-pro`
  - Claude Code: `claude-sonnet-4-5-20250929`
  
- **mcp_servers** (list, optional): List of MCP servers to enable (ADK only)

#### Attributes

- **session_id** (str): Unique session identifier
- **working_dir** (Path): Temporary working directory for the session
- **config** (SessionConfig): Session configuration

#### Methods

##### `run(message, files=None, **kwargs) -> Result`

Synchronous method to run a query.

**Parameters:**
- **message** (str): The user's query or instruction
- **files** (list[tuple], optional): List of (filename, content) tuples
- **kwargs**: Additional arguments

**Returns:**
- Result object with response, files_created, duration, etc.

**Example:**
```python
with DataScientist() as ds:
    result = ds.run("What is Python?")
    print(result.response)
    print(result.status)  # "completed" or "error"
```

##### `run_async(message, files=None, stream=False, context=None) -> Union[Result, AsyncGenerator]`

Asynchronous method to run a query.

**Parameters:**
- **message** (str): The user's query or instruction
- **files** (list[tuple], optional): List of (filename, content) tuples
- **stream** (bool, default=False): If True, returns an async generator for streaming
- **context** (dict, optional): Conversation context for multi-turn interactions

**Returns:**
- If stream=False: Result object
- If stream=True: AsyncGenerator yielding event dictionaries

**Example:**
```python
import asyncio

async def main():
    async with DataScientist() as ds:
        result = await ds.run_async("Explain quantum computing")
        print(result.response)

asyncio.run(main())
```

**Streaming Example:**
```python
async def stream_example():
    async with DataScientist() as ds:
        async for event in await ds.run_async("Complex task", stream=True):
            if event['type'] == 'message':
                print(event['content'])

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
    model="google/gemini-2.5-pro",
    mcp_servers=["filesystem", "fetch"],
    max_llm_calls=1024,
    session_id=None,
    working_dir=None,
)
```

#### Attributes

- **agent_type** (str): "adk" or "claude_code"
- **model** (str, optional): Model to use
- **mcp_servers** (list, optional): List of MCP servers
- **max_llm_calls** (int): Maximum LLM calls per session
- **session_id** (str, optional): Custom session ID
- **working_dir** (str, optional): Custom working directory

### `Result`

Result from running an agent.

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

When using streaming mode, events are emitted as dictionaries.

### Event Types

#### MessageEvent

```python
{
    'type': 'message',
    'content': 'Text content',
    'author': 'agent_name',
    'timestamp': '12:34:56.789',
    'is_thought': False,
    'is_partial': False,
    'event_number': 1
}
```

#### FunctionCallEvent

```python
{
    'type': 'function_call',
    'name': 'tool_name',
    'arguments': {'arg1': 'value1'},
    'author': 'agent_name',
    'timestamp': '12:34:56.789',
    'event_number': 2
}
```

#### FunctionResponseEvent

```python
{
    'type': 'function_response',
    'name': 'tool_name',
    'response': {'result': 'success'},
    'author': 'agent_name',
    'timestamp': '12:34:56.789',
    'event_number': 3
}
```

#### UsageEvent

```python
{
    'type': 'usage',
    'usage': {
        'total_input_tokens': 100,
        'cached_input_tokens': 20,
        'output_tokens': 50
    },
    'timestamp': '12:34:56.789'
}
```

#### ErrorEvent

```python
{
    'type': 'error',
    'content': 'Error message',
    'timestamp': '12:34:56.789'
}
```

#### CompletedEvent

```python
{
    'type': 'completed',
    'session_id': 'session_123',
    'duration': 1.5,
    'total_events': 10,
    'files_created': ['output.txt'],
    'files_count': 1,
    'timestamp': '12:34:56.789'
}
```

## CLI Reference

### Basic Usage

```bash
agentic-data-scientist [OPTIONS] QUERY
```

### Options

- **--mode**: Execution mode, default: `orchestrated`
  - `orchestrated`: Full multi-agent system with planning and verification
  - `simple`: Direct Claude Code execution
- **--files, -f**: Files to upload (can be specified multiple times)
- **--stream**: Enable streaming output
- **--verbose, -v**: Enable verbose logging
- **--help**: Show help message

### Examples

```bash
# Simple query (orchestrated mode by default)
agentic-data-scientist "What is Python?"

# With file upload
agentic-data-scientist "Analyze this data" --files data.csv

# Use simple mode (direct Claude Code)
agentic-data-scientist "Write a script" --mode simple

# Stream output
agentic-data-scientist "Complex task" --stream

# Verbose logging
agentic-data-scientist "Debug this" --verbose
```

## Environment Variables

### Required

- **ANTHROPIC_API_KEY**: Anthropic API key for Claude Code agent
- **GOOGLE_API_KEY**: Google API key for ADK agents (optional)

### Optional

- **DEFAULT_MODEL**: Default model for ADK agents (default: `google/gemini-2.5-pro`)
- **CODING_MODEL**: Model for Claude Code agent (default: `claude-sonnet-4-5-20250929`)
- **MCP_FILESYSTEM_ROOT**: Root directory for filesystem MCP (default: `/tmp`)
- **CLAUDE_SCIENTIFIC_SKILLS_URL**: URL for claude-scientific-skills MCP (default: `https://mcp.k-dense.ai/claude-scientific-skills/mcp`)

## Error Handling

```python
from agentic_data_scientist import DataScientist

with DataScientist() as ds:
    result = ds.run("Query")
    
    if result.status == "error":
        print(f"Error occurred: {result.error}")
    else:
        print(f"Success: {result.response}")
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

3. **Use streaming for long tasks**:
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

## See Also

- [Getting Started Guide](getting_started.md)
- [MCP Configuration](mcp_configuration.md)
- [Extending Guide](extending.md)

