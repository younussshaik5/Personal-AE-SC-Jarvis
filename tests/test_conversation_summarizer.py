"""Tests for ConversationSummarizerSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.conversation_summarizer import ConversationSummarizerSkill


@pytest.mark.asyncio
async def test_conversation_summarizer_generates(mock_config, mock_llm):
    """Test conversation_summarizer skill generates output"""
    skill = ConversationSummarizerSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_conversation_summarizer_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test conversation_summarizer writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = ConversationSummarizerSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "conversation_summarizer.md"
    assert output_file.exists()
