"""Integration tests for MCP server connections."""

from unittest.mock import Mock, patch

import pytest

from agentic_data_scientist.mcp.config import (
    get_claude_scientific_skills_toolset,
    get_fetch_toolset,
    get_filesystem_toolset,
)
from agentic_data_scientist.mcp.registry import get_mcp_toolsets


@pytest.mark.integration
class TestMCPIntegration:
    """Test MCP integration."""

    @patch('agentic_data_scientist.mcp.config.MCPToolset')
    def test_filesystem_toolset_with_read_only_filter(self, mock_toolset_class):
        """Test filesystem toolset is configured with read-only filter."""
        from agentic_data_scientist.mcp.config import filesystem_tool_filter

        mock_toolset = Mock()
        mock_toolset_class.return_value = mock_toolset

        toolset = get_filesystem_toolset("/tmp") # noqa: F841

        mock_toolset_class.assert_called_once()
        call_kwargs = mock_toolset_class.call_args[1]
        assert call_kwargs['tool_filter'] is filesystem_tool_filter

    @patch('agentic_data_scientist.mcp.config.MCPToolset')
    def test_fetch_toolset_configuration(self, mock_toolset_class):
        """Test fetch toolset configuration."""
        mock_toolset = Mock()
        mock_toolset_class.return_value = mock_toolset

        toolset = get_fetch_toolset() # noqa: F841

        mock_toolset_class.assert_called_once()

    @patch('agentic_data_scientist.mcp.config.MCPToolset')
    def test_claude_scientific_skills_sse_connection(self, mock_toolset_class):
        """Test Claude Scientific Skills uses SSE connection."""
        mock_toolset = Mock()
        mock_toolset_class.return_value = mock_toolset

        toolset = get_claude_scientific_skills_toolset() # noqa: F841

        mock_toolset_class.assert_called_once()
        # Verify SSE connection params were created
        assert mock_toolset_class.create_sse_connection_params.called

    @patch('agentic_data_scientist.mcp.config.get_default_mcp_toolsets')
    def test_get_mcp_toolsets_returns_list(self, mock_get_default):
        """Test get_mcp_toolsets returns a list of toolsets."""
        mock_toolset1 = Mock()
        mock_toolset2 = Mock()
        mock_toolset3 = Mock()
        mock_get_default.return_value = [mock_toolset1, mock_toolset2, mock_toolset3]

        toolsets = get_mcp_toolsets()

        assert isinstance(toolsets, list)
        assert len(toolsets) == 3

    @patch('agentic_data_scientist.mcp.config.get_default_mcp_toolsets')
    def test_get_mcp_toolsets_handles_errors(self, mock_get_default):
        """Test get_mcp_toolsets handles errors gracefully."""
        mock_get_default.side_effect = Exception("Connection failed")

        toolsets = get_mcp_toolsets()

        # Should return empty list on error
        assert toolsets == []


@pytest.mark.integration
class TestToolFilter:
    """Test MCP tool filtering."""

    def test_read_only_filter_allows_reads(self):
        """Test that read-only filter allows read operations."""
        from agentic_data_scientist.mcp.config import filesystem_tool_filter

        read_tool = Mock()
        read_tool.name = "read_file"
        assert filesystem_tool_filter(read_tool) is True

        list_tool = Mock()
        list_tool.name = "list_directory"
        assert filesystem_tool_filter(list_tool) is True

        search_tool = Mock()
        search_tool.name = "search_files"
        assert filesystem_tool_filter(search_tool) is True

    def test_read_only_filter_blocks_writes(self):
        """Test that read-only filter blocks write operations."""
        from agentic_data_scientist.mcp.config import filesystem_tool_filter

        write_tool = Mock()
        write_tool.name = "write_file"
        assert filesystem_tool_filter(write_tool) is False

        delete_tool = Mock()
        delete_tool.name = "delete_file"
        assert filesystem_tool_filter(delete_tool) is False

        edit_tool = Mock()
        edit_tool.name = "edit_file"
        assert filesystem_tool_filter(edit_tool) is False
