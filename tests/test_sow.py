"""Tests for SowSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.sow import SowSkill


@pytest.mark.asyncio
async def test_sow_generates(mock_config, mock_llm):
    """Test sow skill generates output"""
    skill = SowSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_sow_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test sow writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = SowSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "sow.md"
    assert output_file.exists()
