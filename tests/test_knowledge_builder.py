"""Tests for KnowledgeBuilderSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.knowledge_builder import KnowledgeBuilderSkill


@pytest.mark.asyncio
async def test_knowledge_builder_generates(mock_config, mock_llm):
    """Test knowledge_builder skill generates output"""
    skill = KnowledgeBuilderSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_knowledge_builder_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test knowledge_builder writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = KnowledgeBuilderSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "knowledge_builder.md"
    assert output_file.exists()
