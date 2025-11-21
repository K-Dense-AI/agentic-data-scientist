"""
Agentic Data Scientist CLI interface.

Simple command-line interface for running Agentic Data Scientist agents.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click

from agentic_data_scientist import DataScientist


# Suppress third-party library console output early, before importing our modules
# This prevents libraries like LiteLLM from setting up their own console handlers
for lib_name in ['LiteLLM', 'litellm', 'httpx', 'httpcore', 'openai', 'anthropic', 'google_adk']:
    lib_logger = logging.getLogger(lib_name)
    lib_logger.setLevel(logging.WARNING)  # Only warnings and above
    lib_logger.propagate = False  # Don't propagate to root logger yet


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
    required=True,
    type=click.Choice(['orchestrated', 'simple']),
    help='REQUIRED: Execution mode - "orchestrated" (full multi-agent with planning) or "simple" (direct coding)',
)
@click.option(
    '--working-dir',
    '-w',
    type=click.Path(),
    help='Working directory for the session (default: ./agentic_output/)',
)
@click.option(
    '--temp-dir',
    is_flag=True,
    help='Use temporary directory in /tmp (auto-cleanup enabled)',
)
@click.option(
    '--keep-files',
    is_flag=True,
    help='Keep working directory after completion (only applies when not using --temp-dir)',
)
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
    temp_dir: bool,
    keep_files: bool,
    verbose: bool,
    log_file: Optional[str],
):
    """
    Run Agentic Data Scientist with a query.

    IMPORTANT: You must specify --mode to choose between orchestrated (with planning)
    or simple (direct coding) execution. This ensures you're always aware of the
    complexity and API cost of your analysis.

    MODE (REQUIRED):
        orchestrated: Full multi-agent system with planning, verification, and Claude Code implementation
        simple: Direct Claude Code execution without orchestration (faster, cheaper)

    WORKING DIRECTORY:
        By default, creates ./agentic_output/ in your current directory and preserves files.
        Use --temp-dir for temporary /tmp directory with auto-cleanup.
        Use --working-dir for custom location.

    Examples:

        Orchestrated analysis (full multi-agent workflow):
            agentic-data-scientist "Perform differential expression analysis" --mode orchestrated --files data.csv

        Simple mode (direct coding, no planning):
            agentic-data-scientist "Write a Python script to parse CSV" --mode simple

        Question answering:
            agentic-data-scientist "Explain how gradient boosting works" --mode simple

        Multiple files:
            agentic-data-scientist "Compare datasets" --mode orchestrated -f data1.csv -f data2.csv

        Directory upload (recursive):
            agentic-data-scientist "Analyze all data" --mode orchestrated --files data_folder/

        Use temporary directory (auto-cleanup):
            agentic-data-scientist "Quick analysis" --mode simple --files data.csv --temp-dir

        Custom working directory:
            agentic-data-scientist "Process data" --mode orchestrated --files data.csv --working-dir ./my_analysis

        Keep files (override default preservation):
            agentic-data-scientist "Generate report" --mode orchestrated --files data.csv --keep-files

        Custom log file location:
            agentic-data-scientist "Analyze data" --mode orchestrated --files data.csv --log-file ./analysis.log

        Verbose logging:
            agentic-data-scientist "Debug issue" --mode simple --files data.csv --verbose
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

    # Determine working directory and cleanup behavior
    if temp_dir:
        # Use temp directory with auto-cleanup
        working_dir_to_use = None  # Will create temp dir
        auto_cleanup = True
    elif working_dir:
        # Use custom directory, default to no cleanup unless keep_files is explicitly set
        working_dir_to_use = working_dir
        auto_cleanup = not keep_files
    else:
        # Default to ./agentic_output/ with no cleanup
        working_dir_to_use = "./agentic_output"
        auto_cleanup = not keep_files if keep_files else False

    # Create core instance
    try:
        core = DataScientist(
            agent_type=agent_type,
            working_dir=working_dir_to_use,
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
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

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
        if temp_dir:
            click.echo(f"Working directory (temporary): {core.working_dir}")
            click.echo("Files will be cleaned up after completion")
        else:
            click.echo(f"Working directory: {core.working_dir}")
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


if __name__ == '__main__':
    main()
