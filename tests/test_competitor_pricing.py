"""Tests for CompetitorPricingSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.competitor_pricing import CompetitorPricingSkill


@pytest.mark.asyncio
async def test_competitor_pricing_generates(mock_config, mock_llm):
    """Test competitor_pricing skill generates output"""
    skill = CompetitorPricingSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_competitor_pricing_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test competitor_pricing writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = CompetitorPricingSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "competitor_pricing.md"
    assert output_file.exists()
