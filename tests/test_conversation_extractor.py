"""Tests for ConversationExtractorSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.conversation_extractor import ConversationExtractorSkill


@pytest.mark.asyncio
async def test_conversation_extractor_generates(mock_config, mock_llm):
    """Test conversation_extractor skill generates output"""
    skill = ConversationExtractorSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_conversation_extractor_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test conversation_extractor writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = ConversationExtractorSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "conversation_extractor.md"
    assert output_file.exists()
