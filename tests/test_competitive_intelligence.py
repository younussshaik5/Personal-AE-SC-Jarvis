"""Tests for CompetitiveIntelligenceSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.competitive_intelligence import CompetitiveIntelligenceSkill


@pytest.mark.asyncio
async def test_competitive_intelligence_generates(mock_config, mock_llm):
    """Test competitive_intelligence skill generates output"""
    skill = CompetitiveIntelligenceSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_competitive_intelligence_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test competitive_intelligence writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = CompetitiveIntelligenceSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "competitive_intelligence.md"
    assert output_file.exists()
