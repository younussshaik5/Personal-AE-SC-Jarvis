# Contributing to JARVIS MCP

Thank you for contributing! This guide will help you add new skills and improve the project.

## Quick Start

1. **Setup Dev Environment**
```bash
git clone https://github.com/your-org/jarvis-mcp.git
cd jarvis-mcp
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

2. **Create a Branch**
```bash
git checkout -b feature/my-new-skill
```

3. **Code, Test, Commit**
```bash
make format  # Black
make lint    # Flake8
make test    # Pytest
git commit -m "Add new skill: my_skill"
git push origin feature/my-new-skill
```

## Adding a New Skill

### 1. Create Skill File
`jarvis_mcp/skills/my_skill.py`:

```python
"""My Skill - Brief description"""

from jarvis_mcp.skills.base_skill import BaseSkill


class MySkillSkill(BaseSkill):
    """Detailed description"""

    async def generate(self, account_name: str, **kwargs) -> str:
        # Read context
        context = await self.read_account_files(account_name)

        # Build prompt
        prompt = f"""Generate [your skill] for {account_name}.

Account Context:
- Company: {context.get('company_research', '')[:500]}...
- Discovery: {context.get('discovery', '')[:500]}...

Create [detailed instructions]."""

        # Call NVIDIA (choose: text, reasoning, long_context, audio, code, quick)
        response = await self.llm.generate(
            model_type="text",
            prompt=prompt,
            context={"account": account_name},
            max_tokens=3000,
        )

        # Write output
        await self.write_output(account_name, "my_skill.md", response)
        return response
```

### 2. Register Skill
Edit `jarvis_mcp/skills/__init__.py`:

```python
from .my_skill import MySkillSkill

__all__ = [..., "MySkillSkill"]

SKILL_REGISTRY = {
    ...
    "my_skill": MySkillSkill,
}
```

### 3. Create Test
`tests/test_my_skill.py`:

```python
import pytest
from jarvis_mcp.skills.my_skill import MySkillSkill


@pytest.mark.asyncio
async def test_my_skill_generates(mock_config, mock_llm):
    skill = MySkillSkill(mock_llm, mock_config)
    result = await skill.generate("TestCorp")
    assert len(result) > 0


@pytest.mark.asyncio
async def test_my_skill_writes_file(mock_config, mock_llm, temp_accounts_dir):
    mock_config.ACCOUNTS_ROOT = temp_accounts_dir
    skill = MySkillSkill(mock_llm, mock_config)
    await skill.generate("TestCorp")
    
    output_file = temp_accounts_dir / "TestCorp" / "my_skill.md"
    assert output_file.exists()
```

### 4. Run Tests
```bash
make test
```

## Code Style

### Naming
- Skill classes: `PascalCase` + `Skill` suffix → `MySkillSkill`
- Skill files: `snake_case` → `my_skill.py`
- Functions: `snake_case` → `generate()`

### Formatting
```bash
make format  # Black (auto)
make lint    # Flake8 (check)
```

## Testing

```bash
# All tests
make test

# Specific test
pytest tests/test_my_skill.py -v

# With coverage
make test-cov
```

Minimum 80% coverage required.

## Commit Messages

Follow conventional commits:
```
feat(skills): add new skill name

Description of what was added.

Closes #123
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Pull Request Checklist

- [ ] Code follows style guide
- [ ] Tests pass (`make test`)
- [ ] New tests added
- [ ] Code coverage maintained
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Commit messages descriptive

## Questions?

- Check existing skills: `jarvis_mcp/skills/`
- Review tests: `tests/test_*.py`
- Look at examples: `examples/accounts/`

---

**Thank you for contributing to JARVIS MCP! 🚀**
