"""Tests for DealStageTrackerSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.deal_stage_tracker import DealStageTrackerSkill


@pytest.mark.asyncio
async def test_deal_stage_tracker_generates(mock_config, mock_llm):
    """Test deal_stage_tracker skill generates output"""
    skill = DealStageTrackerSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_deal_stage_tracker_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test deal_stage_tracker writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = DealStageTrackerSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "deal_stage_tracker.md"
    assert output_file.exists()
