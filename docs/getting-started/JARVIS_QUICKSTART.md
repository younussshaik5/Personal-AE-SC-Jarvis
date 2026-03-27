# JARVIS Quick Start Guide

## One-Command Launch

```bash
./fireup_jarvis.sh
```

That's it! Three components start automatically:
- ✅ **MCP Observer** (Node.js) – Monitors OpenCode conversations
- ✅ **JARVIS Core** (Python) – Orchestrator + all Skills
- ✅ **UI Dashboard** – http://localhost:8080

## Access the Dashboard

Open your browser to: **http://localhost:8080**

The dashboard provides a high-fidelity view of your entire workspace:

- **Live event stream** – Real-time feed of conversation and file events
- **Personas** – Switch between specialized behaviors (Solution Consultant, AE)
- **Account Intelligence** – Access generated Risk, Discovery, and ROI docs
- **Opportunity tracking** – Live status of all deals in your workspace
- **System monitoring** – Component health and connection status

## First Time Setup

If you're running JARVIS for the first time:

```bash
# 1. Edit the config with your identity and LLM settings
nano jarvis/config/jarvis.yaml

# 2. Start everything
./fireup_jarvis.sh
```

Key config values to set in `jarvis/config/jarvis.yaml`:
- `solution_engineer.name` – Your name
- `llm.api_key` – Your NVIDIA/OpenAI API key (for AI synthesis)
- `telegram.bot_token` – (Optional) For Telegram notifications

## Boot Sequence

When you run `./fireup_jarvis.sh`, you'll see:

```
═══════════════════════════════════════════════════════════
   J.A.R.V.I.S. - Autonomous AI Employee
   Complete System Startup
═══════════════════════════════════════════════════════════

🔹 Step 1/3: Starting MCP Observer...
  ✅ MCP observer started (PID 12345)

🔹 Step 2/3: Starting JARVIS Core...
  ✅ JARVIS core started (PID 12346)

🔹 Step 3/3: Starting JARVIS UI Dashboard...
  ✅ JARVIS UI running at http://localhost:8080

─────────────────────────────────────────────────────────
   OPEN IN BROWSER: http://localhost:8080
─────────────────────────────────────────────────────────
```

## Key Features

### Real-Time Document Generation
- **Risk Assessment** – Auto-generates `TECHNICAL_RISK_ASSESSMENT.md` as conversations happen
- **Discovery Management** – Tracks questions to answer (Q2A) and generates handoff summaries
- **Battlecards** – Identifies competitor mentions and provides tactical intel
- **ROI/TCO** – Financial modeling based on account context
- **Master Dashboard** – Aggregates all skill outputs into a single `DASHBOARD.html`

### Event-Driven Intelligence
JARVIS doesn't run on schedules — it reacts to **events**:

- OpenCode Conversation → MCP Observer → Event Bus → Skills → New/Updated Document
- Manual File Edit → FS Observer → Event Bus → Skills → Refreshed Document

## Stopping JARVIS

```bash
# Stop all components
pkill -f mcp-opencode-observer
pkill -f jarvis.core.orchestrator
pkill -f jarvis.ui.server
```

## Troubleshooting

**Port 8080 already in use?**
Find the process: `lsof -i :8080` and kill it, or edit the port in `jarvis/ui/server.py`.

**No AI Synthesis appearing?**
Check `jarvis/logs/jarvis.log` for LLM errors. Ensure your API key is set correctly in `jarvis/config/jarvis.yaml`.

**MCP connection timed out?**
The Node.js observer may need a restart. Run `./fireup_jarvis.sh` again — it will heal all processes.

**Stale data in dashboard?**
Clear browser cache, refresh the page, and verify JARVIS core is still running.

---

**Next Step**: See the [Skills Overview](../skills/OVERVIEW.md) for a deep dive into what each skill generates.