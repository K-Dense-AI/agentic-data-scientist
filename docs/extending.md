# Extending Agentic Data Scientist

This guide explains how to customize and extend Agentic Data Scientist for your specific needs.

## Table of Contents

- [Custom Prompts](#custom-prompts)
- [Custom Agents](#custom-agents)
- [Custom MCP Toolsets](#custom-mcp-toolsets)
- [Custom Event Handlers](#custom-event-handlers)
- [Integration Examples](#integration-examples)

## Custom Prompts

Agentic Data Scientist uses prompt templates for different agent roles. You can customize these prompts.

### Prompt Structure

Prompts are stored in `src/agentic_data_scientist/prompts/`:
```
prompts/
├── base/
│   ├── agent_base.md          # Root agent instructions
│   ├── plan_generator.md      # Planning phase
│   ├── plan_orchestrator.md   # Orchestration
│   ├── plan_verifier.md       # Verification
│   ├── coding_base.md         # Coding instructions (deprecated)
│   ├── coding_review.md       # Review instructions
│   └── summary.md             # Summary generation
└── domain/
    └── bioinformatics/         # Domain-specific prompts
        ├── science_methodology.md
        └── interactive_base.md
```

### Loading Custom Prompts

```python
from agentic_data_scientist.prompts import load_prompt

# Load a base prompt
agent_prompt = load_prompt("agent_base")

# Load a domain-specific prompt
bio_prompt = load_prompt("science_methodology", domain="bioinformatics")
```

### Creating Custom Prompts

1. Create a new markdown file in `prompts/base/` or `prompts/domain/your_domain/`
2. Write your prompt instructions
3. Load it using `load_prompt()`

Example custom prompt (`prompts/base/my_custom_agent.md`):
```markdown
# My Custom Agent

You are a specialized agent for [specific task].

## Guidelines

1. Always follow [specific methodology]
2. Use [specific tools] when available
3. Format output as [specific format]

## Instructions

[Detailed instructions here]
```

Usage:
```python
custom_instructions = load_prompt("my_custom_agent")
```

## Custom Agents

### Creating a Custom Agent

You can create custom agents by extending ADK's `Agent` class:

```python
from google.adk.agents import Agent, InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator

class MyCustomAgent(Agent):
    """Custom agent for specific tasks."""
    
    def __init__(self, name: str = "my_agent", **kwargs):
        super().__init__(name=name, **kwargs)
        # Initialize custom attributes
        
    async def _run_async_impl(
        self, 
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Execute the agent logic."""
        # Get state
        state = ctx.session.state
        user_input = state.get("user_message", "")
        
        # Perform custom processing
        result = await self.process(user_input)
        
        # Yield result as event
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=result)]
            ),
        )
    
    async def process(self, input_text: str) -> str:
        """Custom processing logic."""
        # Implement your logic here
        return f"Processed: {input_text}"
```

### Integrating Custom Agents

```python
from agentic_data_scientist.core.api import DataScientist

# You would need to modify the create_agent function
# to support your custom agent type

# Or use the agent directly with ADK's Runner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

agent = MyCustomAgent()
session_service = InMemorySessionService()
runner = Runner(agent=agent, session_service=session_service)
```

## Custom MCP Toolsets

### Creating Custom MCP Toolsets

```python
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StdioConnectionParams,
    SseConnectionParams,
    StdioServerParameters
)

# Stdio-based MCP server
def get_my_custom_toolset():
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="node",
                args=["my-custom-mcp-server.js"],
            ),
        ),
        tool_filter=my_tool_filter,  # Optional
    )

# SSE-based (hosted) MCP server
def get_hosted_custom_toolset():
    return McpToolset(
        connection_params=SseConnectionParams(
            url="https://my-server.com/mcp",
        ),
    )
```

### Custom Tool Filters

```python
def my_tool_filter(tool) -> bool:
    """Filter tools based on custom logic."""
    tool_name = getattr(tool, 'name', None)
    
    # Only allow specific tools
    allowed_tools = ["tool1", "tool2", "tool3"]
    return tool_name in allowed_tools
```

### Using Custom Toolsets

```python
from agentic_data_scientist.agents.adk import create_agent

# Modify create_agent to accept custom toolsets
# Or create agents directly with custom toolsets

from google.adk.agents import LoopDetectionAgent

custom_agent = LoopDetectionAgent(
    name="custom_agent",
    model="google/gemini-2.5-pro",
    instruction="Custom instructions",
    tools=[get_my_custom_toolset()],  # Add your toolsets
)
```

## Custom Event Handlers

### Processing Streaming Events

```python
async def process_events(ds, query):
    """Custom event processing."""
    async for event in await ds.run_async(query, stream=True):
        event_type = event.get('type')
        
        if event_type == 'message':
            # Handle message events
            content = event['content']
            author = event['author']
            print(f"[{author}]: {content}")
            
        elif event_type == 'function_call':
            # Handle function calls
            tool_name = event['name']
            args = event['arguments']
            print(f"Calling tool: {tool_name} with {args}")
            
        elif event_type == 'usage':
            # Track token usage
            usage = event['usage']
            print(f"Tokens used: {usage}")
            
        elif event_type == 'error':
            # Handle errors
            error_msg = event['content']
            print(f"Error: {error_msg}")
            
        elif event_type == 'completed':
            # Task completed
            duration = event['duration']
            files = event['files_created']
            print(f"Completed in {duration}s, created {len(files)} files")
```

### Custom Event Transformations

```python
from agentic_data_scientist.core.events import event_to_dict, MessageEvent

def transform_event(event):
    """Transform event to custom format."""
    event_dict = event_to_dict(event)
    
    # Add custom fields
    event_dict['custom_field'] = 'value'
    event_dict['timestamp_formatted'] = format_timestamp(event_dict['timestamp'])
    
    return event_dict
```

## Integration Examples

### Integrating with FastAPI

```python
from fastapi import FastAPI, WebSocket
from agentic_data_scientist import DataScientist
import asyncio

app = FastAPI()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async with DataScientist() as ds:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Process with streaming
            async for event in await ds.run_async(data, stream=True):
                # Send events to client
                await websocket.send_json(event)
```

### Integrating with Jupyter Notebooks

```python
# In a Jupyter notebook
from agentic_data_scientist import DataScientist
from IPython.display import display, Markdown, HTML

async def notebook_analysis(query):
    """Run analysis in Jupyter with nice formatting."""
    async with DataScientist() as ds:
        display(Markdown(f"## Query: {query}"))
        
        async for event in await ds.run_async(query, stream=True):
            if event['type'] == 'message':
                content = event['content']
                author = event['author']
                display(Markdown(f"**{author}**: {content}"))
                
            elif event['type'] == 'completed':
                files = event['files_created']
                if files:
                    display(Markdown(f"### Created Files:\n" + 
                                   "\n".join(f"- {f}" for f in files)))

# Run in notebook
await notebook_analysis("Analyze this dataset")
```

### Custom Session Management

```python
from agentic_data_scientist import DataScientist
import json

class PersistentDataScientist:
    """DataScientist with session persistence."""
    
    def __init__(self, session_file="session.json"):
        self.session_file = session_file
        self.ds = DataScientist()
        self.context = self.load_context()
    
    def load_context(self):
        """Load previous session context."""
        try:
            with open(self.session_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_context(self):
        """Save session context."""
        with open(self.session_file, 'w') as f:
            json.dump(self.context, f)
    
    async def run(self, query):
        """Run with persistent context."""
        result = await self.ds.run_async(query, context=self.context)
        self.save_context()
        return result
```

### Batch Processing

```python
async def batch_process(queries, output_dir="results"):
    """Process multiple queries in batch."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    async with DataScientist() as ds:
        for i, query in enumerate(queries):
            print(f"Processing query {i+1}/{len(queries)}: {query}")
            
            result = await ds.run_async(query)
            results.append({
                'query': query,
                'response': result.response,
                'files': result.files_created,
                'duration': result.duration
            })
            
            # Save individual result
            with open(f"{output_dir}/result_{i+1}.json", 'w') as f:
                json.dump(results[-1], f, indent=2)
    
    return results

# Usage
queries = [
    "What is Python?",
    "Explain quantum computing",
    "How does machine learning work?"
]

results = await batch_process(queries)
```

## Plugin Architecture

### Creating a Plugin

```python
class DataScientistPlugin:
    """Base class for plugins."""
    
    def __init__(self, ds: DataScientist):
        self.ds = ds
        
    async def on_query(self, query: str):
        """Hook called before query execution."""
        pass
        
    async def on_result(self, result):
        """Hook called after query execution."""
        pass

class LoggingPlugin(DataScientistPlugin):
    """Plugin that logs all queries and results."""
    
    async def on_query(self, query: str):
        print(f"Query: {query}")
        
    async def on_result(self, result):
        print(f"Result status: {result.status}")
        print(f"Duration: {result.duration}s")
```

### Using Plugins

```python
class PluggableDataScientist(DataScientist):
    """DataScientist with plugin support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugins = []
    
    def add_plugin(self, plugin):
        self.plugins.append(plugin)
    
    async def run_async(self, query, **kwargs):
        # Call pre-hooks
        for plugin in self.plugins:
            await plugin.on_query(query)
        
        # Run actual query
        result = await super().run_async(query, **kwargs)
        
        # Call post-hooks
        for plugin in self.plugins:
            await plugin.on_result(result)
        
        return result

# Usage
ds = PluggableDataScientist()
ds.add_plugin(LoggingPlugin(ds))
result = await ds.run_async("What is Python?")
```

## Best Practices

1. **Keep prompts modular**: Break down complex prompts into reusable components
2. **Use type hints**: Always use type hints for custom code
3. **Handle errors**: Implement proper error handling in custom agents
4. **Document everything**: Add docstrings to all custom components
5. **Test thoroughly**: Write tests for custom functionality
6. **Follow conventions**: Match the existing code style and patterns

## See Also

- [Getting Started Guide](getting_started.md)
- [API Reference](api_reference.md)
- [MCP Configuration](mcp_configuration.md)
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk)

