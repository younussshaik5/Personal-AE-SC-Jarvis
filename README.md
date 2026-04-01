# JARVIS MCP - Production-Ready Sales Intelligence Platform

**Enterprise-grade Model Context Protocol (MCP) server with 24 AI-powered sales intelligence skills.**

Fork-friendly. Production-ready. Deploy in 5 minutes.

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/your-org/jarvis-mcp.git
cd jarvis-mcp
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
pip install -e ".[dev]"
```

### 2. Run Tests
```bash
make test
```

### 3. Use in Claude Code
Add to MCP settings:
```json
{
  "name": "jarvis-mcp",
  "command": "python",
  "args": ["-m", "jarvis_mcp.mcp_server"]
}
```

## The 24 Skills

**Core Intelligence**
- Proposal, Battlecard, Demo Strategy, Risk Report, Value Architecture

**Discovery & Intelligence**
- Discovery, Competitive Intelligence, Meeting Prep, Meeting Summary, Conversation Analyzer

**Deal Management**
- MEDDPICC Tracker, Deal Stage Tracker, SOW Generator, Follow-up Email, Account Summary

**Technical & Advanced**
- Technical Risk, Competitor Pricing, Architecture Diagram, Documentation, HTML Generator, Conversation Extractor, Knowledge Builder, Quick Insights, Custom Template

## File Structure

```
jarvis-mcp/
├── jarvis_mcp/              # Main package (24 skills + core)
├── tests/                   # Complete test suite (24 tests)
├── examples/accounts/       # 3 example accounts
├── .github/workflows/       # CI/CD pipeline
├── setup.py
├── requirements.txt
├── Makefile
└── README.md
```

## Development

```bash
make setup      # Setup dev environment
make test       # Run tests
make test-cov   # Run with coverage
make format     # Format code (Black)
make lint       # Lint code (Flake8)
make type       # Type check (MyPy)
```

## Environment Configuration

Create `.env` from `.env.example`:

```bash
NVIDIA_API_KEY=your_nvidia_api_key
ACCOUNTS_ROOT=~/Documents/claude\ space/ACCOUNTS
MEMORY_ROOT=~/Documents/claude\ space/MEMORY
```

## Adding a New Account

1. Create account directory:
```bash
mkdir -p ~/Documents/claude\ space/ACCOUNTS/MyAccount
```

2. Add files:
```markdown
company_research.md  # Company info, tech stack, pain points
discovery.md         # MEDDPICC, call notes, next steps
deal_stage.json      # Stage, probability, timeline, stakeholders
```

3. Use in Claude Code:
```
@jarvis-mcp get_proposal account=MyAccount
@jarvis-mcp get_battlecard account=MyAccount
```

## Adding a New Skill

See CONTRIBUTING.md for complete step-by-step guide.

Quick version:
1. Create `jarvis_mcp/skills/my_skill.py` (inherit from BaseSkill)
2. Register in `jarvis_mcp/skills/__init__.py`
3. Create test in `tests/test_my_skill.py`
4. Run `make test`

## Documentation

- **README.md** - This file
- **CONTRIBUTING.md** - Developer guide
- **BUILD_SUMMARY.md** - What's included
- **examples/** - Example accounts with sample data

## License

MIT License

---

**Built with ❤️ for sales teams who deserve better tools.**

Fork it. Customize it. Own it.
