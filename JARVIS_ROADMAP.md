# JARVIS Roadmap — What's Built & What's Next

> Personal AE+SC Sales Assistant for Yellow.ai
> NVIDIA 24/7 background processing · Claude Desktop MCP interface · Fully local · Self-learning

---

## What's Live (as of 2026-03-29)

| Component | What it does |
|-----------|-------------|
| **NVIDIA LLM engine** | Primary workhorse — Nemotron-49B for text, Cosmos-Reason2-8B for video, Whisper for audio. Claude only for polished docs. |
| **MCP server** | 11 tools + 4 resource types exposed to Claude Desktop. Full deal dossier, MEDDPICC, battlecards, pipeline view. |
| **Meeting pipeline** | Drop .mp4/.wav → auto-identifies account → transcribes → extracts frames → analyzes slides → structured summary. |
| **RecordingRouter** | 4-layer confidence scoring to find the right account from any dropped recording file. |
| **Playbook engine** | Stage tracking (New → Discovery → Demo → Proposal → Negotiation → Close). Stale deal alerts every 6h. |
| **5 new skills** | meeting_summary, meeting_prep, proposal_generator, followup_email, deal_stage_tracker. |
| **AccountWatcher** | Central reactive router — maps every file change to the right semantic event + right skill chain. |
| **ConversationExtractor** | Watches JARVIS_BRAIN.md entries written by Claude → routes intelligence to ACCOUNTS/ automatically. |
| **DocumentProcessor** | Drop RFP/contract/brief in DOCUMENTS/ → NVIDIA extracts intel → triggers relevant skills. |
| **KnowledgeBuilder** | Fills account intel gaps every 6h (NVIDIA). Scans claude space every 5 min for new files to extract from. |
| **SelfLearner** | Weekly prompt evolution: tracks which outputs you edited → NVIDIA rewrites underperforming prompts. |
| **AccountAutoInitializer** | Creates full folder structure (MEETINGS/ DOCUMENTS/ EMAILS/ INTEL/) when new account detected. |
| **ClaudeSyncManager** | Notification bridge between JARVIS background events and Claude Desktop. |
| **setup.sh + start_jarvis.sh** | One-command setup + startup. MCP auto-registered with Claude Desktop. |
| **CLAUDE_SYSTEM_PROMPT.md** | Paste once into Claude Desktop — makes Claude always write structured entries to JARVIS_BRAIN.md. |

---

## Roadmap: Next 4 Weeks

### Week 1 — Intelligence Sharpening

#### 1. Account News Monitor
**What**: Every morning at 7am, NVIDIA searches for news about each active account (funding, leadership, product launches, layoffs). Writes digest to `INTEL/news_YYYY-MM-DD.md`.
**Why it matters**: Show up to every call knowing what just happened at their company. Instant credibility.
**Build**: `jarvis/brain/news_monitor.py` — asyncio cron, calls NVIDIA with company name + last-known context. Publishes `account.news.updated`.
**Estimate**: 1 day

#### 2. Deal Velocity Score
**What**: Composite score (0–100) measuring deal momentum: days-since-last-activity, MEDDPICC delta over time, email response rate, stage progression speed. Shown in `jarvis_get_pipeline`.
**Why it matters**: Instantly spot which deals are stalling before your manager does.
**Build**: `jarvis/skills/deal_velocity_skill.py` — runs on `meddpicc.updated` and `deal_stage.json` changes. Writes `velocity.json` per account.
**Estimate**: 1 day

---

### Week 2 — Communication Intelligence

#### 3. Style-Learning Email Drafts
**What**: KnowledgeBuilder tracks which follow-up email drafts you sent vs. edited heavily. SelfLearner evolves the `followup_email` prompt to match your actual writing style over time.
**Why it matters**: JARVIS emails start sounding like you, not like a template. Zero editing required after 3–4 deal cycles.
**Build**: Existing SelfLearner + FollowupEmailSkill already half-built for this. Add `jarvis_rate_output` MCP tool to capture signal.
**Estimate**: 1.5 days

#### 4. Email Thread Intelligence
**What**: When you paste (or Claude reads via Gmail MCP) an email thread into JARVIS, NVIDIA extracts: sentiment, objections raised, buying signals, next steps implied. Updates MEDDPICC automatically.
**Why it matters**: Never miss a buried objection in a 20-email thread again.
**Build**: Extend `DocumentProcessor` to handle email format (text/plain). Add email-specific extraction prompt.
**Estimate**: 1 day

#### 5. Voice Note → Action Items
**What**: Record a 2-minute voice memo after a call (no meeting platform needed). JARVIS transcribes it, extracts action items, updates MEDDPICC.
**Why it matters**: Capture deal intelligence while walking to your car. Zero friction.
**Build**: `jarvis/meeting/voice_note_processor.py` — watches `MEETINGS/voice_notes/`. Whisper → NVIDIA extraction → `activities.jsonl`.
**Estimate**: 0.5 days

---

### Week 3 — Proposal & Demo Intelligence

#### 6. Two-Agent Proposal Generation
**What**: NVIDIA (Agent 1) assembles raw proposal data from all account intel. Claude (Agent 2) polishes into a professional doc. Result: a proposal that takes 10 minutes instead of 3 hours.
**Why it matters**: Each agent does what it's good at. NVIDIA knows your deal. Claude writes beautifully.
**Build**: `jarvis/skills/proposal_generator_skill.py` — Phase 1: NVIDIA builds structured brief. Phase 2: Claude MCP tool call returns polished SOW/PPT outline.
**Estimate**: 2 days

#### 7. Demo Intelligence Feed
**What**: Before each demo, JARVIS generates a "demo intelligence card" — which pain points to hit hardest (from discovery), which features to skip, competitive objections likely to come up, suggested demo flow.
**Why it matters**: Stop demoing the same generic flow. Demo exactly what they care about.
**Build**: Extend `DemoStrategySkill` to pull from MEDDPICC pain points + competitive intel. Triggered by calendar event or manual `jarvis_prep_for_meeting`.
**Estimate**: 1 day

---

### Week 4 — Outcomes & Memory

#### 8. Outcome Tracker
**What**: When you mark a deal won or lost, JARVIS runs a full retrospective: what signals predicted it, what was missed, what playbook actions worked. Writes to `MEMORY/win_loss_patterns.md`. SelfLearner uses this to tune MEDDPICC weighting.
**Why it matters**: Win more deals like the ones you won. Stop repeating the pattern that lost the last three.
**Build**: `SelfLearner._analyze_deal_history()` is already built. Add `jarvis_mark_deal_outcome` MCP tool + `deal.won`/`deal.lost` event triggers.
**Estimate**: 1 day

#### 9. Auto-Calendar Brief
**What**: 30 minutes before each meeting (pulled from Google Calendar via Claude MCP), JARVIS auto-generates a prep brief and pushes a notification. Brief includes: account context, last 3 touchpoints, open MEDDPICC gaps, suggested questions.
**Why it matters**: Walk into every call prepared. No last-minute scramble.
**Build**: `MeetingPrepSkill` is built. Need: cron in `PlaybookAutomationEngine` that checks calendar data written by Claude and triggers prep 30 min before. Or triggered manually via `jarvis_prep_for_meeting`.
**Estimate**: 1 day

#### 10. Cross-Deal Pattern Intelligence
**What**: Monthly synthesis across all won/lost deals, MEDDPICC patterns, common objections, competitive win rates. Writes to `MEMORY/patterns/cross_deal_insights.md`. Informs discovery question generation.
**Why it matters**: Build institutional sales memory that compounds. 6 months from now, JARVIS knows your territory better than any CRM.
**Build**: `KnowledgeBuilder.build_cross_deal_patterns()` is already built. Add monthly cron trigger.
**Estimate**: 0.5 days (mostly plumbing)

---

## The Self-Learning Loop (How JARVIS Gets Smarter Over Time)

```
Every conversation with Claude in claude space
        ↓
Claude writes structured entry to JARVIS_BRAIN.md
        ↓
ConversationExtractor routes intelligence to ACCOUNTS/
        ↓
KnowledgeBuilder scans claude space every 5 min for new files
        ↓
NVIDIA extracts insights → routes to MEMORY/ knowledge base
        ↓
Every 6 hours: KnowledgeBuilder fills INTEL/ gaps per account
        ↓
Every Sunday: SelfLearner reviews which outputs you edited heavily
        ↓
NVIDIA rewrites underperforming prompt templates
        ↓
Next week: skills produce outputs closer to what you actually want
```

The more you use JARVIS, the less you have to edit its outputs.

---

## How to Use JARVIS Day-to-Day

```bash
# Start JARVIS (background daemon, NVIDIA processing 24/7)
./start_jarvis.sh

# Stop JARVIS
./stop_jarvis.sh

# Claude Desktop — paste CLAUDE_SYSTEM_PROMPT.md into custom instructions once
# Then use normally:
# "list my accounts"
# "prep me for the Acme meeting"
# "process this recording: /path/to/call.mp4"
# "what's my MEDDPICC for TechCorp?"
# "draft follow-up for today's Acme call"
# "create proposal for Acme Corp"
# "show me my pipeline"
```

---

## Moving to a New Machine (Yellow.ai Laptop)

```bash
git clone git@github.com:younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
./setup.sh          # installs deps, creates ~/JARVIS/, registers Claude Desktop MCP
nano .env            # add NVIDIA_API_KEY
./start_jarvis.sh   # JARVIS running
# Open Claude Desktop → JARVIS MCP auto-registered → working
```

Optionally copy `~/JARVIS/ACCOUNTS/` from old machine to carry deal history.
