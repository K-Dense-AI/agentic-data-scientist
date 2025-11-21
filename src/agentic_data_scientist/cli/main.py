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

# Suppress third-party library console output early, before importing our modules
# This prevents libraries like LiteLLM from setting up their own console handlers
for lib_name in ['LiteLLM', 'litellm', 'httpx', 'httpcore', 'openai', 'anthropic', 'google_adk']:
    lib_logger = logging.getLogger(lib_name)
    lib_logger.setLevel(logging.WARNING)  # Only warnings and above
    lib_logger.propagate = False  # Don't propagate to root logger yet

# Configure LiteLLM to suppress its own logging output
import os
os.environ['LITELLM_LOG'] = 'ERROR'  # Only show errors from LiteLLM

# Try to suppress LiteLLM's verbose output if the module is available
try:
    import litellm
    litellm.suppress_debug_info = True
    litellm.drop_params = True
    litellm.turn_off_message_logging = True
except (ImportError, AttributeError):
    # LiteLLM not installed yet or attributes don't exist, will be configured later
    pass

from agentic_data_scientist import DataScientist


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
@click.option(
    '--working-dir',
    '-w',
    type=click.Path(),
    help='Working directory for the session (default: temporary directory in /tmp)',
)
@click.option(
    '--keep-files',
    is_flag=True,
    help='Keep working directory after completion (default: cleanup temp dirs, preserve custom dirs)',
)
@click.option('--stream/--no-stream', default=False, help='Stream responses in real-time')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option(
    '--log-file',
    type=click.Path(),
    help='Path to log file (default: .agentic_ds.log in working directory)',
)
def main(
    query: Optional[str],
    files: tuple,
    mode: str,
    working_dir: Optional[str],
    keep_files: bool,
    stream: bool,
    verbose: bool,
    log_file: Optional[str],
):
    """
    Run Agentic Data Scientist with a query.

    MODE:
        orchestrated (default): Full multi-agent system with planning, verification, and Claude Code implementation
        simple: Direct Claude Code execution without orchestration

    Examples:

        Basic query:
            agentic-data-scientist "What is machine learning?"

        Single file:
            agentic-data-scientist "Analyze this data" --files data.csv

        Multiple files:
            agentic-data-scientist "Compare datasets" --files data1.csv --files data2.csv
            agentic-data-scientist "Analyze all CSVs" -f file1.csv -f file2.csv -f file3.csv

        Directory (recursive):
            agentic-data-scientist "Analyze all data" --files data_folder/

        Mixed files and directories:
            agentic-data-scientist "Full analysis" -f data.csv -f models/ -f results/

        Custom working directory:
            agentic-data-scientist "Process data" --files data.csv --working-dir ./my_workspace

        Keep files after completion:
            agentic-data-scientist "Generate report" --files data.csv --keep-files

        Custom log file location:
            agentic-data-scientist "Analyze data" --files data.csv --log-file ./analysis.log

        Simple mode with streaming:
            agentic-data-scientist "Write a Python script" --mode simple --stream

        Verbose logging:
            agentic-data-scientist "Debug issue" --files data.csv --verbose
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

    # Determine auto_cleanup based on keep_files flag
    auto_cleanup = not keep_files if keep_files else None  # None means use default behavior

    # Create core instance
    try:
        core = DataScientist(
            agent_type=agent_type,
            working_dir=working_dir,
            auto_cleanup=auto_cleanup,
        )
        
        # Configure logging to file
        if log_file:
            log_path = Path(log_file)
        else:
            # Default to hidden file in working directory
            log_path = Path(core.working_dir) / ".agentic_ds.log"
        
        # Create parent directories if needed
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure file handler for all logs
        file_handler = logging.FileHandler(log_path, mode='w')
        file_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Configure root logger - file only, remove any default console handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        # Remove existing handlers (like default StreamHandler)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        
        # Configure console handler for important user-facing messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter('%(message)s')  # Simpler format for console
        )
        
        # Add console handler only to agentic_data_scientist loggers
        app_logger = logging.getLogger('agentic_data_scientist')
        app_logger.addHandler(console_handler)
        app_logger.propagate = True  # Still send to root logger (file)
        
        # Re-enable propagation for third-party libraries so they go to log file
        # but keep them off the console
        for lib_name in ['LiteLLM', 'litellm', 'httpx', 'httpcore', 'openai', 'anthropic', 'google_adk']:
            lib_logger = logging.getLogger(lib_name)
            lib_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
            lib_logger.handlers.clear()  # Remove any console handlers
            lib_logger.propagate = True  # Send to root logger (file only)
        
        # Re-apply LiteLLM suppression settings in case it was imported
        try:
            import litellm
            litellm.suppress_debug_info = True
            litellm.drop_params = True
            litellm.turn_off_message_logging = True
        except (ImportError, AttributeError):
            pass
        
        # Display working directory information
        if working_dir:
            click.echo(f"Working directory: {core.working_dir}")
        else:
            click.echo(f"Working directory (temporary): {core.working_dir}")
        
        if core.auto_cleanup:
            click.echo("Files will be cleaned up after completion")
        else:
            click.echo("Files will be preserved after completion")
        
        click.echo(f"Logs: {log_path}")
        click.echo("")
        
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
                click.echo(f"Working directory: {core.working_dir}")
                if not core.auto_cleanup:
                    click.echo(f"\nFiles preserved at: {core.working_dir}")
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
                click.echo(f"Working directory: {core.working_dir}")
                if not core.auto_cleanup:
                    click.echo(f"\nFiles preserved at: {core.working_dir}")

            elif event_type == 'error':
                error_content = event.get('content', 'Unknown error')
                click.echo(f"\n[ERROR] {error_content}", err=True)

    except Exception as e:
        click.echo(f"\n\nStreaming error: {e}", err=True)
        raise


if __name__ == '__main__':
    main()
