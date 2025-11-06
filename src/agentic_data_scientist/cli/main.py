"""
Agentic Data Scientist CLI interface.

Simple command-line interface for running Agentic Data Scientist agents.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from agentic_data_scientist import DataScientist


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@click.command()
@click.argument('query', required=False)
@click.option(
    '--files',
    '-f',
    multiple=True,
    help='Files or directories to include in the query (directories are uploaded recursively)',
)
@click.option(
    '--mode',
    default='orchestrated',
    type=click.Choice(['orchestrated', 'simple']),
    help='Execution mode: "orchestrated" (default, with planning) or "simple" (direct Claude Code)',
)
@click.option('--stream/--no-stream', default=False, help='Stream responses in real-time')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(
    query: Optional[str],
    files: tuple,
    mode: str,
    stream: bool,
    verbose: bool,
):
    """
    Run Agentic Data Scientist with a query.

    MODE:
        orchestrated (default): Full multi-agent system with planning, verification, and Claude Code implementation
        simple: Direct Claude Code execution without orchestration

    Examples:

        agentic-data-scientist "What is machine learning?"

        agentic-data-scientist "Analyze this data" --files data.csv

        agentic-data-scientist "Analyze all data" --files data_folder/

        agentic-data-scientist "Compare datasets" -f data1.csv -f data2.csv -f experiments/

        agentic-data-scientist "Write a Python script" --mode simple --stream
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get query from stdin if not provided
    if not query:
        if not sys.stdin.isatty():
            query = sys.stdin.read().strip()
        else:
            click.echo("Error: No query provided. Use 'agentic-data-scientist \"your query\"' or pipe input.", err=True)
            sys.exit(1)

    # Prepare file list
    file_list = []
    for f in files:
        path = Path(f)
        if not path.exists():
            click.echo(f"Warning: File not found: {f}", err=True)
            continue

        # Handle directory - recursively add all files
        if path.is_dir():
            files_found = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    # Preserve relative path structure from the directory being uploaded
                    relative_name = file_path.relative_to(path)
                    file_list.append((str(relative_name), file_path))
                    files_found += 1

            if files_found > 0:
                click.echo(f"Found {files_found} file(s) in directory: {path}")
            else:
                click.echo(f"Warning: No files found in directory: {path}", err=True)
        else:
            # Handle single file
            file_list.append((path.name, path))

    # Map mode to agent_type
    agent_type = "adk" if mode == "orchestrated" else "claude_code"

    # Create core instance
    try:
        core = DataScientist(agent_type=agent_type)
    except Exception as e:
        click.echo(f"Error initializing Agentic Data Scientist: {e}", err=True)
        sys.exit(1)

    # Run query
    try:
        if stream:
            asyncio.run(run_streaming(core, query, file_list))
        else:
            result = core.run(query, files=file_list)
            if result.status == "completed":
                click.echo("\n" + "=" * 60)
                click.echo("RESPONSE:")
                click.echo("=" * 60)
                click.echo(result.response)
                click.echo("\n" + "=" * 60)
                if result.files_created:
                    click.echo(f"\nFiles created ({len(result.files_created)}):")
                    for file in result.files_created:
                        click.echo(f"  - {file}")
                click.echo(f"\nDuration: {result.duration:.2f}s")
                click.echo(f"Session ID: {result.session_id}")
            else:
                click.echo(f"\nError: {result.error}", err=True)
                sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        logger.exception("Unexpected error")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            core.cleanup()
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")


async def run_streaming(core, query, files):
    """Handle streaming output."""
    click.echo("\n" + "=" * 60)
    click.echo("STREAMING RESPONSE:")
    click.echo("=" * 60 + "\n")

    try:
        async for event in await core.run_async(query, files=files, stream=True):
            event_type = event.get('type')

            if event_type == 'message':
                author = event.get('author', 'agent')
                content = event.get('content', '')
                is_thought = event.get('is_thought', False)
                is_partial = event.get('is_partial', False)

                # Format output
                if is_thought:
                    prefix = f"[{author} - THINKING]"
                else:
                    prefix = f"[{author}]"

                if is_partial:
                    # For partial events, print without newline
                    click.echo(content, nl=False)
                else:
                    # For complete events, print with prefix
                    click.echo(f"\n{prefix}: {content}")

            elif event_type == 'function_call':
                name = event.get('name', 'unknown')
                click.echo(f"\n[TOOL] Calling {name}(...)")

            elif event_type == 'function_response':
                name = event.get('name', 'unknown')
                click.echo(f"[TOOL] {name} completed")

            elif event_type == 'file_created':
                file_path = event.get('file_path', 'unknown')
                click.echo(f"\n[FILE] Created: {file_path}")

            elif event_type == 'usage':
                usage = event.get('usage', {})
                total = usage.get('total_input_tokens', 0)
                cached = usage.get('cached_input_tokens', 0)
                output = usage.get('output_tokens', 0)
                click.echo(f"\n[USAGE] Input: {total} (cached: {cached}), Output: {output}")

            elif event_type == 'completed':
                duration = event.get('duration', 0)
                files_count = event.get('files_count', 0)
                click.echo("\n\n" + "=" * 60)
                click.echo("COMPLETED")
                click.echo("=" * 60)
                click.echo(f"Duration: {duration:.2f}s")
                click.echo(f"Files created: {files_count}")
                click.echo(f"Session ID: {event.get('session_id', 'unknown')}")

            elif event_type == 'error':
                error_content = event.get('content', 'Unknown error')
                click.echo(f"\n[ERROR] {error_content}", err=True)

    except Exception as e:
        click.echo(f"\n\nStreaming error: {e}", err=True)
        raise


if __name__ == '__main__':
    main()
