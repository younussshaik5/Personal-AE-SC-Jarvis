# The Art of JARVIS: A Fully Self-Evolving AI Agent Ecosystem

**Author**: YOUR_NAME  
**Date**: March 27, 2026 (Originally March 19, 2026)  
**Version**: 2.1 (Event-Driven, Skill-Based Architecture)  
**Status**: Production-Ready | 15+ Skills Active

---

## Executive Summary

JARVIS (Just A Really Versatile Intelligent System) is **not a chatbot**. It is a **living AI employee** that operates autonomously within your workspace, learning from every interaction, every file change, every approval, and every request. It doesn't just answer questions—it **builds knowledge**, **connects dots**, and **gets smarter** with each passing minute.

### What Makes JARVIS Different?

| Traditional Bot | JARVIS |
|----------------|--------|
| Stateless conversations | Persistent memory with context |
| Keyword matching | LLM-powered understanding |
| Reactive only | Proactive learning and organization |
| Manual knowledge updates | Automatic insight extraction |
| Isolated interactions | Cross-referenced, interconnected knowledge |
| No memory between chats | Full conversation history + reflections |

**JARVIS remembers everything**, organizes it automatically, and uses that knowledge to make better decisions tomorrow.

---

## Core Philosophy

### 1. Everything is a Learning Opportunity

Every single interaction—whether it's a Telegram message, a file edit, an approval, or a scan—is captured, processed, and turned into structured knowledge. Nothing is thrown away.

### 2. Automatic Organization

You don't need to file things. JARVIS automatically:
- Stores conversations by date (`MEMORY/summaries/2026-03-19/`)
- Extracts entities (deals, competitors, people)
- Updates relevant knowledge bases
- Creates cross-links between related data

### 3. Workspace Isolation

JARVIS only learns from **this workspace**. Use OpenCode or Claude for other projects—those conversations stay separate. Each workspace can have its own JARVIS instance with independent memory.

### 4. Continuous Improvement

Every 30 minutes, JARVIS reflects on recent experiences, extracts patterns, and updates its understanding. The system prompt evolves. Future responses get smarter.

---

## Architecture: How JARVIS Thinks

### The Modular Skill Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATOR                             │
│          (The Brain - coordinates everything)                  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   EVENT BUS   │
                    │  (Nervous     │
                    │   System)     │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌─────────────────┐  ┌────────────────────┐
│  OBSERVERS    │  │    LEARNERS     │  │  SKILLS (15+)      │
├───────────────┤  ├─────────────────┤  ├────────────────────┤
│ • File System │  │ • Pattern Rec   │  │ Risk Assessment    │
│   (watchdog)  │  │ • Conv Learner  │  │ Discovery Mgmt     │
│ • Conversation│  │                 │  │ MEDDPICC           │
│   (OpenCode   │  │                 │  │ Stakeholder Map    │
│    DB polls)  │  │                 │  │ Battlecards        │
│               │  │                 │  │ Pricing Comparison │
│               │  │                 │  │ ROI Model          │
│               │  │                 │  │ TCO Analysis       │
│               │  │                 │  │ Demo Strategy      │
│               │  │                 │  │ Tech Talking Pts   │
│               │  │                 │  │ Account Dashboard  │
│               │  │                 │  │ Competitive Intel  │
│               │  │                 │  │ Data Seeder        │
│               │  │                 │  │ Account Auto-Init  │
│               │  │                 │  │ Conv Summarizer    │
│               │  │                 │  │ Documentation      │
└───────────────┘  └─────────────────┘  └────────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              ┌──────────────────────────┐
              │    ACCOUNTS/<team>/      │
              │   <account>/            │
              │  ├── DASHBOARD.html     │
              │  ├── TECHNICAL_RISK_... │
              │  ├── discovery/         │
              │  ├── meddpicc/          │
              │  ├── battlecards/       │
              │  ├── value_architecture/│
              │  ├── demo_strategy/     │
              │  └── notes.json         │
              └──────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │   UI Dashboard           │
              │   http://localhost:8080   │
              │   • Master CRM view      │
              │   • Export (PDF/Word)     │
              └──────────────────────────┘
```

### Component Deep Dive

#### 1. Observers: The Senses

**File System Observer**
- Watches your workspace in real-time using `watchdog`
- Detects: file created, modified, deleted, moved
- Publishes events: `file.created`, `file.modified`, etc.
- **Critical Fix**: Uses main event loop to avoid threading crashes

**Conversation Observer**
- Polls OpenCode SQLite database every 60 seconds
- **Workspace Filter**: `SELECT ... JOIN session WHERE session.directory LIKE '/path/to/your/workspace/%'`
- Only learns from this workspace's conversations
- Emits `conversation.message` events with workspace info

**Workspace Scanner**
- Periodically analyzes workspace structure
- Categorizes projects by tech stack
- Helps JARVIS understand context

#### 2. Learners: The Pattern Recognition

**Pattern Recognition**
- Listens to `file.modified` events
- Builds `MEMORY/patterns/solution_consultant_patterns.json`
- Currently tracks 5 patterns from file edits
- Counts occurrences, builds statistics

**Conversation Learner**
- **The key to self-evolution**
- Subscribes to:
  - `telegram.message` (your questions)
  - `telegram.response` (JARVIS's answers)
  - `conversation.message` (OpenCode chats in this workspace)
  - `modification.approved` (what you approve)
  - `scan.completed` (workspace analysis results)
  - `pattern.discovered` (new patterns found)
  - `competitor.detected` (competitor mentions)
  - `persona.switched` (persona changes)
- Maintains experience buffer (last 1000 interactions)
- Extracts insights using LLM:
  ```json
  {
    "intent": "question",
    "entities": {"deals": [...], "companies": [...]},
    "facts": ["TechCorp deal size $50K"],
    "preferences": {"communication_style": "concise"},
    "knowledge_gaps": ["pricing model unclear"],
    "decisions": ["approved database migration"]
  }
  ```
- Updates `notes.json`, `deals.json`, etc.
- **Reflection Loop**: Every 30 minutes, summarizes last 100 experiences → `MEMORY/learnings.json`

#### 3. Skills: The 15+ Autonomous Agents

Each skill is a self-contained module in `jarvis/skills/` that subscribes to events, gathers context via the DataAggregator, and generates/updates documents per account.

| Skill | Output | Description |
|-------|--------|-------------|
| **Technical Risk Assessment** | `TECHNICAL_RISK_ASSESSMENT.md` | LLM-synthesized risk analysis per account |
| **Discovery Management** | `discovery/internal_discovery.md`, `final_discovery.md`, `Q2A.md` | Full discovery lifecycle docs |
| **Deal MEDDPICC** | `meddpicc/qualification_report.md` | MEDDPICC qualification tracking |
| **Stakeholder Analysis** | `meddpicc/stakeholder_analysis.md` | Champion/MAP tracking |
| **Battlecards** | `battlecards/competitive_intel.md` | Competitor deep-dives |
| **Pricing Comparison** | `battlecards/pricing_comparison.md` | Pricing vs market |
| **ROI Model** | `value_architecture/roi_model.md` | Financial impact analysis |
| **TCO Analysis** | `value_architecture/tco_analysis.md` | Total Cost of Ownership |
| **Demo Strategy** | `demo_strategy/demo_strategy.md` | Tailored demo flow |
| **Tech Talking Points** | `demo_strategy/tech_talking_points.md` | Key proof points |
| **Account Dashboard** | `DASHBOARD.html` | Master CRM-style view with exports |
| **Competitive Intelligence** | `MEMORY/competitors/` | Auto-built competitor profiles |
| **Conversation Summarizer** | `MEMORY/summaries/` | Conversation archival |
| **Data Seeder** | `notes.json`, `deals/` | Initial data population |
| **Account Auto-Init** | Folder structure | Auto-creates account folders & files |
| **Documentation** | `MEMORY/documents/` | Doc request tracking |

All skills read each other's outputs for maximum cross-referencing. A change to `notes.json` triggers cascading updates across Risk, Discovery, MEDDPICC, and Dashboard skills.

For full details on each skill, see `docs/skills/OVERVIEW.md`.

#### 4. Core: The Nervous System

**Orchestrator**
- Initializes Event Bus first
- Starts components in dependency order
- Monitors heartbeats (30s intervals)
- Graceful shutdown on signals

**Event Bus**
- Async pub/sub (custom implementation)
- All communication flows through here
- Decouples components

**Safety Guard**
- Basic approval workflows implemented
- Audit logging active

**Persona Manager**
- Loads personas from `jarvis/data/personas/`
- Current: `work` persona only
- Tracks active persona in `MEMORY/active_persona.json`

**Context Engine (MCP)**
- Bridges MCP Observer data with skill context
- Used by DataAggregator for cross-skill intelligence

**WebSocket Server**
- Serves events to UI dashboard on ws://localhost:8081

#### 5. Interface: The Voice

**Telegram Bot Bridge**
- Uses `python-telegram-bot` library ( polling )
- LLM: NVIDIA Step-3.5-Flash via OpenAI-compatible API
- **Memory**: Per-user conversation history (last 40 messages)
  - Stored in `MEMORY/conversations/{user_id}.json`
- **System Prompt**: Dynamically built with:
  - Current persona description
  - Recent patterns learned
  - Competitor intelligence summary
  - Active deals summary
  - System status
- **Response Flow**:
  1. Receive message
  2. Send typing indicator
  3. Build context (system prompt + history + current message)
  4. Call LLM
  5. Publish `telegram.response` event (for learning)
  6. Send reply (split if >4000 chars)
- **Command Routing**: Uses LLM for intent classification (no more keyword matching)

---

## Data Organization: Where Everything Goes

```
MEMORY/
├── conversations/                    # Chat history per user
│   └── 7354158438.json              # {"history": [{role, content, timestamp}]}
├── summaries/                       # Date-organized conversations
│   ├── 2026-03-19/
│   │   ├── conv_7354158438_064300.json
│   │   ├── insights_deals.json
│   │   ├── insights_patterns.json
│   │   ├── index.json               # {"date": "2026-03-19", "conversations": [...]}
│   │   └── ...
├── competitors/                     # Auto-built profiles
│   ├── techcorp_inc.json
│   └── battle_cards/
│       └── techcorp_inc_battle_card.json
├── documents/                      # Doc request tracking
│   ├── requests/2026-03-19/
│   │   └── doc_proposal_12345.json
│   ├── generated/2026-03-19/
│   │   └── doc_proposal_12345.md
│   └── index.json
├── patterns/                       # Learned code patterns
│   └── solution_consultant_patterns.json
├── notes.json                      # Centralized knowledge
│   {
│     "facts": [{"timestamp": "...", "content": "...", "source": "..."}],
│     "preferences": [...],
│     "knowledge_gaps": [...],
│     "decisions": [...],
│     "approval_patterns": [...],
│     "conversation_experiences": [...]
│   }
├── learnings.json                  # Reflection summaries
│   [
│     {
│       "recurring_intents": ["deal status queries"],
│       "user_preferences": {"detail_level": "high"},
│       "knowledge_gaps": ["pricing models unclear"],
│       "generated_at": "2026-03-19T07:00:00",
│       "experience_count": 127
│     },
│     ...
│   ]
├── active_persona.json             # Current persona state
└── experience.jsonl                # Raw experience log (append-only)
```

**Key Principle**: Everything is **append-only** or **upsert**. No deletions. Full audit trail.

---

## Self-Evolution in Action: A Complete Example

### Scenario: User asks about a competitor

**Step 1: Message Received**
```
User (Telegram): "How do we compete against TechCorp Inc?"
```

**Step 2: Telegram Bot Processes**
- Adds typing indicator
- Builds context:
  ```
  System: "You are JARVIS... Current Role: Solution Consultant...
          Competitor Intelligence: TechCorp Inc mentioned 3 times..."
  History: [previous 10 messages]
  User: "How do we compete against TechCorp Inc?"
  ```
- Calls LLM (NVIDIA Step-3.5-Flash)
- Receives response:
  ```
  "We compete on integration flexibility and total cost of ownership. 
  TechCorp has limited API access and higher licensing fees. 
  Our deployment is 50% faster. Need a battle card?"
  ```

**Step 3: Response Sent & Events Published**
- Sends reply to user
- Publishes `telegram.response` event:
  ```json
  {
    "type": "telegram.response",
    "source": "telegram_bot",
    "data": {
      "user_id": 7354158438,
      "response": "We compete on integration flexibility...",
      "original_message": "How do we compete against TechCorp Inc?"
    }
  }
  ```

**Step 4: Conversation Summarization Skill Triggers**
- Listens to `telegram.response`
- Creates `MEMORY/summaries/2026-03-19/conv_telegram_7354158438_123456.json`
- Extracts insights via LLM:
  ```json
  {
    "entities": {
      "competitors": [{"name": "TechCorp Inc"}]
    },
    "intent": "competitive_comparison",
    "facts": ["TechCorp has limited API access", "TechCorp higher licensing fees", "Our deployment 50% faster"],
    "knowledge_gaps": [],
    "summary": "User asked about competing against TechCorp Inc, response highlighted integration flexibility and TCO advantages."
  }
  ```
- Updates `index.json` for today
- Triggers `CompetitiveIntelligenceSkill`

**Step 5: Competitive Intelligence Skill Updates**
- Receives insights with `entities.competitors`
- Loads/creates `MEMORY/competitors/techcorp_inc.json`
- Updates:
  ```json
  {
    "name": "TechCorp Inc",
    "mentions_count": 4,  // incremented
    "differentiators": ["integration flexibility", "faster deployment", "lower TCO"],  // appended
    "last_updated": "2026-03-19T07:15:00"
  }
  ```
- Generates battle card:
  ```json
  {
    "competitor": "TechCorp Inc",
    "our_advantage_summary": "integration flexibility\nfaster deployment\nlower TCO",
    "their_weaknesses": ["limited API access", "higher licensing fees"],
    "winning_strategy": ["emphasize integration flexibility", "highlight TCO"]
  }
  ```
- Stores in `MEMORY/competitors/battle_cards/techcorp_inc_battle_card.json`

**Step 6: Conversation Learner Processes**
- Receives both `telegram.message` and `telegram.response`
- Adds to experience buffer
- Extracts additional insights: user's communication style, depth of technical detail requested
- Updates `notes.json` with preference patterns

**Step 7: Pattern Recognition**
- If this conversation led to file changes (e.g., updated battle card file), file observer detects
- Pattern recognition notes: "battle_card_*.json updated frequently when competitor queries happen"
- Future: could suggest creating battle card templates proactively

**Step 8: Reflection (30 min cycle)**
- LLM analyzes last 100 experiences
- Notices: "Competitor queries frequently result in battle card creation"
- Updates `learnings.json`:
  ```json
  {
    "recurring_intents": ["competitive_comparison", "deal_status"],
    "successful_patterns": ["providing specific differentiators", "offering battle cards"],
    "focus_changes": ["increased competitor interest this week"],
    "generated_at": "2026-03-19T07:30:00"
  }
  ```
- Next system prompt rebuild includes: "Users frequently ask about competitors. Have battle cards ready."

**Step 9: Next Time**
When user asks "What's our advantage vs TechCorp?", JARVIS:
- Has battle card ready in context
- Can reference specific stored differentiators
- Response is faster, more comprehensive
- May proactively offer to generate updated battle card

**Result**: The system learned and improved from a single conversation.

---

## Persona-Specific Use Cases

### Solution Consultant Persona

**Primary Focus**: Technical architecture, demos, integration planning

#### Use Case 1: Technical Deep Dive
```
User: "How would we integrate our CRM with their API?"
```
**What JARVIS Does**:
- Checks learned patterns: "API integrations common in this workspace"
- Reviews past integration examples from file changes
- Accesses notes on preferred tech stack
- Generates detailed integration plan with code snippets
- Stores method in `notes.json` for future reference

**Knowledge Used**:
- Pattern recognition: Typical integration structures seen in codebase
- File history: Previous successful integrations
- Notes: Client-specific constraints

#### Use Case 2: Demo Preparation
```
User: "Prepare demo for TechCorp showing integration flexibility"
```
**What JARVIS Does**:
- Retrieves TechCorp battle card from `competitors/`
- Finds relevant integration patterns from `patterns/`
- Checks which features TechCorp's competitors lack
- Generates demo script highlighting differentiators
- Saves to `MEMORY/documents/generated/` with link to TechCorp profile

**Files Updated**:
- `documents/generated/demo_techcorp_YYYY-MM-DD.md`
- `documents/index.json` entry with link to TechCorp competitor file

### Account Executive Persona

**Primary Focus**: Business development, negotiations, deal strategy

#### Use Case 1: Deal Status Inquiry
```
User: "What's the status of the TechCorp deal?"
```
**What JARVIS Does**:
- Searches `deals.json` for "TechCorp"
- Extracts from conversation history: last discussion about this deal
- Uses LLM to synthesize: "TechCorp: $50K opportunity, in negotiation phase, budget approved, technical eval complete"
- Suggests next actions based on similar deal patterns

**Files Updated**:
- `deals.json` (if new info provided)
- `notes.json` with deal timeline

#### Use Case 2: Competitor Threat
```
User: "TechCorp just lowered prices. How should we respond?"
```
**What JARVIS Does**:
- Loads TechCorp profile from `competitors/techcorp_inc.json`
- Reviews battle card tactics
- Analyzes note: "TechCorp's weakness: limited support"
- Suggests: "Don't match price. Emphasize support SLA and integration cost savings"
- Logs strategy in decision log

**Files Updated**:
- `notes.json` (decisions category)
- May create new battle card update

---

## Capabilities Checklist

### Out of the Box (Currently Working)

| Capability | Status | Example |
|-----------|--------|---------|
| Natural conversation | ✅ | "What deals are active?" → lists from `deals.json` |
| File change learning | ✅ | Editing `.py` files → pattern recognition updates |
| Workspace isolation | ✅ | OpenCode in other folder → ignored |
| Conversation storage | ✅ | Every chat → `MEMORY/summaries/YYYY-MM-DD/` |
| Insight extraction | ✅ | "TechCorp deal $50K" → auto-updates `deals.json` |
| Competitor profiling | ✅ | Mention competitor → profile + battle card auto-created |
| Documentation tracking | ✅ | "Send me the proposal" → request logged, fulfilled tracked |
| Reflection | ✅ | Every 30 min → `learnings.json` updated |
| Cross-linking | ✅ | Deal mentioned → linked in summary index |
| Long response handling | ✅ | >4000 chars → auto-split |
| Per-user memory | ✅ | Each user's last 40 messages stored |
| Typing indicators | ✅ | Shows "typing..." while thinking |
| LLM-powered routing | ✅ | No more keyword matching; uses intent classification |

### Configuration

**Telegram Bot** (`jarvis/config/jarvis.yaml`):
```yaml
telegram:
  bot_token: "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
  allowed_user_ids: []  # empty = all allowed (not recommended for prod)
  allow_conversational_chat: true
```

**LLM** (Option 1 – Use NVIDIA/OpenAI-compatible):
```yaml
llm:
  provider: "openai"  # using OpenAI-compatible API
  api_key: "YOUR_API_KEY_HERE"
  base_url: "https://integrate.api.nvidia.com/v1"
  model: "stepfun-ai/step-3.5-flash"
  temperature: 1
  max_tokens: 16384
```

**LLM** (Option 2 – Use the same AI as OpenCode chat):
```yaml
opencode_ai:
  enabled: true
  config_path: "~/.config/opencode/config.yaml"
```
When `opencode_ai.enabled` is `true`, JARVIS loads the `llm` section from your OpenCode config and ignores the local `llm` settings. This makes Telegram bot use exactly the same model as OpenCode.

**Workspace**:
```yaml
workspace_root: /path/to/your/workspace
```

---

## Monitoring & Verification

### Check System Health

```bash
# Is JARVIS running?
ps aux | grep orchestrator

# Live logs
tail -f logs/orchestrator_manual.log
tail -f logs/telegram_bot.jsonl

# Component count (15+ skills + core components)
grep "Component started" logs/orchestrator_manual.log | wc -l

# Memory growth
du -sh MEMORY/
ls MEMORY/summaries/  # should show today's date

# Conversation history per user
ls MEMORY/conversations/

# Competitor profiles built
ls MEMORY/competitors/*.json

# WebSocket alive?
nc -z localhost 8081 && echo "WS OK"
```

### Test Workspace Isolation

1. Open OpenCode with a **different** project folder
2. Make a conversation in that project
3. Wait 10 seconds
4. Check if `conversation.message` events appear in logs:
   ```bash
   grep "conversation.message" logs/orchestrator_manual.log
   ```
   **Should NOT see events** from that workspace (filtered by path)

### Test Self-Evolution

1. Send a Telegram message: "We have a deal with TechCorp for $100K"
2. Wait 5 seconds
3. Check `jarvis/data/personas/deals.json` - should have TechCorp deal added
4. Check `MEMORY/competitors/techcorp_inc.json` - should exist or be updated
5. Check `MEMORY/summaries/$(date +%Y-%m-%d)/` - should have conversation file
6. Check `notes.json` - should have new fact recorded

---

## Common Use Cases & Examples

### 1. Daily Standup Briefing
**User**: "What happened yesterday?"

**JARVIS**:
- Pulls from `MEMORY/summaries/YYYY-03-18/` (yesterday)
- Summarizes: file changes, conversations, approvals, scans
- Lists deals touched, patterns learned, competitors mentioned
- Provides actionable insights

**Behind the Scenes**:
- Scans yesterday's summary folder
- Aggregates insights from multiple sources
- Uses LLM to synthesize into coherent brief
- Stores today's summary of this interaction

### 2. Competitor Battle Preparation
**User**: "I'm meeting with competitor X next week. Prep me."

**JARVIS**:
- Loads competitor X profile from `MEMORY/competitors/x.json`
- Reviews all past discussions about X
- Checks which deals X was involved in
- Generates battle card with:
  - Our differentiators
  - Their known weaknesses
  - Winning strategies
- Saves as document in `documents/generated/`

**Behind the Scenes**:
- If no profile exists, asks probing questions to build one
- Extracts insights from memory
- Creates new battle card file
- Updates competitor mention count

### 3. Deal Review
**User**: "Show me the pipeline."

**JARVIS**:
- Lists all deals from `jarvis/data/personas/deals.json`
- For each deal, shows:
  - Client name
  - Budget
  - Status
  - Last activity (from conversation history)
- Sorts by priority (budget + recency)
- Highlights deals needing attention

**Behind the Scenes**:
- May trigger deal updates if user says "TechCorp deal moved to closing"
- Extracts status changes via LLM
- Updates `deals.json` accordingly

### 4. Pattern Analysis
**User**: "What patterns have you learned?"

**JARVIS**:
- Reads `MEMORY/patterns/solution_consultant_patterns.json`
- Summarizes: "I've learned 5 patterns from 234 file observations"
- Lists top patterns:
  - "SQL query optimization" (12 occurrences)
  - "API error handling" (8 occurrences)
  - "Configuration updates" (5 occurrences)
- Suggests: "You frequently optimize queries. Want me to watch for slow queries?"

**Behind the Scenes**:
- Pattern recognition updates with every file change
- Counts aggregated in `patterns.json`
- LLM interprets statistical patterns for user

### 5. Automatic Documentation
**User**: "Can you send me the integration doc for TechCorp?"

**JARVIS**:
- Checks `documents/requests/` for similar past requests
- Finds related generated docs
- If none exists:
  - Asks clarifying questions: "What specific integration details do you need?"
  - Uses LLM to generate doc based on:
    - TechCorp competitor profile
    - Known integration patterns from `patterns/`
    - Past similar docs
  - Saves to `documents/generated/`
  - Marks request as fulfilled
  - Links doc to TechCorp competitor file

---

## Technical Deep Dive

### Event Flow Example: From File Edit to Knowledge Update

```
1. Developer edits: src/api/client.py
   ↓
2. watchdog detects modification
   ↓
3. FileSystemEventHandler.on_modified()
   ↓
4. Publish: Event("file.modified", "file_system", {"path": "...", ...})
   ↓
5. PatternRecognition subscribes to file.modified
   ↓
6. PatternRecognition analyzes change:
   - Reads diff
   - Matches against known patterns
   - If new pattern: updates MEMORY/patterns/...
   - Increments pattern count
   ↓
7. Publishes: Event("pattern.discovered", "pattern_recognition", {...})
   ↓
8. ConversationLearner receives pattern.discovered
   ↓
9. Adds to experience buffer
   ↓
10. (Later) Reflection runs, notices: "Pattern X appears frequently"
    - Updates learnings.json
    - Could suggest: "You're using pattern X a lot. Should I automate it?"
```

### Conversation Memory Structure

```json
{
  "user_id": 7354158438,
  "history": [
    {
      "role": "user",
      "content": "Hi",
      "timestamp": "2026-03-19T06:30:00"
    },
    {
      "role": "assistant",
      "content": "👋 Hello! I'm JARVIS...",
      "timestamp": "2026-03-19T06:30:02"
    },
    {
      "role": "user",
      "content": "What deals are active?",
      "timestamp": "2026-03-19T06:31:00"
    },
    ...
  ]
}
```
- Stored in `MEMORY/conversations/{user_id}.json`
- Last 40 messages (20 exchanges) kept
- Passed to ContextBuilder for LLM context
- Also published as `telegram.message`/`telegram.response` events for learner

### System Prompt Construction

```python
# From ContextBuilder._get_system_prompt()

patterns_summary = f"Learned {patterns_count} patterns from {files_observed} files."
recent_patterns = ["- API error handling (12 times)", "- Config reload (5 times)"]

competitors_summary = "Detected 3 competitors with 15 total mentions."
competitor_details = ["- TechCorp Inc: 8 mentions", "- Globex: 5 mentions", "- Waynes: 2 mentions"]

deals_summary = "Managing 4 active deals with total value $245,000"
deals_info = [
  "- TechCorp Integration ($100K)",
  "- Globex Migration ($80K)",
  "- Waynes Cloud ($50K)",
  "- Soylent AI ($15K)"
]

system_prompt = f"""
You are JARVIS, an autonomous AI employee working in 'OPENCODE SPACE'.

Current Role: Solution Consultant
{persona_desc}

Your Knowledge (Real-time workspace data):

Workspace Overview:
- {patterns_summary}
{recent_patterns}

Competitor Intelligence:
- {competitors_summary}
{competitor_details}

Active Deals:
- {deals_summary}
{deals_info}

System Status:
- System has approved 12/50 modifications autonomously.

Capabilities:
1. Answer questions about work, patterns, deals, workspace
2. Help with technical consulting, sales strategy, deal management
3. Trigger actions: /scan, /archive, /status, /persona, /deals, /patterns, /competitors
4. Provide insights from learned patterns

Persona: Concise, direct, professional. You are an AI employee who is always watching and learning.

Respond helpfully. If asked to perform an action, confirm briefly and execute (via internal mechanisms).
Use Markdown for formatting when appropriate.
"""
```

---

## Extension Points: Adding New Skills

### Example: Meeting Scheduler Skill

Create `jarvis/skills/meeting_scheduler.py`:

```python
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from datetime import datetime, timedelta

class MeetingSchedulerSkill:
    def __init__(self, config_manager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.meeting_scheduler")
    
    async def start(self):
        # Listen for meeting requests
        self.event_bus.subscribe("telegram.message", self._detect_meeting_intent)
        self.logger.info("Meeting scheduler skill started")
    
    async def _detect_meeting_intent(self, event: Event):
        message = event.data.get("message", "").lower()
        if "schedule" in message and "meeting" in message:
            await self._handle_schedule_request(event.data)
    
    async def _handle_schedule_request(self, data: dict):
        user_id = data["user_id"]
        message = data["message"]
        
        # Extract time, participants using LLM
        # Check calendar (would need integration)
        # Propose times
        # Log meeting in MEMORY/meetings/
        
        self.logger.info("Scheduled meeting", user_id=user_id, message=message[:50])
```

Register in `orchestrator.py`:

```python
from jarvis.skills.meeting_scheduler import MeetingSchedulerSkill

COMPONENT_CLASSES = {
    ...
    'meeting_scheduler': MeetingSchedulerSkill,
}

init_order = [
    ...
    'meeting_scheduler',  # after conversation_summarizer
    ...
]
```

Skill automatically:
- Listens to events
- Extracts insights
- Updates knowledge files
- Participates in self-evolution

---

## Troubleshooting

### Problem: Bot says "checking" but no response

**Cause**: LLM call timing out or error.

**Check**:
```bash
tail -f logs/telegram_bot.jsonl | grep "LLM"
```

**Fix**: Verify NVIDIA API key is valid and `base_url` correct.

### Problem: File observer crashes with "no event loop"

**Status**: ✅ **FIXED** in current version  
The handler now receives main loop at startup and uses `call_soon_threadsafe`.

### Problem: Not learning from OpenCode chats

**Check workspace filtering**:
```bash
grep "Conversation observer" logs/orchestrator_manual.log
# Should show: "db: ~/.local/share/opencode/opencode.db"
```

**Verify session directory**:
```sql
SELECT directory FROM session WHERE id = ? LIMIT 1;
```
Must start with `/path/to/your/workspace/`

### Problem: Memory growing too fast

**Normal**: JARVIS stores everything. This is by design.

**Archive old summaries**:
```bash
# Move old dates to archive
mkdir -p MEMORY/archives/summaries
mv MEMORY/summaries/2026-02-* MEMORY/archives/summaries/
```

**Adjust reflection buffer** in `conversation_learner.py`:
```python
self.max_buffer_size = 500  # default 1000
```

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Startup time | ~15 seconds |
| Memory footprint | ~200MB (varies with LLM cache) |
| Disk growth | ~1-10MB/day (depends on activity) |
| LLM latency | 2-5 seconds per response (NVIDIA API) |
| Event processing | <100ms for most events |
| Reflection cycle | 30 minutes (non-blocking) |

---

## Future Roadmap (Ideas)

1. **Proactive Suggestions**: "You haven't followed up with TechCorp in 3 days"
2. **Automated Battle Card Updates**: Pull competitor news from web
3. **Deal Forecasting**: Predict close probability based on patterns
4. **Full CLI Implementation**: Replace placeholder with `jarvis status`, `jarvis persona`, etc.
5. **Advanced Telegram Bridge**: Extended notification and interaction support
6. **Meta-Learning Cycle**: Enable the self-evolution loop via MetaLearner
7. **Semantic Search**: Embedding-based search in context_engine for deeper planning
8. **Export/Import**: Archive entire knowledge base for portability

---

## Conclusion

JARVIS is not just another AI tool. It's a **self-improving ecosystem** that:

1. **Sees everything** in your workspace (files + chats)
2. **Learns continuously** (patterns, facts, preferences)
3. **Organizes automatically** (date folders, cross-links)
4. **Remembers forever** (append-only storage)
5. **Gets smarter** every 30 minutes (reflection)
6. **Stays isolated** (one workspace per instance)

**It's like having an employee who never forgets, never sleeps, and continuously improves.**

The system is **running now** with 14 components. All you need to do is chat naturally. JARVIS handles the rest.

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `./fireup_jarvis.sh` | Start all JARVIS components |
| `tail -f logs/orchestrator_manual.log` | Watch orchestrator logs |
| `tail -f logs/telegram_bot.jsonl` | Watch Telegram bot messages |
| `ls MEMORY/summaries/` | See conversation archives by date |
| `cat MEMORY/competitors/techcorp_inc.json` | View competitor profile |
| `grep "pattern.discovered" logs/` | See pattern learning events |
| `ps aux \| grep orchestrator` | Check if running |
| `kill <PID>` | Stop orchestrator (or use Ctrl+C if foreground) |

---

**Document Version**: 2.1  
**Last Updated**: 2026-03-27  
**System Status**: ✅ Operational (15+ skills active)  
**Art of JARVIS** - Because true AI should evolve, not just respond.
