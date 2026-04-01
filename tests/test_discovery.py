"""Tests for DiscoverySkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.discovery import DiscoverySkill


@pytest.mark.asyncio
async def test_discovery_generates(mock_config, mock_llm):
    """Test discovery skill generates output"""
    skill = DiscoverySkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_discovery_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test discovery writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = DiscoverySkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "discovery.md"
    assert output_file.exists()
