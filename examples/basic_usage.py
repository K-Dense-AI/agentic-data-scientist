#!/usr/bin/env python
"""
Basic usage example for Agentic Data Scientist.

This example shows how to use Agentic Data Scientist programmatically to run
a simple query and get results.

Usage:
    uv run python examples/basic_usage.py
"""

from agentic_data_scientist import DataScientist


def main():
    """Run a basic query with Agentic Data Scientist."""

    # Use context manager for automatic cleanup
    with DataScientist(agent_type="adk") as ds:
        # Run a simple query
        query = "Explain the concept of machine learning in simple terms."

        print("Running query:", query)
        print("=" * 60)

        # Execute the query (synchronous)
        result = ds.run(query)

        # Check the result
        if result.status == "completed":
            print("\nResponse:")
            print(result.response)
            print("\n" + "=" * 60)
            print(f"Duration: {result.duration:.2f}s")
            print(f"Session ID: {result.session_id}")

            if result.files_created:
                print(f"\nFiles created ({len(result.files_created)}):")
                for file in result.files_created:
                    print(f"  - {file}")
        else:
            print(f"\nError: {result.error}")


if __name__ == "__main__":
    main()
