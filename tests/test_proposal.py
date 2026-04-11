"""Tests for ProposalSkill"""

import pytest
from pathlib import Path
from jarvis_mcp.skills.proposal import ProposalSkill


@pytest.mark.asyncio
async def test_proposal_generates(mock_config, mock_llm):
    """Test proposal skill generates output"""
    skill = ProposalSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0
    assert "# " in result or "#" in result  # Markdown


@pytest.mark.asyncio
async def test_proposal_writes_file(mock_config, mock_llm, temp_accounts_dir):
    """Test proposal writes output file"""
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = ProposalSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")

    output_file = temp_accounts_dir / "TestCorp" / "proposal.md"
    assert output_file.exists()
