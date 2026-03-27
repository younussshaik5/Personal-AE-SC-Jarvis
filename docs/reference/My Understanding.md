# My Understanding

> [!WARNING]
> **This document is from an early phase of JARVIS development and contains outdated information** (fictional CLI commands like `jarvis start`, `jarvis scan`, Docker deployment, etc.). For the current, accurate documentation, see:
> - [START_HERE.md](../getting-started/START_HERE.md) – Current system overview
> - [Skills Overview](../skills/OVERVIEW.md) – All 15+ implemented skills
>
> This file is preserved for historical reference only.

## 📖 Overview

**JARVIS** (Just A Really Versatile Intelligent System) is an **autonomous AI employee** designed to run alongside the OpenCode ecosystem. It constantly observes, learns, and acts on your behalf, turning a regular development workspace into a self‑evolving, self‑managing environment.

Key high‑level capabilities:

| Capability | What it means |
|------------|----------------|
| **Self‑Evolution** | Meta‑learning loop that improves its own code, parameters, and strategies based on performance feedback. |
| **Autonomous Integration** | Detects new folders/files, infers project type (React, Django, etc.), and automatically scaffolds configuration, CI/CD, Docker, docs, … |
| **Persona‑Based Management** | Separate “personas” (e.g., Solution Consultant, Account Executive) each with their own deals, preferences, and knowledge graphs. |
| **MCP (Meta‑Cognitive Processor)** | Semantic context engine that plans tasks, selects the right skill, and orchestrates execution. |
| **Safety & Rollback** | Risk‑based approval workflow, automatic backups, atomic changes, kill‑switch, and full audit logs. |
| **Full Orchestration** | Central orchestrator coordinates observers, learners, updaters, persona manager, archive system, and MCP layer. |

---

## 🚀 Quick Start (from the README)

```bash
# Clone & set up
git clone https://github.com/your-org/jarvis.git
cd jarvis
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .                    # Install package in editable mode

# Create env file
cp .env.example .env
# Edit .env with your secrets (API keys, DB URLs, …)

# Start JARVIS
jarvis start            # Runs as a background daemon
jarvis status           # Shows health
jarvis scan now         # Force a workspace scan
jarvis persona list     # List existing personas
jarvis persona create --name "Acme Corp"
```

You can also embed JARVIS as a library:

```python
import asyncio
from jarvis.core.orchestrator import Orchestrator
from jarvis.utils.config import Config

async def main():
    cfg = Config.load()
    jarvis = Orchestrator(cfg)
    await jarvis.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🗂️ Repository Layout (from the top‑level README)

```
jarvis/
├── core/               # Orchestrator, meta‑learner, safety guard, sync manager
├── observers/          # File‑system, Git, DB, conversation, and Git observers
├── learners/           # Pattern recognition, preference extraction, performance analyzer, trend detector
├── updaters/           # Safe file modifications, code generation, config updates, migrations
├── persona/            # Multi‑persona manager, deal tracker, history DB, communication logger
├── scanner/           # Workspace detection, project type categorization, file classification, integration engine
├── mcp/               # Semantic context engine, autonomous planner, skill selector + skill library
├── fireup/            # Dynamic startup, skill loader, config manager
├── archive/           # Automatic snapshots, category archives, restore logic
├── safety/            # Approval workflow, impact analysis, backup & rollback
├── utils/             # Logging, config handling, event bus, file utilities, security helpers
├── cli/               # Command‑line interface and sub‑commands
├── api/               # Optional FastAPI server + endpoints
├── tests/             # Unit, integration, and fixture tests
├── docs/              # Architecture, persona guide, deployment, security, troubleshooting
└── scripts/           # Helper scripts (install, backup, restore, benchmark)
```

Each top‑level directory is described in more detail in the **File Structure** section of the README (lines 63‑207).

---

## 🧩 Core Components

| Component | Path | Responsibility |
|-----------|------|-----------------|
| **Orchestrator** | `core/orchestrator.py` | Central coordination hub; receives events, dispatches tasks, maintains global state. |
| **Meta‑Learner** | `core/meta_learner.py` | Monitors performance metrics, tunes learning rates, generates improvement hypotheses. |
| **Safety Guard** | `safety/guard.py` | Evaluates risk, enforces approval policies, triggers rollbacks. |
| **Sync Manager** | `core/sync_manager.py` | Keeps all subsystems in sync (config files, skill registry, persona data). |
| **Observers** | `observers/*.py` | Real‑time monitoring of file changes, Git activity, DB schema, and conversations. |
| **Learners** | `learners/*.py` | Detects code patterns, extracts user preferences, analyzes performance, spots tech trends. |
| **Updaters** | `updaters/*.py` | Performs safe code modifications, scaffolds new files, generates boilerplate. |
| **Persona Manager** | `persona/persona_manager.py` | Handles multiple personas, deal tracking, history, and communication logs. |
| **Workspace Scanner** | `scanner/workspace_scanner.py` | Detects new projects, categorizes by language/framework, triggers auto‑integration. |
| **MCP (Context Engine)** | `mcp/context_engine.py` | Provides semantic embeddings, context windows, and similarity search for planning. |
| **Planner** | `mcp/autonomous_planner.py` | Breaks high‑level goals into executable tasks, selects appropriate skills. |
| **Skill Selector** | `mcp/skill_selector.py` | Dynamically loads and ranks skills (React, Django, testing, etc.) based on context. |
| **Fireup** | `fireup/fireup.py` | Entry point that wires together all components and loads dynamic skills. |
| **Archive System** | `archive/*` | Daily snapshots, category‑based archives, restoration utilities. |
| **Safety Utilities** | `safety/*` | Approval workflows, impact analysis, backup & restore, kill‑switch handling. |
| **CLI** | `cli/main.py` & `cli/commands/*` | User‑facing commands (`status`, `scan`, `persona`, `deal`, `metrics`, `evolve`, …). |
| **API Server (optional)** | `api/server.py` | Exposes HTTP/WebSocket endpoints for external integration. |

---

## ⚙️ Configuration (excerpt from `jarvis_config.json` in the README)

```json
{
  "observer": {
    "file_system_enabled": true,
    "git_enabled": true,
    "scan_interval_seconds": 300,
    "ignore_patterns": [".git", "node_modules", "__pycache__"]
  },
  "learner": {
    "pattern_min_frequency": 3,
    "confidence_threshold": 0.7,
    "auto_evolution_enabled": true
  },
  "updater": {
    "backup_before_modification": true,
    "preserve_comments": true,
    "dry_run_mode": false
  },
  "safety": {
    "auto_approve_low_risk": true,
    "require_approval_medium_risk": true,
    "require_approval_high_risk": true,
    "rollback_enabled": true
  },
  "mcp": {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "enable_semantic_search": true,
    "context_window_size": 4000
  }
}
```

Full configuration options are documented in `docs/configuration.md`.

---

## 🔐 Safety & Permissions

| Risk Level | Typical Actions | Default Handling |
|------------|----------------|-----------------|
| **Low**   | Docs, tests, comment additions | Auto‑approve |
| **Medium**| Refactoring, new deps, utility functions | PR created; auto‑merge if CI passes |
| **High**  | DB schema changes, new integrations, architectural shifts | Manual approval required |
| **Critical** | Core system changes, security patches | Two‑person approval |
| **Emergency** | Kill‑switch activation | Immediate pause |

*Kill‑switch*: Create a `.jarvis.killswitch` file in the workspace root to instantly halt all JARVIS activity. Remove it to resume.

All actions are logged with timestamps, component, risk level, and approval status. Logs reside in `logs/audit/`.

---

## 📊 Monitoring & Metrics

- **CLI**: `jarvis metrics` (supports time ranges)  
- **Logs**: JSON‑formatted entries in `logs/jarvis.log`  
- **API**: `GET /metrics` (if the API server is enabled)  
- **Dashboard**: Planned web UI (not yet shipped)

Key metrics tracked:

- Tasks completed per persona
- Files modified / suggestions made
- Learning cycles run
- Self‑evolutions applied
- Error rates & rollback counts
- API usage & cost estimation

---

## 🛠️ Extending the System

### Adding a New Skill

1. Create `mcp/skills/my_new_skill.py`:

```python
from mcp.skills.base_skill import BaseSkill

class MyNewSkill(BaseSkill):
    name = "my_new_skill"
    description = "Does something awesome"
    applicable_tech = ["python", "django"]

    async def execute(self, context):
        # implement logic here
        return {"status": "success", "result": "..."}
```

2. Register it (dynamic loader usually picks it up automatically).  
3. Add unit tests under `tests/unit/mcp/skills/`.

### Custom Configuration

Edit `config/jarvis.yaml` (generated on first run) or use environment variables to override defaults. Example snippet (lines 300‑327 of the README) shows safety, evolution, archiving, persona, and logging sections.

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit

# Integration tests (requires a sandbox workspace)
pytest tests/integration

# Full suite with coverage
pytest --cov=jarvis --cov-report=html

# Benchmark performance
python scripts/benchmark.py
```

All tests are runnable without external services; the **self‑evolution** feature includes a `--dry-run` mode for safe experimentation.

---

## 📦 Deployment Options

| Platform | Steps |
|----------|-------|
| **Systemd (Linux)** | Use the `scripts/jarvis.service` file; enable/start with `systemctl`. |
| **Docker** | Build with the provided Dockerfile; mount `data/` and `workspace/` volumes. |
| **Mac / Manual** | Run `jarvis start --foreground` for debugging, or `jarvis start` as a daemon. |

Full guides are in `docs/deployment.md`.

---

## 🤝 Contributing

- Fork → feature branch → implement → add tests → run `pytest` → PR.  
- See `CONTRIBUTING.md` and `docs/development/` for detailed guidelines on adding skills, learners, or safety improvements.

---

## 📚 Additional Documentation

- `docs/architecture.md` – deep dive into system design.  
- `docs/persona_guide.md` – managing multiple personas, deal tracking.  
- `docs/security.md` – security considerations and hardening.  
- `docs/troubleshooting.md` – common issues and fixes.  
- `docs/api/` – REST/WebSocket API reference.

---

### ✅ Summary

- **What the project does:** Provides a self‑evolving, autonomous AI employee that watches your codebase, learns your preferences, and carries out routine development tasks while keeping safety and auditability front‑and‑center.
- **Core ideas:** Observers → Learners → Updaters → Safety Guard → Orchestrator → MCP Planner/Skill Selector.
- **How you interact:** Via the `jarvis` CLI, optional FastAPI server, or directly as a Python library.
- **Extensibility:** Add new skills, tweak safety thresholds, or customize personas without touching core code.
- **Safety:** Risk‑based approvals, automatic backups, kill‑switch, and immutable audit logs protect you from unintended changes.

You now have a complete Markdown file describing the project. Feel free to open or edit it as needed.
