"""
Unit tests for the agent generator module.
"""
import pytest
from unittest.mock import patch
import sys
import os

# Add the mocks directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mocks')))

# Patch the agents module
with patch.dict('sys.modules', {'agents': __import__('tests.mocks.agents', fromlist=['Agent', 'Runner'])}):
    from meta_agent.core import generate_agent
    from meta_agent.models import AgentImplementation


@pytest.mark.asyncio
async def test_generate_agent_basic():
    """Test that the generate_agent function works with basic input."""
    result = await generate_agent("Name: TestAgent\nInstructions: Test instructions")

    assert result is not None
    assert result.main_file is not None
    assert "TestAgent" in result.main_file
    assert result.installation_instructions is not None
    assert result.usage_examples is not None


@pytest.mark.asyncio
async def test_generate_agent_empty_specification():
    """Test that the generate_agent function raises an error with empty input."""
    with pytest.raises(ValueError, match="Agent specification cannot be empty"):
        await generate_agent("")
