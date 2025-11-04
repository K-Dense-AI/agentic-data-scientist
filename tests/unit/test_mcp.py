"""Unit tests for MCP configuration and registry."""

from unittest.mock import Mock, patch

from agentic_data_scientist.mcp.config import (
    filesystem_tool_filter,
    get_claude_scientific_skills_toolset,
    get_default_mcp_toolsets,
    get_fetch_toolset,
    get_filesystem_toolset,
)


class TestFilesystemToolFilter:
    """Test filesystem tool filter."""

    def test_allow_read_operations(self):
        """Test that read operations are allowed."""
        allowed_tools = [
            "read_file",
            "read_multiple_files",
            "list_directory",
            "search_files",
            "get_file_info",
            "list_allowed_directories",
        ]

        for tool_name in allowed_tools:
            tool = Mock()
            tool.name = tool_name
            assert filesystem_tool_filter(tool) is True

    def test_deny_write_operations(self):
        """Test that write operations are denied."""
        denied_tools = [
            "write_file",
            "create_directory",
            "move_file",
            "delete_file",
            "edit_file",
        ]

        for tool_name in denied_tools:
            tool = Mock()
            tool.name = tool_name
            assert filesystem_tool_filter(tool) is False


class TestMCPToolsetGetters:
    """Test MCP toolset getter functions."""

    @patch('agentic_data_scientist.mcp.config.McpToolset')
    def test_get_filesystem_toolset_default(self, mock_toolset):
        """Test filesystem toolset with default directory."""
        get_filesystem_toolset()
        mock_toolset.assert_called_once()
        # Verify tool_filter is passed
        call_kwargs = mock_toolset.call_args[1]
        assert call_kwargs['tool_filter'] is filesystem_tool_filter

    @patch('agentic_data_scientist.mcp.config.McpToolset')
    def test_get_filesystem_toolset_custom(self, mock_toolset):
        """Test filesystem toolset with custom directory."""
        get_filesystem_toolset(working_dir="/custom/path")
        mock_toolset.assert_called_once()

    @patch('agentic_data_scientist.mcp.config.McpToolset')
    def test_get_fetch_toolset(self, mock_toolset):
        """Test fetch toolset."""
        get_fetch_toolset()
        mock_toolset.assert_called_once()

    @patch('agentic_data_scientist.mcp.config.McpToolset')
    def test_get_claude_scientific_skills_toolset(self, mock_toolset):
        """Test Claude Scientific Skills toolset."""
        get_claude_scientific_skills_toolset()
        mock_toolset.assert_called_once()

    @patch('agentic_data_scientist.mcp.config.get_filesystem_toolset')
    @patch('agentic_data_scientist.mcp.config.get_fetch_toolset')
    @patch('agentic_data_scientist.mcp.config.get_claude_scientific_skills_toolset')
    def test_get_default_mcp_toolsets(self, mock_css, mock_fetch, mock_fs):
        """Test getting default MCP toolsets."""
        mock_fs.return_value = Mock()
        mock_fetch.return_value = Mock()
        mock_css.return_value = Mock()

        toolsets = get_default_mcp_toolsets()

        assert len(toolsets) == 3
        mock_fs.assert_called_once()
        mock_fetch.assert_called_once()
        mock_css.assert_called_once()

    @patch('agentic_data_scientist.mcp.config.get_filesystem_toolset')
    @patch('agentic_data_scientist.mcp.config.get_fetch_toolset')
    @patch('agentic_data_scientist.mcp.config.get_claude_scientific_skills_toolset')
    def test_get_default_mcp_toolsets_with_working_dir(self, mock_css, mock_fetch, mock_fs):
        """Test getting default MCP toolsets with custom working directory."""
        mock_fs.return_value = Mock()
        mock_fetch.return_value = Mock()
        mock_css.return_value = Mock()

        toolsets = get_default_mcp_toolsets(working_dir="/custom/path")

        assert len(toolsets) == 3
        mock_fs.assert_called_once_with("/custom/path")
