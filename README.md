# JARVIS - Autonomous AI Employee (Presales Template)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **Welcome to the JARVIS Open-Source Template!**  
> This is a fully functional, self-evolving AI assistant designed specifically for Presales, Solution Engineers, and Account Executives. Fork this repository to run your own autonomous employee locally.

---

> [!IMPORTANT]
> **Just Forked?** Read the [FORK_GUIDE.md](FORK_GUIDE.md) for setup instructions and AI prompts to get JARVIS running in your local environment.

---

## What is JARVIS?

JARVIS is an autonomous AI employee that **continuously learns** from your OpenCode/claude code conversations and file system, automatically generating professional sales engineering documents for every opportunity—zero manual effort required.

### ✨ Features

- **Zero-Config Sync** – Works from any subfolder; automatically detects all sessions in workspace
- **Real-Time Updates** – All documents refresh within 60 seconds of any change
- **LLM-Enhanced Synthesis** – Uses OpenAI/Anthropic/NVIDIA to synthesize high-level insights
- **Comprehensive Skill Suite** – Automated Risk, Discovery, MEDDPICC, ROI, Battlecards, and more
- **Interactive Dashboards** – Master HTML view with exports (PDF, Word, Excel)
- **Multi-Persona Awareness** – Tailors behavior for Solution Consultants, AEs, etc.
- **Fully Interlinked** – Risk assessments and discovery docs all cross-reference each other

---

## 📁 Generated Documents (Per Account)

Each opportunity under `ACCOUNTS/<team>/<Account Name>/` gets an automated intelligence suite:

```
├── DASHBOARD.html                 ← Master CRM-style view with exports
├── TECHNICAL_RISK_ASSESSMENT.md   ← LLM-synthesized risk analysis
├── discovery/
│   ├── internal_discovery.md      ← Deep technical dive
│   ├── final_discovery.md         ← Handoff summary
│   └── Q2A.md                     ← Questions to answer
├── meddpicc/
│   ├── qualification_report.md    ← MEDDPICC analysis
│   └── stakeholder_analysis.md    ← MAP/Champion tracking
├── battlecards/
│   ├── competitive_intel.md       ← Competitor deep-dives
│   └── pricing_comparison.md      ← Pricing vs market
├── value_architecture/
│   ├── roi_model.md               ← Financial impact analysis
│   └── tco_analysis.md            ← Total Cost of Ownership
├── demo_strategy/
│   ├── demo_strategy.md           ← Tailored demo flow
│   └── tech_talking_points.md     ← Key proof points
└── notes.json                     ← Raw facts & knowledge gaps
```

All files feature **Owner: SE YOUR_NAME** and real-time syncing.

---

## 🚀 Getting Started

### Start JARVIS
```bash
./fireup_jarvis.sh
```

**Components launched:**
- **MCP Observer (Node.js)** – Monitors OpenCode and Claude conversations
- **JARVIS Core (Python)** – The "Brain" (Orchestrator + Skills)
- **UI Dashboard** – http://localhost:8080

### Add a New Opportunity

1. Create folder: `ACCOUNTS/<your-team>/<New Account>/`
2. Add at minimum: `notes.json` with facts/gaps
3. Optionally add: `deals/<deal>.json`
4. JARVIS auto-creates all other files and the HTML dashboard within 60 seconds.

---

## 📊 How It Works

1. **Observers** (MCP & File System) detect changes in conversations or manual notes.
2. **Event Bus** broadcasts updates to the **Orchestrator**.
3. **Modular Skills** (Risk, Discovery, ROI, etc.) gather data from across the workspace.
4. **LLM Synthesis** (NVIDIA/Stepfun) produces intelligent, cross-referenced content.
5. **Dashboard Engine** aggregates all outputs into a premium HTML interface.

---

## 🔧 Configuration

### 1. Configure the system

Copy `.env.example` to `.env` and add your API keys, or update `jarvis/config/jarvis.yaml`:

```yaml
workspace_root: /path/to/your/workspace
solution_engineer:
  name: YOUR_NAME
  title: Solution Engineer at COMPANY

llm:
  provider: openai
  api_key: YOUR_API_KEY
  model: gpt-4o
```

---

## 📋 Current Accounts

*Check the root `MASTER_SHEET.md` or individual `DASHBOARD.html` files for live status.*

---

## 🛠️ Advanced Usage

### Force Immediate Update
```bash
touch ACCOUNTS/<team>/<account>/notes.json
```

### Check System Status
```bash
./fireup_jarvis.sh  # Re-runs checks and restarts components if needed
```

*Note: CLI commands (`jarvis status`, etc.) are currently in active development.*

---

## 📚 Architecture Overview

- **Orchestrator** (`jarvis/core/orchestrator.py`) – Central async coordinator
- **Skills** (`jarvis/skills/`) – Specialized document & logic generators
- **Observers** (`jarvis/observers/`) – Real-time conversation & FS monitoring
- **MCP Bridge** (`mcp-opencode-observer/`) – Node.js service for OpenCode integration
- **Account Dashboard** (`jarvis/skills/account_dashboard_skill.py`) – Master aggregation layer
- **MEMORY/ & ACCOUNTS/** – Persistent knowledge and work artifacts

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Orchestrator crashes | Check `logs/orchestrator_manual.log` for missing methods |
| LLM not responding | Verify API key; system falls back to rule-based |
| Files not updating | Ensure folder is under `ACCOUNTS/` with `notes.json` or `deals/` |
| Port 8080 in use | `lsof -i :8080` → kill conflicting process |
| MCP not filtering | Verify `workspace_root` in `config/mcp-observer.json` |

---

## 📄 License

MIT – Created for YourCompany SE Team by YOUR_NAME.

---

*This README is part of the JARVIS autonomous system and is kept up-to-date automatically.*
