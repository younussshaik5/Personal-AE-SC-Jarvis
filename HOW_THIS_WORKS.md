# JARVIS — How This Works: Complete Start-to-End Guide

> Personal AI Sales Assistant for Yellow.ai AE+SC
> NVIDIA 24/7 background · Claude Desktop as UI · Fully local · No cloud dependency

---

## What JARVIS Is

JARVIS is **not a chatbot**. It is a background AI employee that runs on your Mac 24/7, watches your work, and automatically builds sales intelligence — without you having to ask.

Two pieces working together:

```
Claude Desktop (your UI)          JARVIS daemon (background Python process)
        │                                   │
        │  ←── MCP tools ──────────────────►│
        │                                   │
  You talk to Claude.            NVIDIA processes everything:
  Claude calls JARVIS tools.     transcription, MEDDPICC scoring,
  Claude assembles polished       competitive analysis, email drafts,
  documents (proposals, SOWs).   gap-filling — 24/7, no Claude tokens.
```

**The rule**: NVIDIA handles all background processing (free-ish, continuous). Claude handles the polished output you want to send to a customer (on demand, uses your token budget).

---

## Prerequisites

| Requirement | Why |
|-------------|-----|
| Python 3.9+ | JARVIS daemon |
| Node.js 18+ | MCP server for Claude Desktop |
| ffmpeg | Meeting recording → audio extraction |
| NVIDIA API key | ALL background LLM processing (only paid dependency) |
| Claude Desktop | Your primary UI |

Get NVIDIA key: https://build.nvidia.com → sign up → API Keys

---

## First-Time Setup

### Step 1: Clone the repo

```bash
git clone git@github.com:younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

### Step 2: Run setup

```bash
./setup.sh
```

This will:
- Check Python, Node.js, ffmpeg are installed
- Install all Python dependencies (`requirements-jarvis.txt`)
- Build the MCP server (`mcp-jarvis-server/`)
- Create your JARVIS home directory (`~/JARVIS/` by default)
- **Ask you: "Where is your Claude workspace folder?"** — type the full path to the folder where you use Claude Desktop / Claude Code. This is what JARVIS watches to extract intelligence from your conversations.
- Copy `.env.example` → `.env`
- Auto-register JARVIS MCP server with Claude Desktop

### Step 3: Add your NVIDIA API key

```bash
nano .env
```

Set:
```
NVIDIA_API_KEY=nvapi-your-key-here
JARVIS_HOME=/Users/yourname/JARVIS        # where data is stored
CLAUDE_SPACE=/Users/yourname/Documents/work  # your Claude workspace
```

### Step 4: Start JARVIS

```bash
./start_jarvis.sh
```

### Step 5: Configure Claude Desktop (one-time)

1. Open Claude Desktop
2. Go to **Settings → Custom Instructions** (or equivalent)
3. Copy the entire contents of `CLAUDE_SYSTEM_PROMPT.md` and paste it in
4. Save

That's it. Claude will now automatically write structured entries to JARVIS after every work conversation you have. You never need to do this again.

### Step 6: Test it

In Claude Desktop, type:
```
list my accounts
```

If JARVIS is running and MCP is connected, Claude will call `jarvis_list_accounts` and return results (empty list if no accounts yet — that's correct).

---

## Starting and Stopping

```bash
./start_jarvis.sh          # start everything
./stop_jarvis.sh           # stop everything

# Check what's running:
cat ~/JARVIS/logs/jarvis.log | tail -50

# Watch in real-time:
tail -f ~/JARVIS/logs/jarvis.log
```

---

## Folder Structure

Everything lives in `~/JARVIS/` (your `JARVIS_HOME`):

```
~/JARVIS/
│
├── ACCOUNTS/                 ← ONE FOLDER PER ACCOUNT OR OPPORTUNITY
│   │
│   ├── Acme Corp/            ← example account
│   │   ├── account.html      ← open in browser — live dashboard
│   │   ├── meddpicc.json     ← MEDDPICC scores (auto-updated)
│   │   ├── deal_stage.json   ← current stage + full history
│   │   ├── contacts.json     ← stakeholders and champions
│   │   ├── activities.jsonl  ← append-only activity log
│   │   ├── actions.md        ← action items (JARVIS updates this)
│   │   │
│   │   ├── MEETINGS/         ← DROP RECORDINGS HERE (mp4/wav/m4a)
│   │   ├── DOCUMENTS/        ← DROP RFPs, contracts, NDAs here
│   │   ├── EMAILS/           ← SAVE email threads here (.md/.txt)
│   │   ├── INTEL/            ← JARVIS auto-generates intel here
│   │   └── meetings/         ← processed meeting notes (JARVIS writes)
│   │
│   ├── Acme Corp - Q1 Deal/  ← separate opportunity (flat, same level)
│   │   ├── account.html
│   │   ├── meddpicc.json
│   │   └── ...same structure...
│   │
│   └── TechCorp/             ← another account
│       └── ...
│
├── MEETINGS/                 ← global drop folder (JARVIS auto-detects account)
├── MEMORY/                   ← cross-deal patterns, knowledge base
├── JARVIS_BRAIN.md           ← Claude writes here → JARVIS routes intel
├── logs/                     ← runtime logs
└── recordings/               ← processed recordings archived here
```

### Accounts vs Opportunities — JARVIS Makes No Distinction

Every folder in `ACCOUNTS/` is treated identically. You decide what it represents:

- `ACCOUNTS/Tata Sky/` — you're calling this an account
- `ACCOUNTS/Tata Tele/` — you're calling this a separate account
- `ACCOUNTS/Acme Corp - Digital Transformation 2026/` — you're calling this a specific deal
- `ACCOUNTS/Acme Corp/` — the parent account

JARVIS initializes all of them with the same files and starts building intelligence for all of them. The naming and organization is entirely up to you.

---

## How to Create a New Account or Opportunity

**Option A — Just create a folder:**
```bash
mkdir ~/JARVIS/ACCOUNTS/Acme\ Corp
```

Within a few seconds, JARVIS detects the new folder and automatically creates:
- `meddpicc.json` (all zeros)
- `deal_stage.json` (stage: new_account)
- `contacts.json` (empty)
- `activities.jsonl` (empty)
- `actions.md`
- `MEETINGS/`, `DOCUMENTS/`, `EMAILS/`, `INTEL/`, `meetings/` subfolders
- `account.html` (open in browser — will populate as intel builds)

Then JARVIS queues NVIDIA to start filling `INTEL/` with:
- `company_research.md` — who is this company, what do they need
- `competitive_analysis.md` — who you'll face, how to win
- `value_proposition.md` — tailored ROI and business case

**Option B — Tell Claude Desktop:**
```
Create account for Acme Corp
```
Claude can call `jarvis_save_meeting_context` or just create the folder path.

---

## How Meeting Processing Works

### Option A: Drop recording in account folder

```
You drop: ~/JARVIS/ACCOUNTS/Acme Corp/MEETINGS/call_2026-03-29.mp4

JARVIS detects the file (watchdog file watcher)
    ↓
AccountWatcher fires: meeting.recording.added {account: "Acme Corp"}
    ↓
MeetingProcessor runs pipeline:
    ffmpeg → extracts audio → .wav
    NVIDIA Whisper → transcribes → transcript.md
    ffmpeg → extracts video frames every 30s → frame_001.jpg, frame_002.jpg...
    NVIDIA Cosmos-Reason2-8B → analyzes each frame → slide_analysis.json
    ↓
MeetingSummarySkill combines transcript + slide analysis:
    → Attendees, key topics, decisions made
    → Action items extracted
    → MEDDPICC signals identified (pain points, metrics mentioned, etc.)
    → Follow-up email draft
    ↓
Written to: ACCOUNTS/Acme Corp/meetings/2026-03-29_call.md
meddpicc.json updated
account.html refreshed
```

### Option B: Drop in global MEETINGS/ folder (account unknown)

```
You drop: ~/JARVIS/MEETINGS/acme_call.mp4

RecordingRouter identifies the account:
    Layer 1: filename fuzzy match ("acme" → "Acme Corp") — instant
    Layer 2: transcribe first 3 minutes → look for company name — ~30 seconds
    Layer 3: NVIDIA NLP extraction from full transcript — ~2 minutes
    Layer 4: create new account folder if nothing matches

If confidence is low → you get a notification in Claude Desktop to confirm
→ Routes to correct ACCOUNTS/ folder and processes
```

### Option C: Tell Claude Desktop

```
"process this meeting recording at /path/to/call.mp4"
→ Claude calls jarvis_process_meeting() MCP tool
→ Same pipeline runs
```

---

## How Document Processing Works

```
You drop: ~/JARVIS/ACCOUNTS/Acme Corp/DOCUMENTS/Acme_RFP_2026.pdf

JARVIS detects file → DocumentProcessor activates
    ↓
NVIDIA extracts:
    Requirements and evaluation criteria
    Budget signals and timeline
    Stakeholders mentioned
    Technical requirements
    ↓
Written to: ACCOUNTS/Acme Corp/INTEL/rfp_analysis.md
    ↓
IF it's an RFP → ProposalGeneratorSkill assembles proposal brief
IF competitors mentioned → BattlecardsSkill triggers
    ↓
account.html refreshed
```

Supported file types: `.pdf`, `.docx`, `.doc`, `.txt`, `.md`, `.pptx`, `.xlsx`

---

## How Email Thread Processing Works

```
Save email thread as: ~/JARVIS/ACCOUNTS/Acme Corp/EMAILS/thread_john_march.md

JARVIS detects → NVIDIA extracts:
    Sentiment (positive / cautious / blocked)
    Objections raised
    Buying signals
    Action items implied
    Stakeholder positions
    ↓
Written to: ACCOUNTS/Acme Corp/activities.jsonl
meddpicc.json updated if relevant signals found
account.html refreshed
```

---

## How the Brain / Conversation Intelligence Loop Works

This is the key loop that makes JARVIS self-populating:

```
1. You chat with Claude Desktop about any account (normal conversation)

2. Because of the custom instructions you pasted once, Claude automatically
   writes a structured entry to ~/JARVIS/JARVIS_BRAIN.md at the end of the
   conversation. Format:
   <!-- JARVIS_ENTRY
   {"account": "Acme Corp", "type": "conversation", "signals": {...}}
   JARVIS_ENTRY_END -->

3. ConversationExtractor watches JARVIS_BRAIN.md (file watcher)
   → detects new entry within seconds
   → identifies the account via fuzzy matching
   → routes intelligence to ACCOUNTS/Acme Corp/

4. Writes to:
   activities.jsonl (what happened)
   INTEL/conversation_log.md (extracted intelligence)
   contacts.json (any new stakeholders mentioned)
   meddpicc.json (any MEDDPICC signals updated)

5. KnowledgeBuilder queues a gap-fill task (MEDIUM priority)
   → within 1-5 minutes, NVIDIA checks INTEL/ for missing files
   → fills any gaps (company_research, competitive_analysis, value_proposition)

6. account.html refreshed → open it and see updated intelligence
```

Also, if `CLAUDE_SPACE` is set in `.env`:

```
Any file you create or edit in your Claude workspace folder
    ↓ (FileSystemObserver detects change within seconds)
KnowledgeBuilder queues workspace_extract task
    ↓
NVIDIA reads the file and extracts:
    Account names mentioned → routes intel to those ACCOUNTS/ folders
    Product knowledge → saves to MEMORY/knowledge_product.md
    Competitive intel → saves to MEMORY/knowledge_competitive.md
    Insights → saves to MEMORY/knowledge_insights.md
```

---

## How the Task Queue Works (Why Nothing Gets Lost)

All NVIDIA work goes through a SQLite task queue (`~/JARVIS/data/task_queue.db`).

```
Event fires → task queued in SQLite → worker picks up → NVIDIA called → result written to disk

Priority levels:
  HIGH   (1) — meeting recordings, brain entries → processed first
  MEDIUM (2) — documents, emails, workspace files → processed next
  LOW    (3) — gap fills, pattern synthesis, HTML refresh → when workers are free

3 parallel workers run at all times (configurable in jarvis.yaml: queue.workers)

If NVIDIA returns an error:
  → task retried automatically up to 3 times
  → priority lowered slightly each retry (backoff)

If JARVIS crashes mid-task:
  → task is still in SQLite with status "in_progress"
  → on restart, stale in_progress tasks are retried

Deduplication:
  → same account getting 20 events at once = only 1 gap_fill task queued
  → no pile-up, no redundant NVIDIA calls
```

---

## How Claude Desktop MCP Tools Work

You never type these tool names. You just talk naturally to Claude, and Claude calls the right tool automatically.

| What you say to Claude | Tool called | What happens |
|------------------------|-------------|--------------|
| "list my accounts" | `jarvis_list_accounts` | All ACCOUNTS/ folders with stage + MEDDPICC score |
| "brief me on Acme Corp" | `jarvis_get_account` | Full dossier: all INTEL/ files, MEDDPICC, recent meetings, contacts, actions |
| "prep me for Acme meeting" | `jarvis_prep_for_meeting` | NVIDIA generates prep brief from all account data |
| "process this recording at /path" | `jarvis_process_meeting` | Runs full transcription + analysis pipeline |
| "save these notes for Acme" (paste notes) | `jarvis_save_meeting_context` | Writes to ACCOUNTS/Acme/meetings/, triggers MEDDPICC update |
| "save this email for Acme" (paste email) | `jarvis_save_email_context` | Writes to EMAILS/, extracts signals |
| "show my pipeline" | `jarvis_get_pipeline` | All accounts, stages, scores, stale deal flags |
| "battlecard vs Zendesk" | `jarvis_get_battlecard` | Competitive intel from MEMORY/competitors/ |
| "draft follow-up for Acme" | `jarvis_draft_followup` | NVIDIA generates follow-up from latest meeting notes |
| "search for Acme ROI discussion" | `jarvis_search` | Full-text search across all ACCOUNTS/ and MEMORY/ |

---

## How to Generate a Proposal or SOW

```
You: "create a proposal for Acme Corp"

Claude: calls jarvis_get_account("Acme Corp")
      → reads all INTEL/ files:
          company_research.md
          competitive_analysis.md
          value_proposition.md
          rfp_analysis.md (if you dropped an RFP)
          meddpicc_strategy.md
      → reads MEDDPICC scores, contacts, meeting summaries
      → Claude assembles a polished proposal using its own language intelligence

NVIDIA did the data work. Claude wrote the document.
```

This is the key division: NVIDIA extracts and builds the intelligence base. Claude uses that intelligence to write the polished customer-facing document.

---

## How the Self-Learning Loop Works

JARVIS adapts to your style over time:

```
You use a JARVIS output (follow-up email, meeting summary, etc.)

If you edit it heavily before sending:
  → output.edited event fires with the diff

If you rate it poorly via jarvis_rate_output:
  → output.rated event fires

After 3+ feedback signals on the same skill:
  → SelfLearner runs IMMEDIATELY (not on a schedule)
  → NVIDIA analyzes: what did you change, why did you change it
  → NVIDIA rewrites the prompt template for that skill
  → Next output from that skill is closer to what you want

This is NOT model training. The model weights don't change.
It's prompt evolution — the instructions JARVIS gives NVIDIA get better.
After a month of use, JARVIS outputs need almost no editing.
```

---

## Stale Deal Monitoring

Every 5 minutes, PlaybookAutomationEngine scans all accounts:

```
No activity for 7 days:
  → NVIDIA generates a nudge email draft
  → Written to ACCOUNTS/{name}/INTEL/stale_deal_nudge.md
  → Visible in jarvis_get_pipeline as "stale"

No activity for 14 days:
  → Flagged as "critical" in pipeline view
  → Nudge becomes more urgent
```

---

## How Google Workspace Works

JARVIS has **zero Google code**. Google integration goes through Claude's own MCP connectors.

```
You: "check my calendar for tomorrow"
Claude: [Google Calendar MCP connector] → reads your calendar
Claude: "You have: Acme Corp at 2pm, TechCorp at 4pm"

You: "prep me for the Acme meeting at 2pm"
Claude: [calls jarvis_prep_for_meeting("Acme Corp")]
JARVIS: [NVIDIA generates prep brief from all account data]
Claude: shows you the brief

After meeting:
You: "save these notes for Acme" [paste your notes]
Claude: [calls jarvis_save_meeting_context("Acme Corp", notes)]
JARVIS: [NVIDIA updates MEDDPICC, drafts follow-up]

You: "send the follow-up to john@acme.com"
Claude: [Gmail MCP connector] → sends the email
```

You set up Google MCP connectors directly in Claude Desktop (Settings → MCP Servers). JARVIS doesn't need any Google credentials.

---

## Works with Both Claude Desktop AND OpenCode

Both read from the same `~/JARVIS/ACCOUNTS/` folder:

- **Claude Desktop**: primary UI, full MCP tool set, best for proposals and polished docs
- **OpenCode**: use when Claude budget is low. Same JARVIS data, same background processing. JARVIS doesn't know or care which frontend you're using.

To switch: just open OpenCode instead of Claude Desktop. JARVIS keeps running in the background either way.

---

## Moving to a New Machine (Yellow.ai Laptop)

```bash
# On new machine:
git clone git@github.com:younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
./setup.sh
# → type your Claude workspace path when prompted
nano .env
# → NVIDIA_API_KEY=nvapi-your-key
# → JARVIS_HOME=/Users/yourname/JARVIS
# → CLAUDE_SPACE=/Users/yourname/Documents/your-claude-workspace
./start_jarvis.sh
# Open Claude Desktop → JARVIS MCP auto-registered
```

**To carry your deal history**: copy `~/JARVIS/ACCOUNTS/` from old machine to new machine before starting.

---

## What JARVIS Does NOT Do

| Does NOT | Why |
|----------|-----|
| Connect to Google directly | Google goes through Claude's own MCP connectors |
| Send emails | Claude does that via Gmail MCP |
| Train a model | Prompt evolution only — templates get rewritten, weights don't change |
| Access the internet | Uses NVIDIA LLM knowledge and your local files only |
| Modify your CRM | Everything stays in local ACCOUNTS/ files |
| Require internet for operation | All processing is API calls to NVIDIA; no other external dependencies |

---

## Troubleshooting

**JARVIS not starting:**
```bash
cat ~/JARVIS/logs/jarvis.log | tail -30
# Common: missing NVIDIA_API_KEY in .env
# Common: Python package missing → pip install -r requirements-jarvis.txt
```

**Claude Desktop not showing JARVIS tools:**
```bash
# Re-run MCP registration:
python3 scripts/register_mcp.py
# Then restart Claude Desktop
```

**Recordings not being processed:**
```bash
# Check ffmpeg is installed:
ffmpeg -version
# If not: brew install ffmpeg
```

**NVIDIA calls failing:**
```bash
# Check your API key:
cat .env | grep NVIDIA_API_KEY
# Check NVIDIA API status: https://status.build.nvidia.com
```

**account.html looks empty:**
```
Normal on day 1 — NVIDIA is still filling INTEL/ files.
Check the queue: cat ~/JARVIS/data/task_queue.db (SQLite viewer)
Or wait 5-10 minutes and refresh the HTML file.
```

---

## Quick Reference Card

```
Daily workflow:
1. ./start_jarvis.sh (or it auto-starts on login)
2. Open Claude Desktop
3. "list my accounts" → see pipeline
4. Drop recording in ACCOUNTS/{name}/MEETINGS/ → auto-processed
5. "brief me on {account}" → full intel brief
6. "create proposal for {account}" → polished doc

New account:
  mkdir ~/JARVIS/ACCOUNTS/Company\ Name → JARVIS auto-initializes

New opportunity (same company, different deal):
  mkdir ~/JARVIS/ACCOUNTS/Company\ Name\ -\ Project\ Name → same behavior

Check status:
  tail -f ~/JARVIS/logs/jarvis.log
  open ~/JARVIS/ACCOUNTS/{name}/account.html
```
