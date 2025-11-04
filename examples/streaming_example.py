#!/usr/bin/env python
"""
Streaming example for Agentic Data Scientist.

This example shows how to use Agentic Data Scientist with streaming to see
real-time progress as the agent works.

Usage:
    uv run python examples/streaming_example.py
"""

import asyncio

from agentic_data_scientist import DataScientist


async def main():
    """Run a query with streaming enabled."""

    # Use async context manager for automatic cleanup
    async with DataScientist(agent_type="adk") as ds:
        # Run a query with streaming
        query = "Write a Python function to calculate fibonacci numbers and explain how it works."

        print("Running query with streaming:", query)
        print("=" * 60 + "\n")

        # Execute with streaming (asynchronous)
        async for event in await ds.run_async(query, stream=True):
            event_type = event.get('type')

            if event_type == 'message':
                author = event.get('author', 'agent')
                content = event.get('content', '')
                is_thought = event.get('is_thought', False)

                if is_thought:
                    print(f"\n[{author} - THINKING]: {content}")
                else:
                    print(f"\n[{author}]: {content}")

            elif event_type == 'function_call':
                name = event.get('name', 'unknown')
                print(f"\n[TOOL] Calling {name}(...)")

            elif event_type == 'completed':
                duration = event.get('duration', 0)
                files_count = event.get('files_count', 0)
                print("\n\n" + "=" * 60)
                print("COMPLETED")
                print("=" * 60)
                print(f"Duration: {duration:.2f}s")
                print(f"Files created: {files_count}")
                print(f"Session ID: {event.get('session_id', 'unknown')}")

            elif event_type == 'error':
                error_content = event.get('content', 'Unknown error')
                print(f"\n[ERROR] {error_content}")


if __name__ == "__main__":
    asyncio.run(main())
