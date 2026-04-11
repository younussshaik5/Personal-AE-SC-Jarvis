"""Tests for MeetingPrepSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.meeting_prep import MeetingPrepSkill


@pytest.mark.asyncio
async def test_meeting_prep_generates(mock_config, mock_llm):
    """Test meeting_prep skill generates output"""
    skill = MeetingPrepSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_meeting_prep_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test meeting_prep writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = MeetingPrepSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "meeting_prep.md"
    assert output_file.exists()
