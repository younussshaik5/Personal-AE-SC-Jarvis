# JARVIS Core – Python Package

> Autonomous AI Employee for Solution Engineers

## What Is This Package?

This is the core Python package for JARVIS. It contains the orchestrator, event bus, observers, skills, and utility modules that power the autonomous document generation system.

## Package Structure

```
jarvis/
├── core/
│   └── orchestrator.py          # Central async coordinator & component lifecycle
├── skills/                      # 15+ document generation skills
│   ├── technical_risk_assessment.py
│   ├── discovery_management.py
│   ├── account_dashboard_skill.py
│   ├── deal_meddpicc.py
│   ├── stakeholder_analysis.py
│   ├── battlecards.py
│   ├── pricing_comparison.py
│   ├── roi_model.py
│   ├── tco_analysis.py
│   ├── demo_strategy.py
│   ├── documentation.py
│   └── account_initialization.py
├── observers/
│   ├── file_system_observer.py  # Watchdog-based FS monitoring
│   └── conversation_observer.py # OpenCode conversation polling
├── utils/
│   ├── event_bus.py             # Async pub/sub messaging
│   ├── data_aggregator.py       # Cross-skill context gathering
│   ├── llm_manager.py           # LLM provider abstraction
│   ├── logger.py                # Structured JSON logging
│   └── config.py                # YAML config management
├── ui/
│   └── server.py                # Dashboard web server (port 8080)
├── config/
│   └── jarvis.yaml              # Main configuration file
├── cli/
│   └── main.py                  # CLI entry point (placeholder)
└── setup.py                     # Package installer
```

## Installation

```bash
# From the workspace root
pip install -e jarvis
```

This registers the `jarvis` command (currently a placeholder) and makes the package importable.

## Configuration

Edit `jarvis/config/jarvis.yaml`:

```yaml
workspace_root: /path/to/your/workspace
solution_engineer:
  name: YOUR_NAME
  title: Solution Engineer at YourCompany

llm:
  provider: openai
  model: stepfun-ai/step-3.5-flash
  api_key: "your-api-key"
  base_url: "https://integrate.api.nvidia.com/v1"
```

## Running

JARVIS is started via the root-level script:

```bash
./fireup_jarvis.sh
```

This launches the MCP Observer, JARVIS Core (orchestrator), and the UI Dashboard together. You don't run the orchestrator standalone — use `fireup_jarvis.sh`.

## How It Works

1. **Orchestrator** initializes all components in dependency order
2. **Observers** detect file changes and new conversations
3. **Event Bus** broadcasts events to interested skills
4. **Skills** gather context, call LLM if available, and write documents
5. **Dashboard Skill** aggregates all outputs into `DASHBOARD.html`

## Adding a New Skill

1. Create `jarvis/skills/your_skill.py` with a class that has `start()` and `stop()` methods
2. Register it in `orchestrator.py`:
   ```python
   from jarvis.skills.your_skill import YourSkill
   COMPONENT_CLASSES['your_skill'] = YourSkill
   ```
3. Add to `init_order` in the orchestrator
4. Restart JARVIS

## Logs

- `logs/jarvis.log` – Main orchestrator log
- `logs/skill.*.jsonl` – Per-skill structured logs
- `logs/orchestrator_manual.log` – Startup and lifecycle events

## CLI Status

The `jarvis` CLI entry point (`jarvis/cli/main.py`) is currently a **placeholder**. System startup and control is handled entirely by `./fireup_jarvis.sh`.

---

**Owner:** SE YOUR_NAME | YourCompany