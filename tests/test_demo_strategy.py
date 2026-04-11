"""Tests for DemoStrategySkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.demo_strategy import DemoStrategySkill


@pytest.mark.asyncio
async def test_demo_strategy_generates(mock_config, mock_llm):
    """Test demo_strategy skill generates output"""
    skill = DemoStrategySkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_demo_strategy_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test demo_strategy writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = DemoStrategySkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "demo_strategy.md"
    assert output_file.exists()
