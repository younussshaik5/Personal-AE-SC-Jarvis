"""Tests for ArchitectureDiagramSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.architecture_diagram import ArchitectureDiagramSkill


@pytest.mark.asyncio
async def test_architecture_diagram_generates(mock_config, mock_llm):
    """Test architecture_diagram skill generates output"""
    skill = ArchitectureDiagramSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_architecture_diagram_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test architecture_diagram writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = ArchitectureDiagramSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "architecture_diagram.md"
    assert output_file.exists()
