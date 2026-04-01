"""Tests for QuickInsightsSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.quick_insights import QuickInsightsSkill


@pytest.mark.asyncio
async def test_quick_insights_generates(mock_config, mock_llm):
    """Test quick_insights skill generates output"""
    skill = QuickInsightsSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_quick_insights_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test quick_insights writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = QuickInsightsSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "quick_insights.md"
    assert output_file.exists()
