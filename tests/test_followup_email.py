"""Tests for FollowupEmailSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.followup_email import FollowupEmailSkill


@pytest.mark.asyncio
async def test_followup_email_generates(mock_config, mock_llm):
    """Test followup_email skill generates output"""
    skill = FollowupEmailSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_followup_email_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test followup_email writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = FollowupEmailSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "followup_email.md"
    assert output_file.exists()
