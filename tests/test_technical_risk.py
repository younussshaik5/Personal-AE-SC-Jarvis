"""Tests for TechnicalRiskSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.technical_risk import TechnicalRiskSkill


@pytest.mark.asyncio
async def test_technical_risk_generates(mock_config, mock_llm):
    """Test technical_risk skill generates output"""
    skill = TechnicalRiskSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_technical_risk_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test technical_risk writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = TechnicalRiskSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "technical_risk.md"
    assert output_file.exists()
