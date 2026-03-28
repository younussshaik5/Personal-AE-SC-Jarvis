# JARVIS System Architecture - Current Implementation

## Overview

JARVIS is a self-evolving AI agent that continuously learns from all interactions within a designated workspace. The system is composed of **15 coordinated components** (plus tool executor) organized into observers, learners, skills, and core services.

## Running Components (v2.0)

### Core Services
1. **Orchestrator** - Central coordinator managing component lifecycle and event bus
2. **Event Bus** - Async pub/sub for inter-component communication
3. **Safety Guard** - Approval workflows and risk assessment
4. **Persona Manager** - Multi-persona management (solution_consultant, account_executive)
5. **Context Engine** - Semantic context understanding (MCP integration)
6. **WebSocket Server** - Real-time UI dashboard on ws://localhost:8081

### Observers (Data Ingestion)
7. **File System Observer** - Real-time file change monitoring (watchdog)
8. **Conversation Observer** - Polls OpenCode DB for chat messages, workspace-filtered
9. **Workspace Scanner** - Periodic workspace analysis and categorization
10. **Account Auto-Initializer** - Auto-creates smartness files when new account folders appear

### Learners (Pattern Recognition)
11. **Pattern Recognition** - Learns coding patterns from file changes (5 patterns currently)
12. **Conversation Learner** - Extracts insights from all interactions; now captures meta-events (account init, tool exec, skill triggers)

### Skills (Autonomous Actions)
13. **Conversation Summarization Skill** - Stores conversations in account-based folders, extracts insights
14. **Competitive Intelligence Skill** - Auto-builds competitor profiles and battle cards
15. **Documentation Skill** - Tracks doc/PPT requests and links to entities

### Interfaces
16. **Telegram Bot Bridge** - LLM-powered chat with memory, tool execution, and account detection

## Event Flow & Interconnections

```
┌─────────────────────────────────────────────────────────────┐
│                      JARVIS ORCHESTRATOR                     │
│  • Manages component lifecycle                               │
│  • Maintains Event Bus                                      │
│  • Monitors component health                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │          EVENT BUS (async)          │
        └─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────┐
│  OBSERVERS    │  │    LEARNERS     │  │    SKILLS    │
├───────────────┤  ├─────────────────┤  ├──────────────┤
│ FileSystem    │  │ Pattern Rec    │  │ Conv Summar  │
│   - monitors  │  │   - 5 patterns │  │   - account  │
│   workspace   │  │   - updates    │  │   - insights │
│               │  │                 │  │              │
│ Conversation  │  │ Conv Learner   │  │ Comp Intel   │
│   - OpenCode  │  │   - experiences│  │   - profiles │
│   - filtered  │  │   - reflection │  │   - battles  │
│               │  │                 │  │              │
│ Workspace     │  │                 │  │ Documentation│
│   - scanning  │  │                 │  │   - requests │
│   - analysis  │  │                 │  │   - linking  │
│               │  │                 │  │              │
│ AccountInit   │  │                 │  │              │
│   - auto init │  │                 │  │              │
└───────────────┘  └─────────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                   ┌─────────────────┐
                   │  KNOWLEDGE BASE │
                   │  (MEMORY/)      │
                   │  • deals.json   │
                   │  • notes.json   │
                   │  • competitors/ │
                   │  • summaries/   │
                   │  • learnings.json│
                   └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   TELEGRAM BOT  │
                   │  • LLM responses│
                   │  • context from │
                   │    knowledge    │
                   └─────────────────┘
```

## Self-Evolution Loop

1. **Observation**: File changes, OpenCode chats, Telegram messages
2. **Learning**: Pattern recognition, conversation insight extraction
3. **Summarization**: Each conversation stored with extracted insights
4. **Reflection**: Every 30 minutes, LLM summarizes recent experiences
5. **Application**: Learnings update system prompt → better responses

## Workspace Isolation

**Critical**: JARVIS only learns from the configured `workspace_root`. 
- OpenCode DB queries filter by `session.directory LIKE '{workspace_root}%'`
- File system observer only watches `workspace_root`
- All memory files stored under workspace's `MEMORY/` folder

**Multi-workspace support**: Each workspace can have its own JARVIS instance with separate `jarvis/config/jarvis.yaml`.

## Data Organization

```
MEMORY/
├── accounts/               # Account-based storage (auto-created)
│   ├── Yellow.ai/
│   │   ├── <conv_id>.json   # conversation
│   │   ├── deals/           # account-specific deals
│   │   ├── notes.json
│   │   ├── activities.jsonl
│   │   ├── index.json
│   │   └── summary.md
│   └── <new_account>/
├── conversations/          # Per-user chat history (legacy)
│   └── {user_id}.json
├── summaries/              # Date-organized (fallback)
│   ├── 2026-03-19/
│   │   ├── conv_7354158438_064300.json
│   │   ├── insights_deals.json
│   │   ├── index.json
│   │   └── ...
├── competitors/            # Auto-built profiles
│   ├── Yellow.ai.json
│   └── battle_cards/
├── documents/              # Doc request tracking
│   ├── requests/2026-03-19/
│   ├── generated/2026-03-19/
│   └── index.json
├── notes.json              # Centralized knowledge
├── learnings.json          # Reflection summaries
├── experience.jsonl        # Raw experience log
├── active_persona.json     # Current persona state
├── patterns/               # Learned code patterns
│   └── solution_consultant_patterns.json
└── prompt_additions.txt    # Dynamic system prompt enhancements
```

## Component Details

### ConversationLearner
- Subscribes to: `telegram.message`, `telegram.response`, `conversation.message`, `modification.approved`, `scan.completed`, `pattern.discovered`, `competitor.detected`, `persona.switched`
- Plus meta‑learning: `account.initialized`, `tool.executed`, `skill.triggered`, `system.notice`
- Extracts: intents, entities, facts, preferences, knowledge gaps using LLM
- Updates: `notes.json`, `deals.json`, `patterns/`, `competitors/`
- Maintains experience buffer (last 1000 events) and reflection loop (every 30 min)

### ConversationSummarizationSkill
- Triggered by: `telegram.response`, `scan.completed`, `modification.approved`
- Stores: Full conversation with metadata in `MEMORY/summaries/YYYY-MM-DD/`
- Extracts insights using LLM → triggers updates to relevant knowledge files
- Creates index.json for daily cross-reference

### CompetitiveIntelligenceSkill
- Detects competitor queries in Telegram messages
- Builds/updates profiles in `MEMORY/competitors/{name}.json`
- Generates battle cards automatically
- Maintains mention counts and differentiators

### DocumentationSkill
- Detects doc/PPT requests in messages
- Logs requests with status (pending/fulfilled)
- Stores generated content with entity linking
- Creates searchable index
- Publishes `skill.triggered` events for meta-learning

### AccountAutoInitializer
- Watches `MEMORY/accounts/` for new folders (via `file.created` events)
- Auto-creates smartness files: `deals/`, `notes.json`, `activities.jsonl`, `index.json`, `summary.md`
- Links to competitor profile if exists
- Publishes `account.initialized` event for meta-learning

### TelegramBotBridge
- Uses LLMManager with NVIDIA Step-3.5-Flash
- Maintains per-user conversation memory (last 40 messages)
- Sends typing indicators, handles long responses (splitting)
- Publishes `telegram.response` events for learning
- **Tool execution loop**: detects `!command` in LLM output, runs via ToolExecutor, feeds back
- Detects account from conversation, stores under `MEMORY/accounts/<account>/`

#### Tool Executor (jarvis/tools/executor.py)
- Safe command runner with allowlist: `ls`, `grep`, `find`, `cat`, `head`, `tail`, `wc`, `pwd`, `du`, `df`, `file`, `stat`
- Commands run within workspace, 30‑second timeout
- Publishes `tool.executed` events for meta‑learning
- Executor receives `event_bus` to publish events

### ConversationObserver
- Polls OpenCode DB every `polling_interval_seconds` (default 5s)
- Filters sessions by workspace: `WHERE s.directory LIKE '{workspace_root}%'`
- Emits `conversation.message` events with workspace_dir

## Configuration (jarvis/config/jarvis.yaml)

```yaml
workspace_root: /path/to/your/workspace
telegram:
  enabled: true
  bot_token: "xxx"
  allowed_user_ids: []  # empty = allow all
  allow_conversational_chat: true

# Option 1: Use local LLM (e.g., NVIDIA)
llm:
  provider: "openai"
  api_key: "YOUR_API_KEY"
  base_url: "https://integrate.api.nvidia.com/v1"
  model: "stepfun-ai/step-3.5-flash"
  temperature: 1
  max_tokens: 16384

# Option 2: Use OpenCode's AI (same provider/model as OpenCode chat)
opencode_ai:
  enabled: true
  config_path: "~/.config/opencode/config.yaml"
```

When `opencode_ai.enabled` is `true`, JARVIS loads the `llm` section from the specified OpenCode config file and **ignores the local `llm` settings**. This unifies the AI backend between OpenCode and JARVIS Telegram bot.

## Startup Sequence

1. Orchestrator initializes Event Bus
2. Components start in dependency order:
   - safety_guard → persona_manager → context_engine
   - file_system → conversations → pattern_learner → conversation_learner
   - conversation_summarizer → competitive_intelligence → documentation → account_auto_init
   - scanner → archiver → websocket_server → telegram_bot
3. All components report "started"
4. "JARVIS is ready and running"

## Monitoring

- **Logs**: `logs/orchestrator_manual.log`, `logs/telegram_bot.jsonl`
- **WebSocket**: ws://localhost:8081 for real-time UI
- **Component Health**: Heartbeats every 30s logged
- **Memory Growth**: Check `MEMORY/summaries/` daily folders

## Extending the System

### Add New Skill

Create `jarvis/skills/my_skill.py`:

```python
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event

class MySkill:
    def __init__(self, config_manager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.my_skill")
    
    async def start(self):
        self.event_bus.subscribe("some.event", self._handle)
        self.logger.info("My skill started")
    
    async def _handle(self, event: Event):
        # Your logic
        pass
```

Register in `orchestrator.py` COMPONENT_CLASSES and init_order.

---

**This document reflects the actual running system as of March 19, 2026.**
**Total components: 16 | Self-evolving: YES | Workspace-isolated: YES | Tool execution: YES**
