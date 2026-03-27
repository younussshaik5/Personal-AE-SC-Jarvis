# JARVIS System Interconnections Map

> [!WARNING]
> **Parts of this document are outdated** (references to updaters, learners, archive system, trust scores, and `jarvis deal create` CLI). The core event-driven architecture and observer → event bus → skills flow described here is still accurate. For the latest system documentation, see:
> - [Data Flow Architecture](../architecture/DATA_FLOW.md) – Current data flow
> - [START_HERE.md](../getting-started/START_HERE.md) – Current system overview

## Overview
All components are intentionally interconnected through a unified architecture. This document shows how each piece connects.

---

## 1. Dependency Graph

```
                    ┌─────────────────────┐
                    │  OPENCODE_FIREUP   │
                    │      SKILL.md       │
                    └─────────┬───────────┘
                              │ (Phase 0: launches)
                              ▼
                    ┌─────────────────────┐
                    │  MCP Observer       │
                    │  (Node.js)          │
                    │   - polls DB       │
                    │   - extracts insights
                    └─────────┬───────────┘
                              │ (events via MCP)
                              ▼
┌───────────────┐   ┌─────────────────────┐   ┌───────────────┐
│   User Code   │   │   JARVIS Core      │   │   Personas    │
│   & Files      │◄──┤   Orchestrator     │◄──┤  (JSON files) │
└───────────────┘   │   - Coordinates    │   └───────────────┘
     ▲              │   - Lifecycle      │         ▲
     │ (observed)   │   - Health checks │         │ (loaded by)
     │              └─────────┬───────────┘         │
     │                │       │        │          │
     │    ┌───────────▼─────┐ │  ┌────▼─────────┤
     │    │   Observers     │ │  │  Learners    │
     │    │  - file_system  │ │  │  - patterns  │
     │    │  - conversations│ │  │  - preferences
     │    └──────────┬───────┘ │  └──────────────┘
     │               │        │        │
     │    ┌──────────▼───────┐│  ┌────▼────────────┐
     │    │    Updaters      ││  │   Safety Guard │
     │    │  - file_modder   ││  │  - approvals   │
     │    │  - code_gen      ││  │  - trust scores│
     │    └──────────┬───────┘│  └─────────────────┘
     │               │        │
     │    ┌──────────▼───────┐│
     │    │   MCP Context    ││
     │    │   - workspace    ││
     │    │   - semantic     ││
     │    └──────────┬───────┘│
     │               │        │
     │    ┌──────────▼───────┐│
     │    │    Archiver      ││
     │    │  - snapshots     ││
     │    └───────────────────┘│
     │                         │
     └─────────────────────────┘
```

---

## 2. Data Flow

### Startup Sequence
```
1. User: "fireup"
   ↓
2. OPENCODE_FIREUP_SKILL.md executes
   ↓
3. Phase 0: Spawns MCP Observer (node dist/index.js)
   ↓
4. MCP observer starts polling OpenCode DB
   ↓
5. Fireup initializes JARVIS (orchestrator.initialize())
   ↓
6. Orchestrator starts all components in order:
   a. Safety Guard (first - approves everything)
   b. Persona Manager (loads active persona)
   c. Context Engine (loads workspace context)
   d. Observers (file_system, conversations)
   e. Learners (pattern_recognition)
   f. Archiver (scheduled snapshots)
   ↓
7. Workspace scanner runs (if configured)
   ↓
8. Persona auto-matches based on path
   ↓
9. System ready - all observers active
```

### Runtime Data Flow

```
File Created/Modified
    ↓
FileSystemObserver event
    ↓
EventBus.publish("file.created/modified")
    ↓
    ├─► PatternRecognition (learns code patterns)
    ├─► ContextEngine (updates workspace knowledge)
    └─► Updater (if auto-fix triggered)
         ↓
    SafetyGuard approval check
         ↓
    FileModder (writes with backup)
         ↓
    Archiver (snapshot after N changes)

------------

New Conversation Message
    ↓
ConversationObserver polls DB
    ↓
EventBus.publish("conversation.message")
    ↓
    ├─► PatternRecognition (extract preferences)
    ├─► ContextEngine (update domain terms)
    └─► PersonaManager (log activity)

------------

Workspace Detected (scan)
    ↓
Scanner categorizes project type
    ↓
EventBus.publish("workspace.scanned")
    ↓
    ├─► PersonaManager (auto-assign to persona)
    ├─► ContextEngine (set project context)
    └─► MCP Skills (load React/Django/etc)
```

---

## 3. File Interconnections

### Core Files
- `core/orchestrator.py`
  - Imports: ALL other components
  - Central hub - every component registered here
  - Manages start/stop lifecycle

### Configuration Files
- `utils/config.py` (JARVIS_CONFIG)
  - Read by: orchestrator, all components via constructor
  - Paths defined: workspaces, data, logs, cache
  - Hot-reloaded on changes

### Persona System
- `persona/persona_manager.py`
  - Reads/Writes: `data/personas/personas.json`
  - SQLite: `data/history/jarvis.db` (deals, activity)
  - Publishes: `persona.switched`, `deal.created` events
  - Subscribes to: `workspace.scanned` (auto-assignment)

### Observers
- `observers/file_system.py`
  - Uses: watchdog library
  - Watches: `config.workspace_root` + persona workspaces
  - Publishes: `file.created`, `file.modified`, `file.deleted`, `file.moved`
- `observers/conversations.py`
  - Connects to: `config.opencode_db_path` (SQLite)
  - Polls every `config.polling_interval_seconds`
  - Publishes: `conversation.message`

### Learners
- `learners/pattern_recognition.py`
  - Subscribes to: `conversation.message`, `file.created`, `file.modified`
  - Stores: `data/patterns/patterns.json`
  - Updates in-memory cache

### Safety
- `safety/guard.py`
  - Subscribes to: `modification.requested`
  - Reads trust scores from memory
  - Publishes: `modification.approved` or `approval.required`
  - Checks: `config.killswitch_path` before any action

### Updaters (stub)
- Would subscribe to: `modification.approved`
- Would read: backup locations from config
- Would write: actual file modifications

### Context Engine
- `mcp/context_engine.py`
  - Subscribes to: `workspace.scanned`, `persona.switched`, `conversation.message`
  - Stores: `data/cache/context.json`
  - Provides: `get_context()` for MCP tools

### Archiver
- `archive/archiver.py`
  - Subscribes to: `archive.request`, `system.shutdown`
  - Writes to: `data/archives/YYYY-MM/`
  - Uses: `config.archive_compression`

### Event Bus
- `utils/event_bus.py`
  - Central publish/subscribe
  - All components connect through this
  - No direct imports between components (decoupled)

---

## 4. MCP Integration Points

### OpenCode ↔ JARVIS

**OpenCode calls JARVIS MCP tools:**
- `jarvis_status()` → Orchestrator.get_status()
- `get_workspace_context()` → ContextEngine.get_context()
- `list_personas()` → PersonaManager.list_personas()
- `switch_persona(name)` → PersonaManager.switch_persona()
- `create_deal(...)` → PersonaManager.create_deal()
- `get_approvals()` → SafetyGuard.get_queue()
- `approve_change(id)` → SafetyGuard.approve()
- `archive_snapshot(reason)` → Archiver.create_snapshot()
- `run_evolution_cycle()` → MetaLearner.trigger_cycle()

**JARVIS observes OpenCode via:**
- Node.js MCP observer (`mcp-opencode-observer/`)
  - Polls `~/.local/share/opencode/opencode.db` (SQLite)
  - Extracts conversations, file changes
  - Publishes to JARVIS via event bus or direct file
- Alternatively, direct Python observer (future)

---

## 5. Fireup Skill Enhancements

`OPENCODE_FIREUP_SKILL.md` now includes:

```
Phase 0:
  • Auto-launch MCP observer
  • Initialize JARVIS if jarvis/ exists
  • Trigger workspace scan
  • Match persona based on workspace path
  • Load persona-specific skill file
```

This creates seamless integration: when you say "fireup" in OpenCode, JARVIS starts automatically in the correct persona context.

---

## 6. Persona-Based Account/Deal Management

### Persona JSON
`data/personas/personas.json`:
```json
{
  "personas": [
    {
      "id": "work",
      "name": "Work",
      "type": "solution_consultant",
      "workspaces": ["/path/to/presales"],
      "preferences": {...},
      "knowledge_graph": {...},
      "deals": [
        {
          "deal_id": "deal_123",
          "title": "Enterprise Deal",
          "client": "Acme",
          "deadline": "2026-04-15",
          "status": "active",
          "budget": 50000
        }
      ]
    }
  ]
}
```

### Deals Tracking
- Created via CLI: `jarvis deal create ...`
- Stored in: `persona.deals` (in-memory) + `data/history/jarvis.db` (SQLite)
- Auto-linked to git commits if commit message contains `deal_123`
- Auto-updates progress based on task completion events

---

## 7. Safety & Approval Flow

```
Modification Requested
    ↓
SafetyGuard.evaluate()
    ↓
Check risk_level + trust_score
    ↓
    ├─ LOW & trust>0.3 → auto-approve
    ├─ MEDIUM & trust>0.7 & CI passes → auto-approve
    ├─ HIGH → manual approval (2 reviewers)
    └─ CRITICAL → 4-eyes + emergency stop
    ↓
Approved?
    ↓
    YES → Backup file → FileModder → Verify → Log
    NO  → Reject event → Notify user
```

Every step logged to `logs/audit/`.

---

## 8. Self-Evolution Trigger Chain

```
Meta-Learner (runs every 6h)
    ↓
GetMetrics (last 24h)
    ↓
Analyze trends:
  - Error rate ↑
  - Task time ↑
  - User satisfaction ↓
  - New technology detected
    ↓
Generate hypotheses (3-5)
    ↓
Filter by feasibility & impact
    ↓
Select top 2 for A/B test
    ↓
Sandbox test (isolated workspace)
    ↓
Compare metrics against baseline (24h)
    ↓
If improvement >X% with statistical significance:
  - Deploy to 10% of personas (canary)
  - Monitor for 24h
  - If success → full rollout
  - Record in `data/patterns/evolution.json`
    ↓
Update trust scores for affected personas
```

---

## 9. Archive & Restore Chain

```
Scheduled (daily at 2 AM) OR manual request
    ↓
Archiver.create_snapshot()
    ↓
Include:
  - Workspace root (excluding archives/cache)
  - JARVIS data/ (excluding archives)
  - JARVIS config/
    ↓
Compress (gzip) → `data/archives/YYYY-MM/snapshot_YYYYMMDD_HHMMSS.tar.gz`
    ↓
Deduplication: hard links for unchanged files
    ↓
Retention: delete >90 days (configurable)
    ↓
Restore:
  - `jarvis restore --archive <path>` → extracts with rollback
  - Selective: `jarvis restore --file <relative/path>`
```

---

## 10. Directory Relationship Table

| Directory | Purpose | Connected From |
|-----------|---------|----------------|
| `persona/` | Universal persona templates | Fireup skill loader |
| `MEMORY/` | Conversation memory, active_persona | MCP observer, PersonaManager |
| `Presales Skills/` | Specialized presales skills | Fireup skill references |
| `jarvis/data/personas/` | Active persona definitions | PersonaManager (read/write) |
| `jarvis/data/patterns/` | Learned patterns | PatternRecognition (write), Context (read) |
| `jarvis/data/archives/` | Snapshots | Archiver (write), Restore (read) |
| `jarvis/data/history/` | SQLite activity log | PersonaManager, Events |
| `jarvis/logs/` | Structured logs (JSONL) | All components |
| `jarvis/config/jarvis.yaml` | Main configuration | All components (read) |
| `mcp-opencode-observer/` | Node.js MCP bridge | OpenCode MCP config |

---

## 11. Component Responsibility Matrix

| Component | Reads | Writes | Subscribes To | Publishes |
|-----------|-------|--------|---------------|-----------|
| Orchestrator | config | status events | all component.health | system.started, component.registered |
| FileSystemObserver | filesystem | event logs | (watchdog) | file.created/modified/deleted/moved |
| ConversationObserver | OpenCode DB | event logs | poll loop | conversation.message |
| PatternRecognition | patterns file | patterns file | file.*, conversation.* | pattern.discovered, preference.updated |
| PersonaManager | personas.json, history DB | personas.json, history DB | workspace.scanned | persona.switched, deal.created |
| SafetyGuard | trust scores | approval queue | modification.requested | modification.approved/blocked, approval.required |
| ContextEngine | context cache | context cache | workspace.scanned, persona.switched, conversation.* | context.updated |
| Archiver | archives dir | archives | archive.request, system.shutdown | archive.created/restored |

---

## 12. Configuration Flow

```
jarvis/scripts/setup.py
    ↓
Creates: jarvis/config/jarvis.yaml (defaults)
Edits: ~/.config/opencode/opencode.jsonc (adds mcp.jarvis)
    ↓
User can edit jarvis/config/jarvis.yaml
    ↓
ConfigManager.load() reads YAML
    ↓
ConfigManager.start_watcher() watches for changes
    ↓
On change: reloads and notifies components via event_bus
    ↓
Components update their behavior dynamically
```

---

## Conclusion

**Every file and folder has a defined purpose and interconnection.** The system is:

- **Loose coupling**: Components communicate via events (event_bus)
- **High cohesion**: Each component has single responsibility
- **Configurable**: Central config with hot reload
- **Observable**: All actions logged, metrics exposed
- **Safe**: Approval gates, backups, rollback everywhere
- **Evolving**: Meta-learner can improve components

The architecture ensures that adding new skills, observers, or updaters is straightforward: simply implement the interface, register dependencies, and subscribe to relevant events.

All files are interconnected through well-defined contracts (events, config keys, data schemas). No magic - explicit imports, explicit event subscriptions, explicit file paths.
