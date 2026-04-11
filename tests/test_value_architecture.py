"""Tests for ValueArchitectureSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.value_architecture import ValueArchitectureSkill


@pytest.mark.asyncio
async def test_value_architecture_generates(mock_config, mock_llm):
    """Test value_architecture skill generates output"""
    skill = ValueArchitectureSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_value_architecture_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test value_architecture writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = ValueArchitectureSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "value_architecture.md"
    assert output_file.exists()
