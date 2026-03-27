# JARVIS – Start Here

## 🎉 What Is JARVIS?

JARVIS is a **fully autonomous AI employee** built for Solution Engineers. It monitors your workspace — conversations, files, and account data — and automatically generates a complete suite of interlinked sales engineering documents.

**You don't prompt it. You don't schedule it. It just works.**

When a conversation happens in OpenCode or a file changes in your `ACCOUNTS/` folder, JARVIS detects it within 60 seconds and updates every relevant document: risk assessments, discovery docs, MEDDPICC reports, battlecards, ROI models, and a master HTML dashboard.

---

## 📦 System Components

```
OPENCODE SPACE/
├── fireup_jarvis.sh            ← Run this to start everything
├── ACCOUNTS/                   ← Your accounts & opportunities
├── MEMORY/                     ← Cross-account knowledge base
├── jarvis/                     ← Python core package
│   ├── core/orchestrator.py    ← Central async coordinator
│   ├── skills/                 ← 15+ document generation skills
│   ├── observers/              ← File system & conversation monitors
│   ├── utils/                  ← Event bus, data aggregation, logging
│   ├── ui/server.py            ← Dashboard web server
│   └── config/jarvis.yaml      ← Main configuration
├── mcp-opencode-observer/      ← Node.js bridge for OpenCode
├── persona/                    ← Role-specific behavior configs
├── docs/                       ← This documentation
└── config/                     ← MCP observer & rules config
```

**All core components are fully implemented and operational.**

---

## 🚀 Getting Started

### 1. Configure
Edit `jarvis/config/jarvis.yaml` with:
- Your name and title under `solution_engineer`
- Your LLM API key under `llm` (NVIDIA/OpenAI)
- Optional: Telegram bot token for notifications

### 2. Launch
```bash
./fireup_jarvis.sh
```

This starts three services:
- **MCP Observer** (Node.js) – Polls OpenCode conversations
- **JARVIS Core** (Python) – Orchestrator + Skills engine
- **UI Dashboard** – Available at http://localhost:8080

### 3. Add an Account
Create a folder structure:
```bash
mkdir -p "ACCOUNTS/YOUR TEAM/Account Name"
```
Add a `notes.json` with initial facts and knowledge gaps. JARVIS will auto-generate all documents within 60 seconds.

---

## 📊 How It Works

```
OpenCode Conversations ──→ MCP Observer ──→ Event Bus
Local File Changes ──────→ FS Observer  ──→ Event Bus
                                               │
                                         Orchestrator
                                               │
                              ┌────────────────┼────────────────┐
                              ▼                ▼                ▼
                         Risk Skill      Discovery Skill   Dashboard Skill
                              │                │                │
                              ▼                ▼                ▼
                    RISK_ASSESSMENT.md    Q2A.md / discovery/   DASHBOARD.html
```

1. **Observers** detect changes (conversations, files)
2. **Event Bus** broadcasts events to the **Orchestrator**
3. **Orchestrator** triggers the relevant **Skills**
4. **Skills** gather context from all account files, call the LLM if configured, and write output documents
5. **Dashboard Skill** aggregates everything into a master HTML view

---

## 🛠️ What Gets Generated (Per Account)

```
ACCOUNTS/<Team>/<Account>/
├── DASHBOARD.html                 ← Master CRM-style view with exports
├── TECHNICAL_RISK_ASSESSMENT.md   ← LLM-synthesized risk analysis
├── discovery/
│   ├── internal_discovery.md      ← Deep technical dive
│   ├── final_discovery.md         ← Handoff summary
│   └── Q2A.md                     ← Questions to answer
├── meddpicc/
│   ├── qualification_report.md    ← MEDDPICC qualification
│   └── stakeholder_analysis.md    ← Champion/MAP tracking
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

All files are **interlinked** — a risk found in discovery automatically appears in the risk assessment and dashboard.

---

## 📚 Documentation Guide

Read in this order:

| # | File | What You'll Learn |
|---|------|-------------------|
| 1 | **This file** | System overview and getting started |
| 2 | **[Quickstart](JARVIS_QUICKSTART.md)** | One-command launch and boot sequence |
| 3 | **[Skills Overview](../skills/OVERVIEW.md)** | What each skill does and generates |
| 4 | **[Data Flow](../architecture/DATA_FLOW.md)** | How information moves through the system |
| 5 | **[Current Architecture](../architecture/CURRENT_ARCHITECTURE.md)** | Full component breakdown |

---

## ✅ What's Working Now

- ✅ Event-driven orchestration with async Event Bus
- ✅ Real-time file system & conversation monitoring
- ✅ 15+ automated document generation skills
- ✅ LLM synthesis (NVIDIA/OpenAI) with rule-based fallbacks
- ✅ Master HTML Dashboard with PDF/Word/Excel export
- ✅ Cross-skill data aggregation (skills are context-aware)
- ✅ Multi-persona support (Solution Consultant, AE)
- ✅ Automatic account initialization
- ✅ Telegram notifications (basic)
- ✅ Web search integration (DuckDuckGo)

## 🚧 In Progress

- 🏗️ CLI commands (`jarvis status`, etc.) — placeholder only
- 🏗️ Advanced Telegram interactivity
- 🏗️ Meta-learning / self-correction loop
- 🏗️ Extended test coverage

---

## 🎯 Key Concepts

### Event-Driven Architecture
Components don't call each other directly — they publish events that others subscribe to. This keeps the system **loosely coupled** and extensible. Adding a new skill never requires modifying the orchestrator.

### Cross-Skill Intelligence
The `DataAggregator` utility reads all generated files across skills, so each skill has full context. When the Discovery skill finds a gap, the Risk Assessment skill can immediately factor it in.

### LLM + Rule-Based Hybrid
JARVIS uses LLM synthesis (via NVIDIA or OpenAI) for high-quality output. If the LLM is unavailable, every skill has a **rule-based fallback** that still extracts and formats all relevant data.

### Persona System
The `persona/` directory contains role-specific configurations. The system tailors its behavior based on whether you're operating as a Solution Consultant or an Account Executive.

---

## 💡 Tips

- **Force an immediate update**: `touch ACCOUNTS/<team>/<account>/notes.json`
- **Check system health**: Re-run `./fireup_jarvis.sh` — it checks and restarts all processes
- **View logs**: `tail -f jarvis/logs/jarvis.log`
- **Add a new account**: Just create the folder under `ACCOUNTS/` and add `notes.json`

---

**Built by SE YOUR_NAME** | Designed for YourCompany Solution Engineers
