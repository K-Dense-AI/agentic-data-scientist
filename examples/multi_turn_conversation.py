#!/usr/bin/env python
"""
Multi-turn conversation example for Agentic Data Scientist.

This example shows how to maintain conversation context across
multiple queries using the same Agentic Data Scientist instance.

Usage:
    uv run python examples/multi_turn_conversation.py
"""

import asyncio

from agentic_data_scientist import DataScientist


async def main():
    """Run a multi-turn conversation."""

    # Use async context manager for automatic cleanup
    async with DataScientist(agent_type="adk") as ds:
        print("Starting multi-turn conversation")
        print("=" * 60 + "\n")

        # Conversation context (optional - for future use)
        context = {}

        # First turn
        print("Turn 1: Asking about Python")
        query1 = "What is Python programming language?"
        result1 = await ds.run_async(query1, context=context)
        print(f"Response: {result1.response[:200]}...")
        print()

        # Second turn - builds on previous context
        print("Turn 2: Asking for an example (builds on previous context)")
        query2 = "Can you give me a simple example?"
        result2 = await ds.run_async(query2, context=context)
        print(f"Response: {result2.response[:200]}...")
        print()

        # Third turn - asking for clarification
        print("Turn 3: Asking for clarification")
        query3 = "Can you explain that example in more detail?"
        result3 = await ds.run_async(query3, context=context)
        print(f"Response: {result3.response[:200]}...")
        print()

        print("=" * 60)
        print("Conversation complete!")
        print(f"Session ID: {ds.session_id}")


if __name__ == "__main__":
    asyncio.run(main())
