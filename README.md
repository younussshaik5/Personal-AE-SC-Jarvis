# JARVIS — Your Personal AI Sales Assistant

> *"What if you had an AI employee who attended every call, read every email, tracked every deal, and briefed you before every meeting — without you having to ask?"*

---

## The Problem Every Sales Person Knows

You're an Account Executive. You're also the Solution Consultant. You're running 10 deals at once.

Monday morning: "What was the status on Tata Sky? Who was the economic buyer? Did we send that proposal? What did they say about the timeline in last week's call?"

You dig through emails. You search Slack. You scroll through your notes app. You find bits and pieces. You piece it together. You get on the call — slightly underprepared.

This happens every single day. To every single salesperson.

**JARVIS fixes this.**

---

## What JARVIS Is

JARVIS is not a chatbot. It's not a CRM. It's not another tool you have to log into.

**JARVIS is a background AI employee who works 24/7 on your machine.**

He watches everything — your meeting recordings, your emails, your documents, your Google Calendar. He processes it all automatically using NVIDIA's most powerful AI models. He builds a living, breathing intelligence file for every account you're working on.

Then, when you open Claude Desktop and ask "brief me on Tata Sky" — in 10 seconds you have everything. The last three meetings summarized. The MEDDPICC score. The competitive positioning. The open action items. The champion's name. The budget that was mentioned in passing six weeks ago.

You never had to type a single note.

---

## How It Works — The Full Picture

```
Your World                    JARVIS (Background)              You Get
─────────────────────         ────────────────────────         ──────────────────
Meeting recording    ──────→  Transcribe (Whisper AI)    ──→  Meeting summary
Email from buyer     ──────→  Extract signals             ──→  MEDDPICC update
RFP document         ──────→  Parse requirements          ──→  Proposal brief
Calendar event       ──────→  Prep automatically          ──→  Meeting brief
Google Drive doc     ──────→  Extract intel               ──→  Stakeholder map
You asking Claude    ──────→  Pull all intel              ──→  Instant answer
```

Everything goes through an **async task queue**. JARVIS processes multiple accounts in parallel using different NVIDIA AI models simultaneously — each model doing what it's best at:

| What's happening | AI Model doing it |
|---|---|
| Transcribing your meeting recording | Whisper Large v3 Turbo |
| Analyzing slides and video frames | NVIDIA Cosmos Reason2 8B |
| Building company research, value prop | Nemotron Super 49B |
| Analyzing a 200-page RFP | Nemotron 3 Super 120B (1M token context) |
| Deep deal strategy, win/loss analysis | Nemotron Ultra 253B |
| Fast tagging, classification | Minitron 8B |

Nothing waits for anything else. It all runs concurrently, 24/7, while you're on other calls.

---

## What Happens For Each Account

The moment you create a folder in `ACCOUNTS/`, JARVIS initializes it and starts building intelligence automatically:

```
ACCOUNTS/
  Tata Sky/
    account.html          ← Open in browser. Live dashboard. Auto-updated.
    meddpicc.json         ← 8-dimension deal score. Updated after every interaction.
    deal_stage.json       ← Current stage + full history
    contacts.json         ← Every stakeholder, their role, their sentiment
    activities.jsonl      ← Timeline of everything that happened
    actions.md            ← Open action items. JARVIS tracks these.

    MEETINGS/             ← Drop your recording here. JARVIS does the rest.
    DOCUMENTS/            ← Drop RFPs, contracts, proposals here.
    EMAILS/               ← Paste email threads here.
    INTEL/                ← JARVIS auto-generates these:
      company_research.md     (who they are, industry, tech stack, news)
      competitive_analysis.md (who you're up against, how to win)
      value_proposition.md    (ROI in their language, talking points)
      meddpicc_strategy.md    (what's weak, what to fix, what to ask)
    meetings/             ← Processed meeting notes (JARVIS writes these)
```

You never create any of these files. JARVIS creates them. You just drop files in folders.

---

## MEDDPICC — Built In, Always On

Every sales interaction is automatically scored across 8 dimensions:

| Dimension | What JARVIS Watches For |
|---|---|
| **M** Metrics | Numbers, ROI, cost savings mentioned in emails/calls |
| **E** Economic Buyer | CFO, VP, final decision maker identified |
| **D** Decision Criteria | Evaluation criteria, requirements documents |
| **D** Decision Process | Procurement steps, approvals needed |
| **P** Paper Process | Legal review, security questionnaire, contracts |
| **I** Implicated Pain | Problems, frustrations, bottlenecks they describe |
| **C** Champion | Internal advocate found? How strong are they? |
| **C** Competition | Which competitors mentioned, how often, in what context |

Each dimension scored 0–3. Total score tells you exactly where the deal is strong and where it's bleeding. JARVIS flags it. You fix it.

---

## Google Workspace — Fully Connected

Connect Gmail, Google Calendar, and Google Drive to Claude Desktop once. After that, JARVIS pulls intelligence from everything automatically.

**Gmail:** Claude reads an email from your Tata Sky contact. JARVIS finds the right account folder, saves the thread, extracts buying signals, updates MEDDPICC. You see: *"Budget approved mentioned — Economic Buyer score updated."*

**Calendar:** You have a "Tata Sky Demo" at 2pm. JARVIS reads the event, reads everything it knows about Tata Sky, and has a complete meeting brief ready 30 minutes before your call. You didn't ask for it. It's just there.

**Drive:** Someone shares an RFP document. JARVIS reads it, extracts requirements, budget, timeline, stakeholders, and which competitors they mentioned. Saved to the account folder automatically.

**After a meeting ends:** Claude asks "Want me to save notes for Tata Sky?" You say yes, dictate or type a quick summary. JARVIS updates MEDDPICC, clears the stale flag, queues a follow-up draft.

---

## Your Day With JARVIS

### Morning

```
You: "What's my day?"

JARVIS + Claude:
  Today's meetings:
  • 10am — Tata Sky (Discovery call, Day 2)
    MEDDPICC: 14/24. Weak: Economic Buyer, Champion. Push on these today.
    Last interaction: Email 3 days ago. They asked about security compliance.
    Prep: Lead with the security architecture slide. Ask about budget approval process.

  • 2pm — Acme Corp (Demo)
    MEDDPICC: 19/24. Strong position. Competitor: Freshdesk mentioned twice.
    Prep: Show the Freshdesk comparison slide. Focus on their CRM integration pain.

  Pipeline alerts:
  • TechCorp — no activity in 9 days. Stale. Follow up today.
  • Reliance Jio — proposal sent 12 days ago. No response. Nudge needed.
```

### Before a call

```
You: "Prep me for the Tata Sky call. Attendees: Rahul (CTO), Priya (Procurement)"

JARVIS: Full brief in 10 seconds.
  Pain points raised in previous calls.
  What Rahul cares about (technical depth, security).
  What Priya cares about (timeline, vendor process, SLAs).
  3 questions to ask that move the deal forward.
  The one thing that killed our last deal with a similar company.
```

### After a call

```
You: "Save notes. Budget confirmed $200K. Timeline Q2. Need security review.
      Priya is our champion now."

JARVIS: Notes saved. MEDDPICC updated.
  Paper Process score: 2 (security review triggered).
  Champion score: 3 (confirmed internal advocate).
  Follow-up email draft: ready in 2 minutes.
```

### End of day

```
You: "What did I close today?"

JARVIS: Pipeline update.
  2 deals advanced to next stage.
  1 follow-up sent.
  3 new intel files generated.
  1 deal (TechCorp) still stale — needs attention tomorrow.
```

---

## How This Helps Your Sales Organization

### For Individual Sales Reps
- Never lose context on a deal again
- Walk into every meeting fully prepared — automatically
- Know exactly what's weak in every deal and what to do about it
- Spend time selling, not note-taking

### For AE + SC in One Person (Which Most Enterprise Sales Looks Like)
- Switch between commercial and technical context instantly
- JARVIS remembers both what the CFO said and what the CTO needs
- One system. One place. Everything.

### For Sales Managers (Future)
- Pipeline visibility without chasing reps for updates
- MEDDPICC scores across all deals in one view
- Pattern recognition: what separates won deals from lost deals

### For the Whole Sales Org
- Institutional knowledge doesn't walk out the door when a rep leaves
- Competitive intelligence builds automatically from every deal
- Winning patterns get learned and applied across all accounts

---

## What JARVIS Does NOT Do

To be clear about the boundaries:

- ❌ Does not send emails on your behalf
- ❌ Does not update your CRM directly
- ❌ Does not access the internet for research (uses NVIDIA's trained knowledge)
- ❌ Does not connect to your company's internal systems
- ❌ Does not store your data anywhere except your own machine

Everything stays **local**. Your deal data never leaves your laptop.

---

## Getting Started

### What You Need
- A Mac or Linux machine (Windows via WSL works too)
- Python 3.11+ and Node.js 18+ (auto-installed if missing)
- Claude Desktop — [download here](https://claude.ai/download)
- A free NVIDIA API key — [get it here](https://build.nvidia.com/)

### Step 1 — Clone and Setup

```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
./setup.sh
```

`setup.sh` handles everything automatically:
- Installs missing dependencies (Python, Node, ffmpeg)
- Creates your `~/JARVIS` data folder
- Generates all config files for your machine
- Registers JARVIS with Claude Desktop
- Creates the `ACCOUNTS/` folder visible in the project

### Step 2 — Add Your NVIDIA Key

Open `.env` in the project folder. One line to change:

```
NVIDIA_API_KEY=nvapi-your-key-here
```

That is the **only** thing you configure manually. Everything else was done by setup.sh.

### Step 3 — Connect Google Workspace (Optional but Powerful)

In Claude Desktop → Settings → MCP Servers, add:
- Google Gmail MCP
- Google Calendar MCP
- Google Drive MCP

Sign in with Google once. Done. JARVIS will now automatically pull from your inbox, calendar, and drive.

### Step 4 — Start JARVIS

```bash
./start_jarvis.sh
```

JARVIS is now running in the background.

### Step 5 — Create Your First Account

In Finder, open the `ACCOUNTS/` folder in the project. Create a new folder with your account name:

```
ACCOUNTS/Acme Corp/
```

Wait 5 seconds. JARVIS auto-initializes the folder, creates all subfolders, and starts building intelligence. Open `account.html` in a browser to see the live dashboard.

### Step 6 — Talk to Claude Desktop

Open Claude Desktop. Try:

```
"list my accounts"
"brief me on Acme Corp"
"what's my pipeline looking like?"
"prep me for my Acme meeting at 3pm"
```

Claude calls JARVIS automatically. You get answers.

---

## For Developers — How It's Built

```
Personal-AE-SC-Jarvis/
  jarvis/                    Python core — runs as background daemon
    brain/                   Intelligence engine
      knowledge_builder.py   Fills missing intel using NVIDIA
      self_learner.py        Learns from your feedback, rewrites prompts
      conversation_extractor.py  Watches Claude workspace for intel
    queue/
      task_queue.py          SQLite-backed async task queue (survives crashes)
      worker_pool.py         N parallel workers consuming tasks
    observers/
      account_initializer.py Detects new ACCOUNTS/ folders, auto-initializes
      file_system.py         Watches for dropped files (recordings, docs, emails)
    skills/
      html_generator_skill.py  Generates account.html dashboards
    playbook/
      automation_engine.py   Stale deal detection, nudge generation
    llm/
      llm_client.py          Routes each task to the right NVIDIA model

  mcp-jarvis-server/         TypeScript MCP server — Claude Desktop talks to this
    src/tools.ts             15 MCP tools including Google Workspace bridge

  scripts/
    generate_config.py       Generates all machine-specific configs at setup time
    register_mcp.py          Registers JARVIS with Claude Desktop / OpenCode

  setup.sh                   One command: installs, configures, registers everything
  start_jarvis.sh            Starts the JARVIS daemon
  .claude/CLAUDE.md          Tells Claude how to behave automatically with JARVIS
```

**Key architectural decisions:**
- **Zero hardcoded paths** — everything resolves from `JARVIS_HOME` env var. Fork it, clone it, it works.
- **SQLite task queue** — tasks survive crashes. Nothing gets lost.
- **Event-driven** — components talk via pub/sub events, not direct imports. Fully decoupled.
- **Per-task model routing** — each task type uses the optimal NVIDIA model concurrently.
- **Generated configs** — machine-specific files created at setup time, never committed.

---

## Contributing

This started as a personal tool built for one salesperson doing both AE and SC work. If you're in sales and want to contribute:

- **More NVIDIA models** — as NVIDIA releases new models, they slot in via `llm_models` config
- **CRM connectors** — Salesforce, HubSpot MCP bridges
- **More playbook automation** — deal scoring, stage triggers, competitive alerts
- **Multi-user support** — team-level intelligence sharing

Open an issue or PR. The architecture is designed to be extended.

---

## License

MIT — use it, fork it, build on it.

---

*Built for the salesperson who is tired of being underprepared. Powered by NVIDIA. Runs on your machine. Your data stays yours.*
