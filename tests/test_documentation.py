"""Tests for DocumentationSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.documentation import DocumentationSkill


@pytest.mark.asyncio
async def test_documentation_generates(mock_config, mock_llm):
    """Test documentation skill generates output"""
    skill = DocumentationSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_documentation_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test documentation writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = DocumentationSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "documentation.md"
    assert output_file.exists()
