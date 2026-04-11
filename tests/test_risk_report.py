"""Tests for RiskReportSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.risk_report import RiskReportSkill


@pytest.mark.asyncio
async def test_risk_report_generates(mock_config, mock_llm):
    """Test risk_report skill generates output"""
    skill = RiskReportSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_risk_report_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test risk_report writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = RiskReportSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "risk_report.md"
    assert output_file.exists()
