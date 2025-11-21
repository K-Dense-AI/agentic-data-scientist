"""
File operation tools for ADK agents.

All file operations are read-only and enforce working_dir sandboxing.
Paths are validated to prevent access outside the working directory.
"""

import base64
import json
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def _truncate_content(content: str, max_content_length: int) -> str:
    """
    Truncate content to maximum length and add warning if truncated.

    Parameters
    ----------
    content : str
        The content to potentially truncate
    max_content_length : int
        Maximum allowed length in characters

    Returns
    -------
    str
        Original content if under limit, or truncated content with warning message
    """
    if len(content) <= max_content_length:
        return content

    original_length = len(content)
    truncated = content[:max_content_length]
    warning = (
        f"\n\n[Content truncated at {max_content_length:,} characters. Original length: {original_length:,} characters]"
    )
    return truncated + warning


def _validate_path(path: str, working_dir: str) -> Path:
    """
    Validate and resolve a path within the working directory.

    Parameters
    ----------
    path : str
        The path to validate (can be relative or absolute)
    working_dir : str
        The working directory root

    Returns
    -------
    Path
        The resolved absolute path

    Raises
    ------
    ValueError
        If the path is outside the working directory
    """
    working_path = Path(working_dir).resolve()

    # Resolve the target path
    if Path(path).is_absolute():
        target_path = Path(path).resolve()
    else:
        target_path = (working_path / path).resolve()

    # Security check: ensure target is within working directory
    try:
        target_path.relative_to(working_path)
    except ValueError:
        # Don't expose the full path in error message for security
        raise ValueError("Access denied: Path is outside the allowed working directory")

    return target_path


def _format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Parameters
    ----------
    size_bytes : int
        Size in bytes

    Returns
    -------
    str
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def read_file(
    path: str,
    working_dir: str,
    head: Optional[int] = None,
    tail: Optional[int] = None,
    max_content_length: int = 10000,
) -> str:
    """
    Read the complete contents of a text file.

    Parameters
    ----------
    path : str
        Path to the file (relative to working_dir or absolute)
    working_dir : str
        Working directory root for security validation
    head : int, optional
        If provided, returns only the first N lines
    tail : int, optional
        If provided, returns only the last N lines
    max_content_length : int, optional
        Maximum content length in characters before truncation, default 10000

        **WARNING: Do not modify max_content_length unless absolutely necessary.
        The default 10,000 character limit prevents token overflow.**

    Returns
    -------
    str
        File contents or error message

    Notes
    -----
    - Only files within working_dir can be accessed
    - If both head and tail are provided, tail takes precedence
    - Handles various text encodings automatically
    - Content exceeding max_content_length will be truncated with a warning message
    """
    logger.info(f"[Tool:read_file] Reading '{path}' (head={head}, tail={tail})")
    try:
        file_path = _validate_path(path, working_dir)

        if not file_path.exists():
            return f"Error: File '{path}' does not exist"

        if not file_path.is_file():
            return f"Error: '{path}' is not a file"

        # Read file content
        content = file_path.read_text(encoding="utf-8", errors="replace")

        # Apply head/tail filtering if requested
        if tail is not None:
            lines = content.splitlines()
            content = "\n".join(lines[-tail:])
        elif head is not None:
            lines = content.splitlines()
            content = "\n".join(lines[:head])

        # Apply content length truncation
        content = _truncate_content(content, max_content_length)

        return content

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def read_media_file(path: str, working_dir: str) -> str:
    """
    Read a binary/media file (images, audio, etc.) and return base64 encoded data.

    This function follows the MCP filesystem server implementation for handling
    binary files. Returns a JSON string containing the base64 data and MIME type.

    Parameters
    ----------
    path : str
        Path to the media file (relative to working_dir or absolute)
    working_dir : str
        Working directory root for security validation

    Returns
    -------
    str
        JSON string with 'data' (base64 encoded) and 'mimeType' fields,
        or error message

    Notes
    -----
    - Only files within working_dir can be accessed
    - Returns base64 encoded binary data for transmission
    - MIME type is automatically detected from file extension
    - Supported for images, audio, video, and other binary formats
    - File size limit: 10 MB (files larger than this will be rejected)
    - Media files are NOT truncated as partial media files are broken

    Examples
    --------
    >>> result = read_media_file("image.png", "/working/dir")
    >>> import json
    >>> parsed = json.loads(result)
    >>> print(parsed["mimeType"])  # "image/png"
    >>> print(parsed["data"][:20])  # "iVBORw0KGgoAAAANSUh..."
    """
    logger.info(f"[Tool:read_media_file] Reading media file '{path}'")
    try:
        file_path = _validate_path(path, working_dir)

        if not file_path.exists():
            return f"Error: File '{path}' does not exist"

        if not file_path.is_file():
            return f"Error: '{path}' is not a file"

        # Check file size before reading (10 MB limit)
        MAX_MEDIA_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
        file_size = file_path.stat().st_size
        if file_size > MAX_MEDIA_SIZE:
            size_mb = file_size / (1024 * 1024)
            return f"Error: Media file exceeds size limit of 10 MB (actual: {size_mb:.1f} MB)"

        # Read file as binary and encode to base64
        with open(file_path, "rb") as f:
            file_data = f.read()

        base64_data = base64.b64encode(file_data).decode("utf-8")

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        # Return as JSON string (compatible with ADK tool interface)
        result = {
            "data": base64_data,
            "mimeType": mime_type,
        }
        return json.dumps(result)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading media file: {e}"


def list_directory(
    path: str = ".",
    working_dir: str = "",
    show_sizes: bool = False,
    sort_by: str = "name",
    max_content_length: int = 10000,
) -> str:
    """
    List the contents of a directory.

    Parameters
    ----------
    path : str, optional
        Path to the directory (relative to working_dir or absolute), default "."
    working_dir : str
        Working directory root for security validation
    show_sizes : bool, optional
        If True, display file sizes, default False
    sort_by : str, optional
        Sort order: "name" or "size", default "name"
    max_content_length : int, optional
        Maximum content length in characters before truncation, default 10000

        **WARNING: Do not modify max_content_length unless absolutely necessary.
        The default 10,000 character limit prevents token overflow.**

    Returns
    -------
    str
        Formatted directory listing or error message

    Notes
    -----
    - Only directories within working_dir can be accessed
    - Files are prefixed with [FILE], directories with [DIR]
    - Sizes are shown in human-readable format (KB, MB, etc.)
    - Hidden files (starting with '.') are included
    - Output exceeding max_content_length will be truncated with a warning message
    """
    logger.info(f"[Tool:list_directory] Listing '{path}' (show_sizes={show_sizes}, sort_by={sort_by})")
    try:
        dir_path = _validate_path(path, working_dir)

        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist"

        if not dir_path.is_dir():
            return f"Error: '{path}' is not a directory"

        # Get directory entries
        entries = []
        for entry in dir_path.iterdir():
            try:
                stats = entry.stat()
                entries.append(
                    {
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": stats.st_size if entry.is_file() else 0,
                        "mtime": stats.st_mtime,
                    }
                )
            except Exception:
                # Skip entries we can't stat
                continue

        # Sort entries
        if sort_by == "size":
            entries.sort(key=lambda x: x["size"], reverse=True)
        else:
            entries.sort(key=lambda x: x["name"])

        # Format output
        lines = []
        for entry in entries:
            prefix = "[DIR] " if entry["is_dir"] else "[FILE]"
            name = entry["name"].ljust(40)

            if show_sizes and not entry["is_dir"]:
                size_str = _format_size(entry["size"]).rjust(10)
                lines.append(f"{prefix}{name} {size_str}")
            else:
                lines.append(f"{prefix}{name}")

        # Add summary
        total_files = sum(1 for e in entries if not e["is_dir"])
        total_dirs = sum(1 for e in entries if e["is_dir"])
        total_size = sum(e["size"] for e in entries if not e["is_dir"])

        lines.append("")
        lines.append(f"Total: {total_files} files, {total_dirs} directories")
        if show_sizes:
            lines.append(f"Combined size: {_format_size(total_size)}")

        result = "\n".join(lines)
        return _truncate_content(result, max_content_length)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


def directory_tree(
    path: str = ".",
    working_dir: str = "",
    exclude_patterns: Optional[list[str]] = None,
    max_content_length: int = 10000,
) -> str:
    """
    Generate a recursive directory tree view.

    Parameters
    ----------
    path : str, optional
        Path to the directory (relative to working_dir or absolute), default "."
    working_dir : str
        Working directory root for security validation
    exclude_patterns : list[str], optional
        List of glob patterns to exclude (e.g., ["*.pyc", "__pycache__"])
    max_content_length : int, optional
        Maximum content length in characters before truncation, default 10000

        **WARNING: Do not modify max_content_length unless absolutely necessary.
        The default 10,000 character limit prevents token overflow.**

    Returns
    -------
    str
        JSON string representing the directory tree or error message

    Notes
    -----
    - Only directories within working_dir can be accessed
    - Returns a JSON structure with nested entries
    - Each entry has "name", "type" (file/directory), and optional "children"
    - Hidden files (starting with '.') are included unless excluded
    - Output exceeding max_content_length will be truncated with a warning message

    Examples
    --------
    >>> tree = directory_tree(".", "/working/dir", exclude_patterns=["*.pyc"])
    >>> import json
    >>> parsed = json.loads(tree)
    >>> print(parsed[0]["name"])  # First entry name
    """
    logger.info(f"[Tool:directory_tree] Building tree for '{path}' (exclude_patterns={exclude_patterns})")
    if exclude_patterns is None:
        exclude_patterns = []

    try:
        root_path = _validate_path(path, working_dir)

        if not root_path.exists():
            return f"Error: Directory '{path}' does not exist"

        if not root_path.is_dir():
            return f"Error: '{path}' is not a directory"

        def should_exclude(entry_path: Path, root: Path) -> bool:
            """
            Check if path matches any exclude pattern.

            Parameters
            ----------
            entry_path : Path
                The path to check
            root : Path
                The root path for relative path calculation

            Returns
            -------
            bool
                True if the path should be excluded, False otherwise
            """
            from fnmatch import fnmatch

            try:
                relative = entry_path.relative_to(root)
                rel_str = str(relative)
                entry_name = entry_path.name

                for pattern in exclude_patterns:
                    # Check if pattern has wildcards
                    if '*' in pattern or '?' in pattern:
                        # Use glob-style matching
                        if fnmatch(entry_name, pattern) or fnmatch(rel_str, pattern):
                            return True
                    else:
                        # Exact matching
                        if pattern in rel_str or entry_name == pattern:
                            return True
                        # Check if it's in an excluded directory
                        if any(part == pattern.rstrip('/') for part in relative.parts):
                            return True
            except ValueError:
                pass
            return False

        def build_tree(current_path: Path) -> list[dict[str, str | list]]:
            """
            Recursively build directory tree.

            Parameters
            ----------
            current_path : Path
                The current directory path to build tree for

            Returns
            -------
            list[dict[str, str | list]]
                List of directory entries with name, type, and optional children
            """
            entries = []

            try:
                for entry in sorted(current_path.iterdir(), key=lambda x: x.name):
                    if should_exclude(entry, root_path):
                        continue

                    entry_data = {
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                    }

                    if entry.is_dir():
                        try:
                            entry_data["children"] = build_tree(entry)
                        except PermissionError:
                            entry_data["children"] = []

                    entries.append(entry_data)
            except PermissionError:
                pass

            return entries

        tree_data = build_tree(root_path)
        result = json.dumps(tree_data, indent=2)
        return _truncate_content(result, max_content_length)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating directory tree: {e}"


def search_files(
    pattern: str,
    working_dir: str,
    path: str = ".",
    exclude_patterns: Optional[list[str]] = None,
    max_content_length: int = 10000,
) -> str:
    """
    Search for files matching a pattern.

    Parameters
    ----------
    pattern : str
        Glob pattern to match (e.g., "*.py", "test_*.txt")
    working_dir : str
        Working directory root for security validation
    path : str, optional
        Directory to search in (relative to working_dir or absolute), default "."
    exclude_patterns : list[str], optional
        List of patterns to exclude from results
    max_content_length : int, optional
        Maximum content length in characters before truncation, default 10000

        **WARNING: Do not modify max_content_length unless absolutely necessary.
        The default 10,000 character limit prevents token overflow.**

    Returns
    -------
    str
        Newline-separated list of matching file paths or error message

    Notes
    -----
    - Only searches within working_dir
    - Searches recursively through all subdirectories
    - Returns paths relative to the search directory
    - Hidden files are included unless excluded
    - Output exceeding max_content_length will be truncated with a warning message

    Examples
    --------
    >>> results = search_files("*.py", "/working/dir", exclude_patterns=["test_*"])
    >>> print(results)
    main.py
    utils.py
    lib/helpers.py
    """
    logger.info(f"[Tool:search_files] Searching for pattern '{pattern}' in '{path}'")
    if exclude_patterns is None:
        exclude_patterns = []

    try:
        search_path = _validate_path(path, working_dir)

        if not search_path.exists():
            return f"Error: Directory '{path}' does not exist"

        if not search_path.is_dir():
            return f"Error: '{path}' is not a directory"

        def should_exclude(file_path: Path) -> bool:
            """
            Check if path matches any exclude pattern.

            Parameters
            ----------
            file_path : Path
                The file path to check

            Returns
            -------
            bool
                True if the path should be excluded, False otherwise
            """
            file_name = file_path.name
            for excl_pattern in exclude_patterns:
                if excl_pattern in str(file_path) or excl_pattern == file_name:
                    return True
            return False

        # Search for matching files
        matches = []
        for file_path in search_path.rglob(pattern):
            if file_path.is_file() and not should_exclude(file_path):
                try:
                    # Return path relative to search directory
                    relative = file_path.relative_to(search_path)
                    matches.append(str(relative))
                except ValueError:
                    continue

        if not matches:
            return "No matches found"

        matches.sort()
        result = "\n".join(matches)
        return _truncate_content(result, max_content_length)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error searching files: {e}"


def get_file_info(path: str, working_dir: str) -> str:
    """
    Get detailed metadata about a file.

    Parameters
    ----------
    path : str
        Path to the file (relative to working_dir or absolute)
    working_dir : str
        Working directory root for security validation

    Returns
    -------
    str
        Formatted file information or error message

    Notes
    -----
    - Only files within working_dir can be accessed
    - Returns size, modification time, access time, type, and permissions
    - All timestamps are in ISO 8601 format

    Examples
    --------
    >>> info = get_file_info("data.csv", "/working/dir")
    >>> print(info)
    name: data.csv
    size: 1.5 MB
    type: file
    modified: 2025-01-15T10:30:00
    accessed: 2025-01-15T10:35:00
    permissions: rw-r--r--
    """
    logger.info(f"[Tool:get_file_info] Getting info for '{path}'")
    try:
        file_path = _validate_path(path, working_dir)

        if not file_path.exists():
            return f"Error: File '{path}' does not exist"

        stats = file_path.stat()

        # Get file type
        if file_path.is_file():
            file_type = "file"
        elif file_path.is_dir():
            file_type = "directory"
        elif file_path.is_symlink():
            file_type = "symlink"
        else:
            file_type = "other"

        # Format permissions
        mode = stats.st_mode
        permissions = []
        for who in [(0o400, 0o200, 0o100), (0o040, 0o020, 0o010), (0o004, 0o002, 0o001)]:
            permissions.append("r" if mode & who[0] else "-")
            permissions.append("w" if mode & who[1] else "-")
            permissions.append("x" if mode & who[2] else "-")
        perm_str = "".join(permissions)

        # Build info string
        info_lines = [
            f"name: {file_path.name}",
            f"size: {_format_size(stats.st_size)}",
            f"type: {file_type}",
            f"modified: {datetime.fromtimestamp(stats.st_mtime).isoformat()}",
            f"accessed: {datetime.fromtimestamp(stats.st_atime).isoformat()}",
            f"permissions: {perm_str}",
        ]

        return "\n".join(info_lines)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error getting file info: {e}"
