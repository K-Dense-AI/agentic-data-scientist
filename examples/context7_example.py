"""
Example of using Context7 MCP for documentation retrieval.

This example demonstrates how the Claude Code agent can use Context7
to fetch up-to-date library documentation during implementation.
"""

import asyncio
from agentic_data_scientist import DataScientist


async def main():
    """Example using Context7 MCP for documentation queries."""
    
    # Use claude_code agent which has Context7 MCP configured
    async with DataScientist(agent_type="claude_code") as ds:
        # The agent will automatically use Context7 MCP to fetch library docs
        result = await ds.run_async(
            """
            Show me how to use pandas 2.0 new features for data analysis.
            Specifically, I want to see examples of:
            1. The new PyArrow string type
            2. Copy-on-write behavior
            3. Any performance improvements
            """,
            stream=False
        )
        
        print("Response:")
        print(result.response)
        print("\n" + "="*80 + "\n")
        
        # Another example with different library
        result2 = await ds.run_async(
            """
            I need to implement authentication in a FastAPI application.
            Show me the recommended approach using the latest FastAPI features.
            """,
            stream=False
        )
        
        print("Response:")
        print(result2.response)


if __name__ == "__main__":
    asyncio.run(main())

