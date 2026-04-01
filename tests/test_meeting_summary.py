"""Tests for MeetingSummarySkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.meeting_summary import MeetingSummarySkill


@pytest.mark.asyncio
async def test_meeting_summary_generates(mock_config, mock_llm):
    """Test meeting_summary skill generates output"""
    skill = MeetingSummarySkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_meeting_summary_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test meeting_summary writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = MeetingSummarySkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "meeting_summary.md"
    assert output_file.exists()
