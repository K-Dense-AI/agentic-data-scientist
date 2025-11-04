"""Integration tests for Claude Code agent."""

from unittest.mock import Mock, patch

import pytest

from agentic_data_scientist.agents.claude_code import ClaudeCodeAgent


@pytest.mark.asyncio
@pytest.mark.integration
class TestClaudeCodeIntegration:
    """Test Claude Code agent integration."""

    def test_agent_initialization_with_mcp(self):
        """Test that Claude Code agent initializes with MCP configuration."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ClaudeCodeAgent(
                working_dir=tmpdir,
                model="claude-sonnet-4-5-latest",
            )

            assert agent.working_dir == tmpdir
            assert agent.model == "claude-sonnet-4-5-latest"

    @patch('agentic_data_scientist.agents.claude_code.agent.query')
    @patch('agentic_data_scientist.agents.claude_code.agent.ClaudeAgentOptions')
    async def test_claude_agent_options_include_mcp(self, mock_options_class, mock_query):
        """Test that ClaudeAgentOptions includes MCP server configuration."""
        import tempfile

        from google.adk.agents import InvocationContext
        from google.adk.sessions import InMemorySession

        # Mock query to return an empty async generator
        async def mock_generator(*args, **kwargs):
            # Yield a ResultMessage to complete
            result_msg = Mock()
            result_msg.subtype = 'success'
            type(result_msg).__name__ = 'ResultMessage'
            yield result_msg

        mock_query.return_value = mock_generator()

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ClaudeCodeAgent(working_dir=tmpdir)

            # Create a mock context
            session = InMemorySession(
                app_name="test",
                user_id="test_user",
                session_id="test_session",
            )
            session.state["implementation_task"] = "Test task"

            ctx = InvocationContext(session=session)

            # Run the agent
            events = []
            async for event in agent._run_async_impl(ctx):
                events.append(event)

            # Verify ClaudeAgentOptions was called with mcp_servers
            assert mock_options_class.called
            call_kwargs = mock_options_class.call_args[1]
            assert 'mcp_servers' in call_kwargs
            assert 'claude-scientific-skills' in call_kwargs['mcp_servers']
            assert 'url' in call_kwargs['mcp_servers']['claude-scientific-skills']
