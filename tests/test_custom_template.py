"""Tests for CustomTemplateSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.custom_template import CustomTemplateSkill


@pytest.mark.asyncio
async def test_custom_template_generates(mock_config, mock_llm):
    """Test custom_template skill generates output"""
    skill = CustomTemplateSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_custom_template_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test custom_template writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = CustomTemplateSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "custom_template.md"
    assert output_file.exists()
