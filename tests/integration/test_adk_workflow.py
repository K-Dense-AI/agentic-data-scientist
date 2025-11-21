"""Integration tests for ADK workflow."""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
class TestADKWorkflow:
    """Test full ADK workflow integration."""

    def test_create_agent(self):
        """Test creating an ADK agent with local tools."""
        import tempfile

        from agentic_data_scientist.agents.adk import create_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = create_agent(working_dir=tmpdir)
            assert agent is not None
            assert agent.name == "agentic_data_scientist_workflow"

    def test_agent_has_sub_agents(self):
        """Test that created agent has proper sub-agents."""
        import tempfile

        from agentic_data_scientist.agents.adk import create_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = create_agent(working_dir=tmpdir)
            # SequentialAgent has sub_agents
            assert hasattr(agent, 'sub_agents')
            assert len(agent.sub_agents) == 4  # planning_loop, parser, orchestrator, summary

    def test_agent_with_tools_integration(self):
        """Test agent creation with local tools integration."""
        import tempfile

        from agentic_data_scientist.agents.adk import create_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = create_agent(working_dir=tmpdir)

            # Verify agent was created successfully
            assert agent is not None
            assert hasattr(agent, 'sub_agents')


@pytest.mark.asyncio
@pytest.mark.integration
class TestImplementationLoop:
    """Test implementation loop integration."""

    def test_make_implementation_agents(self):
        """Test creating implementation agents."""
        import tempfile

        from agentic_data_scientist.agents.adk.implementation_loop import make_implementation_agents

        with tempfile.TemporaryDirectory() as tmpdir:
            coding_agent, review_agent, review_confirmation = make_implementation_agents(tmpdir, [])

            assert coding_agent is not None
            assert review_agent is not None
            assert review_confirmation is not None
            assert coding_agent.name == "coding_agent"
            assert review_agent.name == "review_agent"

    def test_coding_agent_is_claude_code(self):
        """Test that coding agent is always ClaudeCodeAgent."""
        import tempfile

        from agentic_data_scientist.agents.adk.implementation_loop import make_implementation_agents
        from agentic_data_scientist.agents.claude_code import ClaudeCodeAgent

        with tempfile.TemporaryDirectory() as tmpdir:
            coding_agent, review_agent, review_confirmation = make_implementation_agents(tmpdir, [])

            assert isinstance(coding_agent, ClaudeCodeAgent)
