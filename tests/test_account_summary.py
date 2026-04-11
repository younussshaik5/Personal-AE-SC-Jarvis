"""Tests for AccountSummarySkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.account_summary import AccountSummarySkill


@pytest.mark.asyncio
async def test_account_summary_generates(mock_config, mock_llm):
    """Test account_summary skill generates output"""
    skill = AccountSummarySkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_account_summary_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test account_summary writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = AccountSummarySkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "account_summary.md"
    assert output_file.exists()
