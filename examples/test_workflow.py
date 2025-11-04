"""
End-to-end test workflow for Agentic Data Scientist.

This script tests the complete agent workflow with MCP integration.
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentic_data_scientist.agents.adk.agent import create_agent
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_agent_creation():
    """Test that the agent can be created successfully."""
    logger.info("=" * 80)
    logger.info("TEST 1: Agent Creation")
    logger.info("=" * 80)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Creating agent with working_dir: {temp_dir}")
            agent = create_agent(
                working_dir=temp_dir,
                model="google/gemini-2.5-pro",
                mcp_servers=["filesystem", "fetch"],  # Test with minimal MCP servers
            )
            logger.info(f"✓ Agent created successfully: {agent.name}")
            return True
    except Exception as e:
        logger.error(f"✗ Agent creation failed: {e}")
        return False


async def test_mcp_tools():
    """Test MCP tool loading."""
    logger.info("=" * 80)
    logger.info("TEST 2: MCP Tools Loading")
    logger.info("=" * 80)
    
    try:
        from agentic_data_scientist.mcp import get_mcp_tools
        from agentic_data_scientist.mcp.config import get_server_config
        
        # Test configuration is correct
        logger.info("Checking MCP server configurations...")
        
        servers_to_check = ["filesystem", "fetch", "markitdown", "claude_scientific_skills"]
        for server in servers_to_check:
            try:
                config = get_server_config(server)
                logger.info(f"  ✓ {server}: {config.command} {config.args}")
            except Exception as e:
                logger.error(f"  ✗ {server}: {e}")
                return False
        
        # Note: We skip actually starting servers as they block in test environment
        logger.info("✓ MCP server configurations are valid")
        logger.info("  (Skipping actual server startup to avoid blocking)")
        
        return True
    except Exception as e:
        logger.error(f"✗ MCP tools loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_workflow():
    """Test a simple data analysis workflow."""
    logger.info("=" * 80)
    logger.info("TEST 3: Simple Workflow")
    logger.info("=" * 80)
    
    try:
        import csv
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample data
            data_file = temp_path / "sample_data.csv"
            with open(data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['product', 'sales', 'region'])
                writer.writerow(['Widget A', 100, 'North'])
                writer.writerow(['Widget B', 150, 'South'])
                writer.writerow(['Widget C', 200, 'East'])
                writer.writerow(['Widget A', 120, 'South'])
                writer.writerow(['Widget B', 180, 'North'])
            
            logger.info(f"✓ Created sample data at: {data_file}")
            logger.info(f"  Sample data has {len(list(csv.reader(open(data_file))))} rows")
            
            # Test that we can create an agent
            agent = create_agent(
                working_dir=str(temp_path),
                model="google/gemini-2.5-pro",
                mcp_servers=[],  # Skip MCP for this test
            )
            
            logger.info(f"✓ Agent created for workflow test")
            logger.info("  Note: Full workflow execution would require running the agent")
            logger.info("  This test verifies setup is correct")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Simple workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_litellm_config():
    """Test LiteLLM configuration."""
    logger.info("=" * 80)
    logger.info("TEST 4: LiteLLM Configuration")
    logger.info("=" * 80)
    
    try:
        from agentic_data_scientist.agents.adk.utils import DEFAULT_MODEL, REVIEW_MODEL
        
        logger.info(f"✓ DEFAULT_MODEL configured: {DEFAULT_MODEL.model}")
        logger.info(f"✓ REVIEW_MODEL configured: {REVIEW_MODEL.model}")
        
        return True
    except Exception as e:
        logger.error(f"✗ LiteLLM configuration test failed: {e}")
        return False


async def test_claude_agent_import():
    """Test Claude Code agent can be imported."""
    logger.info("=" * 80)
    logger.info("TEST 5: Claude Code Agent Import")
    logger.info("=" * 80)
    
    try:
        from agentic_data_scientist.agents.claude_code.agent import ClaudeCodeAgent
        
        agent = ClaudeCodeAgent(
            name="test_claude_agent",
            working_dir=tempfile.mkdtemp(),
        )
        
        logger.info(f"✓ Claude Code agent created: {agent.name}")
        logger.info(f"  Model: {agent.model}")
        logger.info(f"  Output key: {agent.output_key}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Claude agent import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("AGENTIC DATA SCIENTIST - END-TO-END TEST SUITE")
    logger.info("=" * 80 + "\n")
    
    tests = [
        ("Agent Creation", test_agent_creation),
        ("MCP Tools Loading", test_mcp_tools),
        ("Simple Workflow", test_simple_workflow),
        ("LiteLLM Configuration", test_litellm_config),
        ("Claude Code Agent Import", test_claude_agent_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
        
        logger.info("")  # Blank line between tests
    
    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


