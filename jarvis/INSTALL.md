# JARVIS Installation & Setup Guide

## System Requirements

- **Python 3.11+** (for JARVIS core)
- **Node.js 18+** (for MCP Observer)
- Workspace: `/path/to/your/workspace`

## Installation

### 1. Install Python Package

```bash
cd ~/Documents/OPENCODE\ SPACE
pip install -e jarvis
```

### 2. Build MCP Observer (if not already built)

```bash
cd mcp-opencode-observer
npm install
npm run build
cd ..
```

### 3. Configure JARVIS

Edit `jarvis/config/jarvis.yaml`:

```yaml
workspace_root: /path/to/your/workspace
solution_engineer:
  name: YOUR_NAME
  title: Solution Engineer at Yellow.ai

llm:
  provider: openai
  api_key: "your-nvidia-or-openai-key"
  base_url: "https://integrate.api.nvidia.com/v1"
  model: "stepfun-ai/step-3.5-flash"
```

### 4. Launch

```bash
./fireup_jarvis.sh
```

This starts:
- MCP Observer (Node.js) – polls OpenCode and Claude conversations
- JARVIS Core (Python) – orchestrator + all skills
- UI Dashboard – http://localhost:8080

## Verification

After launch, check:

```bash
# Are processes running?
ps aux | grep -E "mcp-opencode-observer|jarvis.core.orchestrator"

# Check logs
tail -f logs/jarvis.log

# Open dashboard
open http://localhost:8080
```

## Directory Structure After Setup

```
~/Documents/OPENCODE SPACE/
├── fireup_jarvis.sh            # One-command startup
├── ACCOUNTS/                   # Your accounts & opportunities
├── MEMORY/                     # Cross-account knowledge base
├── jarvis/                     # Python core package
│   ├── core/orchestrator.py    # Central coordinator
│   ├── skills/                 # 15+ document generation skills
│   ├── observers/              # FS & conversation monitors
│   ├── utils/                  # Event bus & utilities
│   ├── ui/server.py            # Dashboard backend
│   └── config/jarvis.yaml      # Main configuration
├── mcp-opencode-observer/      # Node.js MCP bridge
├── persona/                    # Role-specific configs
├── docs/                       # Extended documentation
└── logs/                       # Runtime logs
```

## Common Issues

**JARVIS core fails to start:**
- Check Python version: `python3 --version` (need 3.11+)
- Check logs: `tail -f logs/jarvis.log`
- Re-install: `pip install -e jarvis`

**MCP Observer fails:**
- Check Node.js: `node --version` (need 18+)
- Rebuild: `cd mcp-opencode-observer && npm run build`
- Check logs: `tail -f logs/mcp_observer.log`

**No documents generating:**
- Ensure account folder exists under `ACCOUNTS/`
- Add at least a `notes.json` file
- Wait up to 60 seconds for the next poll cycle
- Check skill logs: `ls logs/skill.*.jsonl`

**LLM synthesis not working:**
- Verify API key in `jarvis/config/jarvis.yaml`
- System automatically falls back to rule-based generation

## Uninstall

```bash
# Stop all JARVIS processes
pkill -f "jarvis.core.orchestrator"
pkill -f "mcp-opencode-observer"

# Uninstall Python package
pip uninstall jarvis
```

---

**Next:** See [JARVIS Quickstart](docs/getting-started/JARVIS_QUICKSTART.md) for usage details.