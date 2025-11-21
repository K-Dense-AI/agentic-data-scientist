"""
Unit tests for tools module.

Tests all file operations and web fetch functionality including
security boundary validation and edge cases.
"""

import base64
import json
from unittest.mock import Mock, patch

import pytest

from agentic_data_scientist.tools import (
    directory_tree,
    fetch_url,
    get_file_info,
    list_directory,
    read_file,
    read_media_file,
    search_files,
)


@pytest.fixture
def temp_workspace(tmp_path):
    """
    Create a temporary workspace with test files.

    Returns
    -------
    Path
        Path to temporary workspace directory
    """
    # Create directory structure
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested").mkdir()

    # Create text files
    (tmp_path / "test.txt").write_text("Hello, world!")
    (tmp_path / "data.csv").write_text("name,value\nalice,100\nbob,200")
    (tmp_path / "subdir" / "nested" / "deep.txt").write_text("Deep content")

    # Create a file with multiple lines for head/tail testing
    lines = [f"Line {i}" for i in range(1, 11)]
    (tmp_path / "multiline.txt").write_text("\n".join(lines))

    # Create a binary file (simple image-like data)
    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    (tmp_path / "image.png").write_bytes(binary_data)

    # Create Python files for search testing
    (tmp_path / "main.py").write_text("print('main')")
    (tmp_path / "subdir" / "utils.py").write_text("print('utils')")

    return tmp_path


class TestReadFile:
    """Tests for read_file function."""

    def test_read_file_success(self, temp_workspace):
        """Test reading a regular text file."""
        result = read_file("test.txt", str(temp_workspace))
        assert result == "Hello, world!"

    def test_read_file_with_path_in_subdir(self, temp_workspace):
        """Test reading a file in subdirectory."""
        result = read_file("subdir/nested/deep.txt", str(temp_workspace))
        assert result == "Deep content"

    def test_read_file_head(self, temp_workspace):
        """Test reading first N lines with head parameter."""
        result = read_file("multiline.txt", str(temp_workspace), head=3)
        expected = "Line 1\nLine 2\nLine 3"
        assert result == expected

    def test_read_file_tail(self, temp_workspace):
        """Test reading last N lines with tail parameter."""
        result = read_file("multiline.txt", str(temp_workspace), tail=3)
        expected = "Line 8\nLine 9\nLine 10"
        assert result == expected

    def test_read_file_nonexistent(self, temp_workspace):
        """Test reading a non-existent file."""
        result = read_file("missing.txt", str(temp_workspace))
        assert "Error" in result
        assert "does not exist" in result

    def test_read_file_directory(self, temp_workspace):
        """Test attempting to read a directory."""
        result = read_file("subdir", str(temp_workspace))
        assert "Error" in result
        assert "not a file" in result

    def test_read_file_outside_working_dir(self, temp_workspace):
        """Test security: reading outside working directory."""
        result = read_file("../outside.txt", str(temp_workspace))
        assert "Error" in result
        assert "outside" in result.lower()

    def test_read_file_absolute_path_outside(self, temp_workspace):
        """Test security: absolute path outside working directory."""
        result = read_file("/etc/passwd", str(temp_workspace))
        assert "Error" in result
        assert "outside" in result.lower()


class TestReadMediaFile:
    """Tests for read_media_file function."""

    def test_read_media_file_success(self, temp_workspace):
        """Test reading a binary file."""
        result = read_media_file("image.png", str(temp_workspace))

        # Parse JSON result
        data = json.loads(result)
        assert "data" in data
        assert "mimeType" in data
        assert data["mimeType"] == "image/png"

        # Verify base64 encoding
        decoded = base64.b64decode(data["data"])
        assert decoded.startswith(b"\x89PNG")

    def test_read_media_file_nonexistent(self, temp_workspace):
        """Test reading a non-existent media file."""
        result = read_media_file("missing.png", str(temp_workspace))
        assert "Error" in result
        assert "does not exist" in result

    def test_read_media_file_outside_working_dir(self, temp_workspace):
        """Test security: reading media file outside working directory."""
        result = read_media_file("../outside.png", str(temp_workspace))
        assert "Error" in result
        assert "outside" in result.lower()


class TestListDirectory:
    """Tests for list_directory function."""

    def test_list_directory_success(self, temp_workspace):
        """Test listing a directory."""
        result = list_directory(".", str(temp_workspace))

        assert "[FILE]" in result
        assert "[DIR]" in result
        assert "test.txt" in result
        assert "subdir" in result
        assert "Total:" in result

    def test_list_directory_with_sizes(self, temp_workspace):
        """Test listing with file sizes."""
        result = list_directory(".", str(temp_workspace), show_sizes=True)

        assert "B" in result or "KB" in result  # Size units
        assert "Combined size:" in result

    def test_list_directory_sort_by_size(self, temp_workspace):
        """Test sorting by size."""
        result = list_directory(".", str(temp_workspace), sort_by="size", show_sizes=True)

        assert "Total:" in result
        # Largest files should appear first (excluding directories)

    def test_list_directory_subdir(self, temp_workspace):
        """Test listing a subdirectory."""
        result = list_directory("subdir", str(temp_workspace))

        assert "nested" in result or "utils.py" in result

    def test_list_directory_nonexistent(self, temp_workspace):
        """Test listing a non-existent directory."""
        result = list_directory("missing", str(temp_workspace))
        assert "Error" in result
        assert "does not exist" in result

    def test_list_directory_file(self, temp_workspace):
        """Test listing a file (should fail)."""
        result = list_directory("test.txt", str(temp_workspace))
        assert "Error" in result
        assert "not a directory" in result

    def test_list_directory_outside_working_dir(self, temp_workspace):
        """Test security: listing outside working directory."""
        result = list_directory("..", str(temp_workspace))
        assert "Error" in result
        assert "outside" in result.lower()


class TestDirectoryTree:
    """Tests for directory_tree function."""

    def test_directory_tree_success(self, temp_workspace):
        """Test generating a directory tree."""
        result = directory_tree(".", str(temp_workspace))

        # Parse JSON result
        tree = json.loads(result)
        assert isinstance(tree, list)
        assert len(tree) > 0

        # Check structure
        for entry in tree:
            assert "name" in entry
            assert "type" in entry
            assert entry["type"] in ["file", "directory"]

    def test_directory_tree_with_exclusions(self, temp_workspace):
        """Test tree generation with exclusion patterns."""
        result = directory_tree(".", str(temp_workspace), exclude_patterns=["*.png", "__pycache__"])

        tree = json.loads(result)

        # Verify PNG file is excluded
        all_names = self._collect_all_names(tree)
        assert "image.png" not in all_names

    def test_directory_tree_nonexistent(self, temp_workspace):
        """Test tree of non-existent directory."""
        result = directory_tree("missing", str(temp_workspace))
        assert "Error" in result
        assert "does not exist" in result

    def test_directory_tree_outside_working_dir(self, temp_workspace):
        """Test security: tree outside working directory."""
        result = directory_tree("..", str(temp_workspace))
        assert "Error" in result
        assert "outside" in result.lower()

    @staticmethod
    def _collect_all_names(tree):
        """Helper to collect all names in tree recursively."""
        names = []
        for entry in tree:
            names.append(entry["name"])
            if "children" in entry:
                names.extend(TestDirectoryTree._collect_all_names(entry["children"]))
        return names


class TestSearchFiles:
    """Tests for search_files function."""

    def test_search_files_success(self, temp_workspace):
        """Test searching for files by pattern."""
        result = search_files("*.py", str(temp_workspace))

        assert "main.py" in result
        assert "utils.py" in result

    def test_search_files_in_subdir(self, temp_workspace):
        """Test searching in a subdirectory."""
        result = search_files("*.txt", str(temp_workspace), path="subdir")

        assert "nested/deep.txt" in result
        # Should NOT include files from parent
        assert "test.txt" not in result

    def test_search_files_with_exclusions(self, temp_workspace):
        """Test searching with exclusion patterns."""
        result = search_files("*.txt", str(temp_workspace), exclude_patterns=["multiline.txt"])

        assert "test.txt" in result
        assert "multiline.txt" not in result

    def test_search_files_no_matches(self, temp_workspace):
        """Test searching with no matches."""
        result = search_files("*.xyz", str(temp_workspace))
        assert "No matches found" in result

    def test_search_files_nonexistent_dir(self, temp_workspace):
        """Test searching in non-existent directory."""
        result = search_files("*.txt", str(temp_workspace), path="missing")
        assert "Error" in result
        assert "does not exist" in result

    def test_search_files_outside_working_dir(self, temp_workspace):
        """Test security: searching outside working directory."""
        result = search_files("*.txt", str(temp_workspace), path="..")
        assert "Error" in result
        assert "outside" in result.lower()


class TestGetFileInfo:
    """Tests for get_file_info function."""

    def test_get_file_info_success(self, temp_workspace):
        """Test getting file information."""
        result = get_file_info("test.txt", str(temp_workspace))

        assert "name: test.txt" in result
        assert "size:" in result
        assert "type: file" in result
        assert "modified:" in result
        assert "accessed:" in result
        assert "permissions:" in result

    def test_get_file_info_directory(self, temp_workspace):
        """Test getting info for a directory."""
        result = get_file_info("subdir", str(temp_workspace))

        assert "name: subdir" in result
        assert "type: directory" in result

    def test_get_file_info_nonexistent(self, temp_workspace):
        """Test getting info for non-existent file."""
        result = get_file_info("missing.txt", str(temp_workspace))
        assert "Error" in result
        assert "does not exist" in result

    def test_get_file_info_outside_working_dir(self, temp_workspace):
        """Test security: getting info outside working directory."""
        result = get_file_info("../outside.txt", str(temp_workspace))
        assert "Error" in result
        assert "outside" in result.lower()


class TestFetchUrl:
    """Tests for fetch_url function."""

    @patch("agentic_data_scientist.tools.web_ops.requests.get")
    def test_fetch_url_success(self, mock_get):
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.text = "Success content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_url("https://example.com")

        assert result == "Success content"
        mock_get.assert_called_once()

    @patch("agentic_data_scientist.tools.web_ops.requests.get")
    def test_fetch_url_with_user_agent(self, mock_get):
        """Test fetch with custom user agent."""
        mock_response = Mock()
        mock_response.text = "Content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        _ = fetch_url("https://example.com", user_agent="TestBot/1.0")

        # Verify user agent was passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["User-Agent"] == "TestBot/1.0"

    @patch("agentic_data_scientist.tools.web_ops.requests.get")
    def test_fetch_url_timeout(self, mock_get):
        """Test fetch with timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        result = fetch_url("https://example.com", timeout=5)

        assert "Error" in result
        assert "timed out" in result

    @patch("agentic_data_scientist.tools.web_ops.requests.get")
    def test_fetch_url_connection_error(self, mock_get):
        """Test fetch with connection error."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = fetch_url("https://example.com")

        assert "Error" in result
        assert "connect" in result.lower()

    @patch("agentic_data_scientist.tools.web_ops.requests.get")
    def test_fetch_url_http_error(self, mock_get):
        """Test fetch with HTTP error."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_get.return_value = mock_response

        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        result = fetch_url("https://example.com/missing")

        assert "Error" in result
        assert "404" in result

    def test_fetch_url_invalid_scheme(self):
        """Test fetch with invalid URL scheme."""
        result = fetch_url("ftp://example.com")

        assert "Error" in result
        assert "HTTP" in result


class TestSecurityValidation:
    """Additional security-focused tests."""

    def test_symlink_escape_attempt(self, temp_workspace):
        """Test that symlinks cannot escape working directory."""
        # Create a symlink pointing outside
        outside_dir = temp_workspace.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        (outside_dir / "secret.txt").write_text("secret")

        symlink_path = temp_workspace / "escape_link"
        symlink_path.symlink_to(outside_dir / "secret.txt")

        # Attempting to read through symlink should fail
        result = read_file("escape_link", str(temp_workspace))
        # The symlink might resolve outside, which should be caught
        # or it might fail to read - either is acceptable
        assert "Error" in result or "secret" not in result

    def test_absolute_path_within_working_dir(self, temp_workspace):
        """Test that absolute paths within working dir are allowed."""
        test_file = temp_workspace / "test.txt"

        result = read_file(str(test_file), str(temp_workspace))

        # Should succeed since it's within working dir
        assert result == "Hello, world!"

    def test_dotdot_in_middle_of_path(self, temp_workspace):
        """Test path traversal in middle of valid path."""
        # Create subdir/test.txt
        (temp_workspace / "subdir" / "test.txt").write_text("subdir content")

        # Try to access via path traversal
        result = read_file("subdir/../test.txt", str(temp_workspace))

        # Should work as it resolves within working dir
        assert "Hello, world!" in result
