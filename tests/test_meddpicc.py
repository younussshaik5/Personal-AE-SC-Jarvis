"""Tests for MeddpiccSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.meddpicc import MeddpiccSkill


@pytest.mark.asyncio
async def test_meddpicc_generates(mock_config, mock_llm):
    """Test meddpicc skill generates output"""
    skill = MeddpiccSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_meddpicc_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test meddpicc writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = MeddpiccSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "meddpicc.md"
    assert output_file.exists()
