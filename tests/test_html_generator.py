"""Tests for HtmlGeneratorSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.html_generator import HtmlGeneratorSkill


@pytest.mark.asyncio
async def test_html_generator_generates(mock_config, mock_llm):
    """Test html_generator skill generates output"""
    skill = HtmlGeneratorSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_html_generator_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test html_generator writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = HtmlGeneratorSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "html_generator.md"
    assert output_file.exists()
