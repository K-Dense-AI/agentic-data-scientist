"""Integration tests for ADK workflow."""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
class TestADKWorkflow:
    """Test full ADK workflow integration."""

    @patch('agentic_data_scientist.mcp.get_mcp_toolsets')
    def test_create_agent(self, mock_toolsets):
        """Test creating an ADK agent with MCP toolsets."""
        import tempfile

        from agentic_data_scientist.agents.adk import create_agent

        mock_toolsets.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = create_agent(working_dir=tmpdir)
            assert agent is not None
            assert agent.name == "agentic_data_scientist_workflow"

    @patch('agentic_data_scientist.mcp.get_mcp_toolsets')
    def test_agent_has_sub_agents(self, mock_toolsets):
        """Test that created agent has proper sub-agents."""
        import tempfile

        from agentic_data_scientist.agents.adk import create_agent

        mock_toolsets.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = create_agent(working_dir=tmpdir)
            # SequentialAgent has sub_agents
            assert hasattr(agent, 'sub_agents')
            assert len(agent.sub_agents) == 4  # root, generator, planning_loop, summary

    @patch('agentic_data_scientist.mcp.config.McpToolset')
    @patch('agentic_data_scientist.mcp.get_mcp_toolsets')
    def test_agent_with_mcp_integration(self, mock_get_toolsets, mock_toolset_class):
        """Test agent creation with MCP toolset integration."""
        import tempfile

        from agentic_data_scientist.agents.adk import create_agent

        # Mock toolsets
        mock_toolset = Mock()
        mock_get_toolsets.return_value = [mock_toolset]

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = create_agent(working_dir=tmpdir)  # noqa: F841

            # Verify get_mcp_toolsets was called
            mock_get_toolsets.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
class TestImplementationLoop:
    """Test implementation loop integration."""

    def test_make_implementation_agents(self):
        """Test creating implementation agents."""
        import tempfile

        from agentic_data_scientist.agents.adk.implementation_loop import make_implementation_agents

        with tempfile.TemporaryDirectory() as tmpdir:
            coding_agent, review_agent = make_implementation_agents(tmpdir, [])

            assert coding_agent is not None
            assert review_agent is not None
            assert coding_agent.name == "coding_agent"
            assert review_agent.name == "review_agent"

    def test_coding_agent_is_claude_code(self):
        """Test that coding agent is always ClaudeCodeAgent."""
        import tempfile

        from agentic_data_scientist.agents.adk.implementation_loop import make_implementation_agents
        from agentic_data_scientist.agents.claude_code import ClaudeCodeAgent

        with tempfile.TemporaryDirectory() as tmpdir:
            coding_agent, review_agent = make_implementation_agents(tmpdir, [])

            assert isinstance(coding_agent, ClaudeCodeAgent)
