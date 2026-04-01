"""Tests for BattlecardSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.battlecard import BattlecardSkill


@pytest.mark.asyncio
async def test_battlecard_generates(mock_config, mock_llm):
    """Test battlecard skill generates output"""
    skill = BattlecardSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_battlecard_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test battlecard writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = BattlecardSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "battlecard.md"
    assert output_file.exists()
