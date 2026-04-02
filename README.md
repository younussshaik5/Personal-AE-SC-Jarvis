# JARVIS — AI Sales Intelligence Platform

> **Stop writing deliverables. Start closing deals.**

---

## What Is JARVIS?

JARVIS is a free AI plugin that sits inside Claude Desktop and acts as your personal sales analyst. You talk to Claude the same way you always do — and JARVIS gives Claude 24 specialist sales tools it wouldn't otherwise have.

You tell Claude about a deal. JARVIS turns that into a battlecard, a MEDDPICC score, a risk report, a proposal, a demo strategy, a follow-up email — or all of them at once, in parallel, in seconds. Everything it writes is grounded in your actual notes and deal data. It never guesses.

**In one sentence:** JARVIS is the difference between Claude giving you generic sales advice and Claude knowing your specific deal inside out and generating production-ready deliverables from it.

---

## Why Should You Use It?

You're probably already spending time on things like:

- Writing proposals from scratch (2-3 hours each)
- Updating your CRM after every call (30-45 mins)
- Prepping for meetings by piecing together notes from 5 places (1 hour)
- Building competitive battlecards before demos (1-2 hours)
- Manually scoring MEDDPICC and explaining gaps to your manager

That's 5-8 hours a week on work that isn't selling.

JARVIS cuts that to minutes. You paste your notes, you ask, you get the output. Everything is tied to your actual deal — not a generic template. The proposal references the real ARR. The battlecard addresses the actual competitor. The risk report flags the specific gaps in *your* discovery notes.

**The result:** more time on calls, better prepared for every meeting, nothing falling through the cracks.

---

## How Does It Work?

JARVIS runs as a plugin (called an MCP server) inside Claude Desktop. When you open Claude, JARVIS is already running in the background. You don't launch it separately.

You maintain a simple folder on your computer for each deal — your notes go in, JARVIS outputs come out. The more you put in, the sharper it gets.

```
How a typical interaction goes:

1. You finish a discovery call
2. You open Claude and paste your notes:
   "Update Acme Corp — Sarah confirmed $180k budget, Q3 deadline,
   competing with Freshdesk, champion is Mike in IT"

3. JARVIS updates the deal files automatically

4. You ask: "Score MEDDPICC for Acme Corp"
   → JARVIS reads your notes
   → Scores all 9 dimensions simultaneously (parallel)
   → Economic Buyer: AMBER — budget confirmed but CFO not engaged
   → Champion: GREEN — Mike Torres, strong advocate
   → Competition: GREEN — Freshdesk confirmed
   → Gives you the full scorecard in ~15 seconds

5. You ask: "What should I focus on before the next call?"
   → Top gaps, recommended questions, specific next action with date
```

**What it doesn't do (yet):**
- It doesn't auto-read your Gmail or calendar — you paste context in, Claude processes it
- It doesn't run while Claude is closed
- It doesn't connect to your CRM automatically — though that's on the roadmap (see the "What We Can Build Next" section)

---

## What Does It Actually Do?

You bring the context. JARVIS does the writing and analysis.

| You say | JARVIS generates |
|---|---|
| Paste discovery notes | MEDDPICC score, risk report, battlecard, value architecture — all in parallel |
| "Prep me for my Acme Corp meeting" | Who's in the room, what to ask, objections to expect, hard ask |
| "Write a proposal for RetailCo" | Full proposal from your actual discovery data — not a blank template |
| "What's the risk on TechCo?" | RED/AMBER/GREEN risk report with specific mitigations per risk |
| "Battlecard vs Salesforce for Acme" | Competitive positioning tied to what *that customer* actually said |
| "Demo strategy for RetailCo" | Custom demo flow ordered by their confirmed pain points |
| "Follow-up email for Acme Corp" | Two options: direct (short, action-focused) and consultative |
| "Score MEDDPICC for TechCo" | All 9 dimensions scored simultaneously with evidence and gaps |

Everything saved to your deal folder. Nothing invented.

---

## Before You Start — What You Need

You need three things. That's it.

**1. Mac, Windows, or Linux**
- Mac: works natively
- Windows: use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows Subsystem for Linux) or Git Bash
- Linux: works natively

**2. Claude Desktop** (free)
- Download from [claude.ai/download](https://claude.ai/download)
- This is the desktop app for Claude — different from the website

**3. An NVIDIA API Key** (free tier available)
- Go to [build.nvidia.com](https://build.nvidia.com/)
- Click "Sign In" → create a free account
- Click your profile → "API Keys" → "Generate Key"
- Copy the key — it starts with `nvapi-`

> **Why NVIDIA?** JARVIS uses **Kimi K2 Thinking** — a reasoning AI model hosted on NVIDIA's platform. It thinks through your deal before writing, which is why outputs are strategic rather than generic. The free tier gives you enough calls to run JARVIS daily.

> **Why multiple NVIDIA keys?** JARVIS generates multiple sections of a document simultaneously (e.g. MEDDPICC scores all 9 dimensions at once in parallel). With one key you can sometimes hit NVIDIA's rate limits mid-generation. With 2-5 keys, requests automatically rotate across them — no waiting, no failed generations. You can get multiple free keys from the same NVIDIA account.

---

## Installation — Step by Step

### Step 1: Install Claude Desktop

Download from [claude.ai/download](https://claude.ai/download) and open it. Sign in with your Anthropic account (or create one free).

### Step 2: Clone JARVIS

Open Terminal (search "Terminal" in Spotlight — ⌘Space).

```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

> **Don't have git?** Run `xcode-select --install` in Terminal first. Or download the ZIP from GitHub and unzip it.

### Step 3: Run Setup

This single command does everything — installs Python dependencies, registers JARVIS with Claude Desktop, creates your accounts folder, and walks you through API key setup.

```bash
bash setup.sh
```

**What you'll see:**

```
╔═══════════════════════════════════════════════════╗
║  JARVIS MCP — Complete Setup (Zero Dependencies)  ║
╚═══════════════════════════════════════════════════╝

1️⃣  Checking Homebrew... ✅
2️⃣  Checking Python 3.10+... ✅
3️⃣  Installing Python dependencies... ✅
...
5️⃣  Setting up NVIDIA API keys...

   JARVIS uses Kimi K2 Thinking via NVIDIA NIM for all 24 skills.
   Get free keys at: https://build.nvidia.com/

   ┌─────────────────────────────────────────────────────────────┐
   │  WHY MULTIPLE KEYS?                                         │
   │  JARVIS fires parallel LLM calls per skill. With 1 key you  │
   │  can hit rate limits. With 5 keys, requests round-robin     │
   │  automatically — no waiting, no retries.                    │
   └─────────────────────────────────────────────────────────────┘

   🔑 NVIDIA API Key 1 (required): nvapi-xxxx...
      ✅ Key 1 accepted

   🔑 NVIDIA API Key 2 (optional — press Enter to skip): nvapi-yyyy...
      ✅ Key 2 accepted

   🔑 NVIDIA API Key 3 (optional — press Enter to skip): [Enter]

   2 key(s) collected — writing to .env...
   ✅ .env written
```

### Step 4: Restart Claude Desktop

Close Claude Desktop completely (⌘Q on Mac — don't just close the window). Then reopen it.

### Step 5: Verify JARVIS Is Running

In Claude Desktop, look for the **🔨 (hammer) icon** in the chat input bar. Click it — you should see JARVIS tools listed. If you see `scaffold_account`, `get_proposal`, `track_meddpicc` etc., you're ready.

You should also see a CRM dashboard open automatically at **http://localhost:8000** in your browser.

---

## Your First 5 Minutes With JARVIS

### Create Your First Account

Tell Claude about a deal you're working on:

```
"Create an account for Acme Corp. They're a 500-person logistics company
evaluating us to replace their Salesforce Service Cloud. Primary contact is
Sarah Chen, VP Operations. ARR target is $180k."
```

JARVIS will call `scaffold_account` automatically, creating a folder with all the templates pre-filled.

### Add Your Discovery Notes

After a discovery call, paste your notes:

```
"Update Acme Corp with these call notes:
- Sarah confirmed budget is approved: $150-200k range
- Timeline is Q3 — contract with Salesforce ends June 30
- Pain: agents spend 40% of time switching between 5 systems
- They evaluated Zendesk last year, eliminated for pricing
- Need SSO with Okta and Salesforce integration
- Champion is Mike Torres, IT Director — very engaged"
```

JARVIS extracts every MEDDPICC signal, updates the deal stage, and queues relevant skills.

### Generate Intelligence

Now ask for what you need:

```
"Give me a battlecard for Acme Corp vs Salesforce"
"What are the top risks on Acme Corp?"
"Score MEDDPICC for Acme Corp"
"Prep me for my meeting with Sarah tomorrow"
```

Each generates in parallel — sections are built simultaneously, not one after another.

---

## Real User Journeys

### Journey 1: AE Working a New Logo

**Monday morning:**
```
You: "What's my pipeline look like?"
JARVIS: [pulls quick_insights for all active deals]
        → Acme Corp: AMBER — no economic buyer confirmed
        → TechCo: RED — timeline risk, 3 weeks to close
        → StartupX: GREEN — strong champion, paper process started
```

**Tuesday — discovery call with new prospect:**
```
You: [after the call] "Create account for RetailCo. Here are my notes:
     [paste notes]"

JARVIS:
→ Creates RetailCo account
→ Extracts: company size, pain, competitors, timeline, stakeholders
→ Scores MEDDPICC: M=AMBER, E=RED, D=GREEN...
→ Queues: battlecard, risk report, value architecture
→ "Economic Buyer is RED — you have a contact but no confirmed budget authority"
```

**Wednesday — prep for RetailCo demo:**
```
You: "Demo strategy for RetailCo"

JARVIS generates in parallel:
→ Demo objective: get POC approval
→ Audience breakdown: CTO cares about integrations, CFO cares about ROI
→ Demo flow: ordered by their confirmed pain points
→ Wow moment: show the 5-system integration they mentioned
→ What NOT to show: enterprise features they can't afford yet
→ Objection handlers for the 3 objections they raised
→ Hard ask: POC start date
```

**Thursday — competitive objection raised:**
```
You: "RetailCo just told me they're re-evaluating Freshdesk. Battlecard?"

JARVIS:
→ Competitor profile: Freshdesk's strengths in their segment
→ Their weaknesses tied to what RetailCo actually said they want
→ Our differentiated position for this specific deal
→ Killer questions to expose Freshdesk's gap
→ Positioning statement (2 sentences)
```

**Friday — proposal requested:**
```
You: "Generate a proposal for RetailCo"

JARVIS fires 4 parallel sections simultaneously:
→ Executive Summary & Requirements  ← from discovery notes
→ Proposed Solution                 ← maps each requirement to a feature
→ Pricing & Timeline                ← uses actual ARR + their deadline
→ Competitive Positioning & Next Steps ← vs Freshdesk
```

---

### Journey 2: SC Working a Technical Deal

**Incoming RFP situation:**
```
You: "Technical risk assessment for Acme Corp"

JARVIS identifies in parallel:
→ Integration risks: SSO with Okta, Salesforce API complexity
→ Security/compliance risks: data residency requirements mentioned
→ Unknown gaps: no mention of data migration scope

For each: Severity (RED/AMBER/GREEN), Evidence, Pre-sales action, Resolution path
```

**Architecture review request:**
```
You: "Generate solution architecture for Acme Corp"

JARVIS generates in parallel:
→ Architecture narrative: components + data flows based on their requirements
→ Mermaid.js diagram: Customer systems → Our platform → Integration points
   (paste into Mermaid.live for a visual diagram)
```

**Deal health check before QBR:**
```
You: "Full MEDDPICC for Acme Corp"

JARVIS fires all 9 sections simultaneously:
→ Metrics: AMBER — ROI mentioned but not quantified
→ Economic Buyer: RED — Sarah confirmed budget but CFO not engaged
→ Decision Criteria: GREEN — full eval list from RFP
→ Decision Process: AMBER — steps known, timeline unclear
→ Paper Process: AMBER — procurement contact unidentified
→ Implications/Pain: GREEN — 3 confirmed pain points with impact
→ Champion: GREEN — Mike Torres, strong advocate
→ Competition: GREEN — Freshdesk eliminated, Zendesk remaining
→ Overall: AMBER — 2 critical gaps before commit
```

---

### Journey 3: The Morning Routine

```
[You open Claude Desktop at 8am]
→ CRM dashboard opens at http://localhost:8000

You: "Brief me for today — here are my accounts: Acme Corp, RetailCo, TechCo"
→ JARVIS reads saved deal data for each account
→ RetailCo: MEDDPICC gaps flagged — no economic buyer confirmed
→ Acme Corp: timeline is tight, risk report shows RED on paper process
→ TechCo: last activity was 8 days ago — suggest follow-up

You: "Meeting prep for my Acme Corp call at 2pm"
→ JARVIS generates brief from saved notes — who's attending, what to ask,
   objection handlers, hard ask
→ Takes ~15 seconds
```

Note: JARVIS doesn't know about your calendar automatically. You tell it what's happening — it generates what you need.

---

## The 24 Skills

Every skill generates clean, grounded markdown — no hallucinated facts, no generic filler. If something isn't in your deal data, JARVIS says "TBD — needs discovery."

All skills with multiple sections generate those sections **in parallel** — so a 7-section proposal takes the same time as generating 1 section.

### Core Deal Intelligence

| Skill | What It Generates | Sections Generated in Parallel |
|---|---|---|
| `get_account_summary` | Full deal dossier from your saved notes | Company + Deal, Pain Points, MEDDPICC status, Risks & Actions |
| `quick_insights` | Fast deal snapshot — stage, risks, next action | Deal snapshot & signals, Risks & next action |
| `track_meddpicc` | Scores all 8 MEDDPICC dimensions from your discovery notes | **9 sections simultaneously** — each dimension independently |

### Competitive & Positioning

| Skill | What It Generates | Sections Generated in Parallel |
|---|---|---|
| `get_battlecard` | Win/loss positioning vs incumbent | Competitor profile, Our differentiators, Objection handlers |
| `get_competitive_intelligence` | Deep competitive analysis | Competitor profile, Weaknesses & positioning, Questions & risk |
| `analyze_competitor_pricing` | Pricing comparison + commercial strategy | Pricing comparison, Price positioning, Objection handlers |

### Deal Execution

| Skill | What It Generates | Sections Generated in Parallel |
|---|---|---|
| `get_proposal` | Full commercial proposal | Executive summary, Solution, Pricing & timeline, Competitive positioning |
| `generate_sow` | Statement of Work | Project overview & scope, Deliverables & timeline, Responsibilities & terms |
| `get_value_architecture` | ROI model + TCO + value case | Business problems & value, ROI model & TCO, Executive value statement |
| `generate_followup` | 2 follow-up email options | Option A (direct) + Option B (consultative) — both simultaneously |

### Risk & Discovery

| Skill | What It Generates | Sections Generated in Parallel |
|---|---|---|
| `get_risk_report` | RED/AMBER/GREEN risk report | Stakeholder risks, Technical risks, Commercial risks, Overall assessment |
| `assess_technical_risk` | Technical blocker analysis | Integration risks, Security & compliance risks |
| `get_discovery` | Discovery framework + gaps | Questions by MEDDPICC dimension, Pain mapping & gaps |
| `get_meeting_prep` | Pre-meeting brief | Context & what we know, Agenda & questions, Objections & hard ask |

### Meeting & Communication

| Skill | What It Generates | Sections Generated in Parallel |
|---|---|---|
| `process_meeting` | Meeting summary + deal impact | Meeting summary, Deal impact & MEDDPICC signals |
| `summarize_conversation` | Conversation analysis | Summary, Impact on deal & next steps |
| `extract_intelligence` | MEDDPICC signals from any text | MEDDPICC signals, Key intel & action items |
| `get_demo_strategy` | Demo flow + script | Objective & audience, Demo flow & wow moment, Objections & close |

### Technical & Documentation

| Skill | What It Generates | Sections Generated in Parallel |
|---|---|---|
| `generate_architecture` | Mermaid.js solution diagram | Architecture overview, Mermaid.js diagram |
| `build_knowledge_graph` | Stakeholder + deal knowledge map | Stakeholder map, Deal knowledge graph |
| `generate_sow` | Statement of Work | Project overview, Deliverables, Responsibilities |
| `generate_documentation` | Technical/sales documentation | Overview & requirements, Technical details |
| `generate_html_report` | HTML report for stakeholders | Executive dashboard, Risk & action report |
| `generate_custom_template` | Any custom document | Part 1 (overview), Part 2 (details) |

---

## How Parallel Generation Works (Non-Technical)

Think of it like a kitchen vs a single chef.

**Old way (one LLM call):** One chef cooks the whole meal course by course. Appetizer done → main course → dessert. Everything waits.

**JARVIS way (parallel sections):** You have a full brigade. The appetizer chef, main course chef, and dessert chef all start at the same time. Everything's ready together.

When you ask for MEDDPICC, JARVIS doesn't score Metrics → then Economic Buyer → then Decision Criteria one by one. It fires all 9 scoring requests simultaneously across your NVIDIA API keys. The result arrives in the time it takes to score *one* dimension, not nine.

This is why multiple NVIDIA keys matter. If you have 5 keys and fire 9 parallel requests, each key handles 1-2 requests at once, and none of them hit rate limits.

---

## MEDDPICC Framework

JARVIS uses MEDDPICC as the backbone for deal qualification. Every skill output references MEDDPICC status.

| Dimension | What JARVIS Looks For | Why It Matters |
|---|---|---|
| **M**etrics | ROI numbers, cost savings, productivity gains | No metrics = no business case |
| **E**conomic Buyer | CFO/VP/person with budget authority confirmed | Wrong sponsor = deal dies in procurement |
| **D**ecision Criteria | Evaluation requirements documented | Don't know criteria = can't win evaluation |
| **D**ecision Process | Procurement steps, approval chain mapped | Surprises in process = timeline slips |
| **P**aper Process | Legal, security review, MSA status | Paper process = months of surprise delays |
| **I**mplications | Pain points with business impact | No pain = no urgency |
| **C**hampion | Internal advocate selling on your behalf | No champion = no inside track |
| **C**ompetition | Competitors named, status known | Blind to competition = ambushed at close |

**Score:**
- **GREEN** — confirmed, documented, evidence in notes
- **AMBER** — partial, unverified, or assumed
- **RED** — missing or known gap

Overall deal health: below 40% GREEN = under-qualified. Above 70% = well qualified.

---

## Your Account Folders — How It All Works

This is the most important thing to understand about JARVIS. Everything lives in a folder on your Mac. JARVIS reads from that folder and writes back to it. The better your notes in the folder, the better everything JARVIS generates.

### Where Is The Folder?

After setup, your accounts folder lives at:

```
~/JARVIS/ACCOUNTS/
```

To open it:
- **Mac:** Finder → press **⌘⇧G** → paste `~/JARVIS/ACCOUNTS` → Enter. Bookmark it.
- **Windows:** Open File Explorer → paste `%USERPROFILE%\JARVIS\ACCOUNTS` in the address bar
- **Linux:** File manager → navigate to `~/JARVIS/ACCOUNTS`

Or from terminal (all platforms):
```bash
# Mac/Linux
open ~/JARVIS/ACCOUNTS    # Mac opens Finder
xdg-open ~/JARVIS/ACCOUNTS  # Linux opens file manager

# Or just navigate there in terminal
cd ~/JARVIS/ACCOUNTS && ls
```

### What's Inside Each Account Folder

When you create an account (say "Acme Corp"), JARVIS creates this:

```
~/JARVIS/ACCOUNTS/
└── AcmeCorp/
    │
    │  ── FILES YOU WRITE ──────────────────────────────────────
    ├── discovery.md         ← YOUR MOST IMPORTANT FILE
    │                           Paste call notes here. Everything JARVIS
    │                           generates gets better as this fills up.
    │
    ├── company_research.md  ← Background on the company
    │                           Paste LinkedIn info, news articles, anything
    │                           you know about them before engaging
    │
    ├── deal_stage.json      ← Deal metadata (auto-managed by JARVIS)
    │                           Stage, ARR, probability, stakeholder list,
    │                           activity log — JARVIS updates this when you
    │                           tell it about changes
    │
    ├── CLAUDE.md            ← Account-specific notes for JARVIS
    │                           Anything you want JARVIS to always remember
    │                           about this account. Free text, no format.
    │                           "Primary contact is Sarah. Don't mention pricing
    │                           until technical validation is done."
    │
    │  ── FILES JARVIS WRITES (don't edit these manually) ──────
    ├── account_summary.md
    ├── battlecard.md
    ├── meddpicc.md
    ├── risk_report.md
    ├── value_architecture.md
    ├── demo_strategy.md
    ├── meeting_prep.md
    ├── proposal.md
    ├── sow.md
    ├── competitive_intelligence.md
    └── ... (one file per skill)
```

### The Golden Rule

**JARVIS only generates from what's actually in your files. It never invents facts.**

- No ARR in `deal_stage.json`? The proposal will say "TBD — confirm pricing"
- No competitor in `discovery.md`? The battlecard will say "TBD — identify competitor"
- Nothing in `discovery.md`? Every skill output will be surface-level generic

The workflow is: **you add notes → JARVIS generates intelligence → you add more notes → JARVIS gets sharper**. After 2-3 discovery calls worth of notes, the outputs become genuinely useful.

### How To Add Notes (The Actual Flow)

**Easiest way — just tell Claude:**
```
"Update Acme Corp discovery notes:
- CFO Sarah Chen confirmed $180k budget approved
- Timeline is hard: Salesforce contract ends June 30
- Pain: agents switching between 5 systems, 40% wasted time
- IT Director Mike Torres is our champion — very engaged
- Competing with Freshdesk, eliminated Zendesk on pricing"
```
JARVIS updates the files automatically.

**Or open the file directly:**
1. Open Finder → go to `~/JARVIS/ACCOUNTS/AcmeCorp/`
2. Open `discovery.md` in any text editor (TextEdit works fine)
3. Paste your notes in plain English — no special format needed
4. Save the file
5. Next time you ask JARVIS for anything on Acme Corp, it reads the updated file

**Or paste a transcript after a call:**
```
"Process this meeting for Acme Corp: [paste transcript]"
```
JARVIS pulls out the MEDDPICC signals, updates the deal stage, and saves a summary.

### Enterprise Accounts — One Company, Multiple Deals

If you're selling into a large company with multiple business units (e.g. Tata Group with separate deals at TataTele and TataSky), you can use a parent/child structure:

```
ACCOUNTS/
└── Tata/                         ← parent folder
    ├── company_research.md       ← ONE file, shared by all Tata deals
    │                                (the group's background, news, org structure)
    │
    ├── TataTeleservices/         ← child deal — its own pipeline
    │   ├── deal_stage.json       ← TataTele's ARR, stage, contacts
    │   ├── discovery.md          ← TataTele-specific call notes
    │   └── battlecard.md         ← generated from TataTele context
    │
    └── TataSky/                  ← completely separate child deal
        ├── deal_stage.json
        ├── discovery.md
        └── ...
```

**Why this matters:** You write the company research once (Tata's background, their tech stack, their strategic priorities) and every child deal automatically inherits it. When you run `get_battlecard` for TataTele, JARVIS reads both the Tata company research AND the TataTele-specific discovery notes.

To create this: `scaffold_account` with account name `TataTeleservices` and parent name `Tata`. JARVIS handles the folder structure.

### What Not To Do

- **Don't rename the JARVIS-generated files** (battlecard.md, meddpicc.md etc.) — JARVIS looks for them by exact name
- **Don't edit `deal_stage.json` manually** — it's JSON, easy to break. Tell Claude to update it instead
- **Don't put account folders inside other folders** unless you're intentionally using parent/child — JARVIS expects `ACCOUNTS/CompanyName/` flat structure for standalone deals
- **Don't worry about formatting** in `discovery.md` or `company_research.md` — plain sentences work fine. JARVIS reads natural language.

---

## CRM Dashboard

Auto-starts at **http://localhost:8000** every time you open Claude Desktop.

**What you see:**

```
Pipeline Overview
├── Open Pipeline: $2.4M
├── Weighted Pipeline: $980k
├── Closed Won (QTD): $430k
├── Win Rate: 34%
├── Avg Deal Size: $87k
└── MEDDPICC Health: 58% (AMBER)

Deal Stage Funnel
Discovery (3) → Qualify (2) → Demo (4) → Negotiate (1) → Close (2)

Pipeline Table
Account      │ Stage    │ ARR     │ MEDDPICC │ Risk │ Skills
AcmeCorp     │ Demo     │ $180k   │ 62% 🟡   │ 🟡   │ 14/24
RetailCo     │ Qualify  │ $95k    │ 38% 🔴   │ 🔴   │ 6/24
TechCo       │ Negotiate│ $240k   │ 78% 🟢   │ 🟢   │ 22/24
```

**Per-account drill-down:**
- Click any account → full scrollable intelligence report
- MEDDPICC scorecard with all 8 dimensions visualized
- Risk breakdown (HIGH/MEDIUM/LOW with evidence)
- All 24 skill outputs with generation status
- "⚡ Generate All" button — queues all missing skills in background
- "📄 Export PDF" — one-click full deal story for manager or QBR

---

## What We Can Build Next — Full Sales Cycle via MCP

Right now JARVIS is a conversation tool — you paste context in, it generates intelligence. The next evolution is connecting it to the systems you already use, so data flows in and out automatically. MCP (the same protocol JARVIS runs on) makes this possible for almost every tool in the modern sales stack.

Here's the full picture: **lead born to deal closed**, every stage, every system.

---

### Stage 1 — Lead Born & Prospect Research

**The problem today:** You get a new lead. You spend 30 minutes on LinkedIn, their website, Crunchbase, and Google News piecing together context before your first call.

**What MCP enables:**
```
You: "Research RetailCo before my call tomorrow"

Claude:
→ [LinkedIn MCP]     — scrapes company page, decision-maker profiles, recent posts
→ [Google Search MCP] — recent news, funding rounds, tech stack signals
→ [Crunchbase MCP]   — headcount, funding history, investors
→ [JARVIS]           — scaffold_account + populate company_research.md
→ Returns: full pre-call brief in 30 seconds
```

| Integration | What it adds | MCP exists? |
|---|---|---|
| LinkedIn | Stakeholder profiles, org chart, job postings (hiring = budget signal) | Yes (unofficial) |
| Google Search | Recent news, press releases, competitor mentions | Yes |
| Crunchbase / PitchBook | Funding, investors, growth signals | Possible |
| Company website | Product pages, pricing, tech stack (via job listings) | Yes (web fetch) |

---

### Stage 2 — CRM Sync (Bi-directional)

**The problem today:** Your CRM has the deal data. JARVIS has the intelligence. They're separate. You copy-paste between them.

**What MCP enables:**
```
You: "Sync Acme Corp"

Claude:
→ [CRM MCP]   — pulls Opportunity, Contacts, Activities, Emails
→ [JARVIS]    — populates deal_stage.json + discovery.md
             — runs MEDDPICC, risk report, battlecard in parallel
→ [CRM MCP]   — pushes back: MEDDPICC score, risk level, next actions as Tasks
```

**What gets written back to your CRM automatically:**
- MEDDPICC score and gap summary → custom fields
- RED/AMBER/GREEN risk → opportunity risk field
- Stage change → opportunity stage
- Top 3 next actions → CRM Tasks with due dates
- Champion/economic buyer confirmed → contact roles updated
- Key insight → note/chatter on the opportunity

| CRM | MCP Status |
|---|---|
| Salesforce | Official MCP server in beta ([forcedotcom/mcp-hosted](https://github.com/forcedotcom/mcp-hosted)) |
| HubSpot | Community MCP available |
| Pipedrive | API-based, wrappable as MCP |
| Notion (deal tracking) | Official MCP available |

---

### Stage 3 — Discovery & Meetings

**The problem today:** You take notes during calls, clean them up after, manually update your CRM. Takes 45 minutes per meeting.

**What MCP enables:**
```
After a call:
You: "Process my Acme Corp call"

Claude:
→ [Google Meet / Zoom MCP] — pulls transcript from the recording
→ [JARVIS process_meeting]  — extracts MEDDPICC signals, updates deal stage,
                              generates meeting summary
→ [Gmail MCP]              — drafts follow-up email from the summary
→ [CRM MCP]                — logs activity, updates opportunity, creates next tasks
→ [Google Calendar MCP]    — schedules next meeting if date was mentioned
```

| Integration | What it adds | MCP exists? |
|---|---|---|
| Google Meet / Zoom | Auto-pull transcripts after calls | Zoom MCP in progress |
| Fireflies.ai / Otter | Meeting transcripts + summaries | API wrappable |
| Google Calendar | Meeting context, prep triggering | Yes (Google Workspace MCP) |
| Gmail / Outlook | Email threads → deal intel, draft follow-ups | Yes (Google Workspace MCP) |

---

### Stage 4 — Demo & Technical Validation

**The problem today:** SC builds a custom demo flow from scratch for each account. No memory of what worked last time.

**What MCP enables:**
```
You: "Prep demo for RetailCo — they care about Salesforce integration and SSO"

Claude:
→ [JARVIS get_demo_strategy]     — custom demo flow from their discovery notes
→ [JARVIS generate_architecture] — Mermaid.js diagram of their specific setup
→ [Confluence / Notion MCP]      — pulls your internal solution docs for reference
→ [Jira MCP]                     — checks if similar integrations were delivered before
```

| Integration | What it adds | MCP exists? |
|---|---|---|
| Confluence / Notion | Internal knowledge base, past solutions | Yes |
| Jira / Linear | Past implementation references, known issues | Yes |
| GitHub | Technical docs, integration guides | Yes |

---

### Stage 5 — Proposal & Commercial

**The problem today:** Proposal takes 2-3 hours. Half of it is formatting, half is pulling numbers from different places.

**What MCP enables:**
```
You: "Generate proposal for RetailCo"

Claude:
→ [CRM MCP]             — pulls actual ARR, product, contract terms
→ [Google Drive MCP]    — pulls approved pricing deck / legal templates
→ [JARVIS get_proposal] — generates grounded proposal using all of the above
→ [Google Drive MCP]    — saves final proposal to their shared folder
→ [Gmail MCP]           — drafts the email to send it
```

| Integration | What it adds | MCP exists? |
|---|---|---|
| Google Drive / SharePoint | Proposal templates, pricing docs, legal terms | Yes |
| DocuSign / Adobe Sign | Contract send + signature tracking | API wrappable |
| CPQ tools (Salesforce CPQ, DealHub) | Real-time pricing, discount approval | Possible |

---

### Stage 6 — Negotiation & Close

**The problem today:** Legal redlines take weeks. Procurement surprises kill timelines. No visibility until it's too late.

**What MCP enables:**
```
You: "What's blocking TechCo from closing?"

Claude:
→ [JARVIS get_risk_report]      — RED items from deal data
→ [CRM MCP]                     — paper process status, last activity
→ [DocuSign MCP]                — contract status, who hasn't signed
→ [Email MCP]                   — last email thread, days since response
→ Returns: clear blocker list with owners and actions
```

| Integration | What it adds | MCP exists? |
|---|---|---|
| DocuSign / Ironclad | Contract status, redline tracking | API wrappable |
| Slack | Internal deal room discussions, stakeholder signals | Yes (official Slack MCP) |
| Email thread analysis | Sentiment shift, ghosting detection | Yes (Gmail MCP) |

---

### Stage 7 — Closed Won → Handoff

**The problem today:** AE closes the deal. CS/implementation team starts from scratch. No context transfer.

**What MCP enables:**
```
Deal marked Closed Won in CRM:

Claude:
→ [JARVIS get_account_summary]  — full deal story: stakeholders, pain, requirements
→ [JARVIS generate_sow]         — SOW from actual discovery data
→ [Jira MCP]                    — creates implementation project with tasks
→ [Slack MCP]                   — posts deal summary to #new-customers channel
→ [CRM MCP]                     — updates account record with implementation notes
```

| Integration | What it adds | MCP exists? |
|---|---|---|
| Jira / Linear | Auto-create implementation tickets from SOW | Yes |
| Slack | Deal announcement, CS handoff notification | Yes |
| Gainsight / ChurnZero | CSM handoff with full context | API wrappable |
| Zendesk / Freshdesk | Support account setup with deal context | API wrappable |

---

### The Full Picture

```
Lead Born
    │  LinkedIn + Search MCPs → company_research.md
    ↓
CRM Sync
    │  Salesforce/HubSpot MCP → deal_stage.json (bi-directional)
    ↓
Discovery Calls
    │  Zoom/Meet MCP → transcripts → process_meeting → CRM updated
    ↓
Demo & Technical
    │  Confluence/Jira MCPs → solution reference + architecture diagrams
    ↓
Proposal
    │  Drive MCP → templates → get_proposal → Drive MCP (saved)
    ↓
Negotiation
    │  DocuSign + Slack MCPs → blocker tracking + deal room
    ↓
Closed Won
    │  Jira + Slack + CRM MCPs → full handoff, zero context lost
```

**How MCP makes this possible:** Claude Desktop acts as the orchestrator. Every tool above has (or can have) an MCP server. You add them all to Claude Desktop's config alongside JARVIS. Then in a single conversation, Claude can reach into any of them — read, generate with JARVIS, write back. No custom integrations. No API keys per tool in your code. Just MCP servers registered in one config file.

JARVIS is the intelligence layer. The MCP ecosystem is the connectivity layer. Together they cover the entire revenue cycle.

---

## NVIDIA Keys — How To Get More

You can get multiple free keys from NVIDIA's platform:

1. Go to [build.nvidia.com](https://build.nvidia.com/)
2. Sign in → click your profile picture → "API Keys"
3. Click "Generate Key" — you can generate multiple keys
4. Add each one to your `.env` file:

```bash
# In your .env file:
NVIDIA_API_KEY=nvapi-key1...
NVIDIA_API_KEY_2=nvapi-key2...
NVIDIA_API_KEY_3=nvapi-key3...
NVIDIA_API_KEY_4=nvapi-key4...
NVIDIA_API_KEY_5=nvapi-key5...
```

After editing `.env`, restart Claude Desktop (⌘Q → reopen) for the keys to load.

**How many do you need?**
- 1 key: works fine for moderate use
- 2-3 keys: recommended for daily use with multiple accounts
- 5 keys: ideal if you're running JARVIS heavily or sharing with a team

---

## Troubleshooting

### JARVIS not showing in Claude Desktop tools (no 🔨 icon)

```bash
# Re-run setup
bash setup.sh
# Then quit Claude Desktop (⌘Q) and reopen — don't just close the window
```

### "All NVIDIA keys exhausted" or API errors

1. Check your key is correct: open `.env` and verify `NVIDIA_API_KEY=nvapi-...`
2. Test the key at [build.nvidia.com](https://build.nvidia.com/) → try a model in the playground
3. If rate-limited: wait 60 seconds (JARVIS auto-recovers), or add more keys
4. Keys must be in `.env` file — not just set in terminal. Claude Desktop doesn't read shell env vars.

### Skills returning "TBD — needs discovery"

This is correct behavior, not an error. JARVIS only generates from your actual data. Fix: add more notes to `discovery.md` or `deal_stage.json` for that account. The more context you give, the more grounded and useful the output.

### CRM dashboard not loading at http://localhost:8000

```bash
# Check if the CRM sidecar is registered
cat "$HOME/Library/Application Support/Claude/claude_desktop_config.json" | grep jarvis-crm

# If missing, re-run setup
bash setup.sh
```

### Queue not processing (skills queued but not generating)

```bash
# Inspect the queue
cat ~/.jarvis/queue.json

# If stuck, clear it and regenerate manually
echo '{"queue":[]}' > ~/.jarvis/queue.json
# Then ask Claude to generate the skill you need
```

### Python or import errors after setup

```bash
# Reinstall dependencies
bash setup.sh
# setup.sh is safe to re-run — it won't overwrite your .env or account data
```

---

## Adding Your Own Skills

Each skill is one Python file. Here's the minimal template:

```python
# jarvis_mcp/skills/my_skill.py
from jarvis_mcp.skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        sections = [
            {
                "name": "Section One",
                "prompt": f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nWrite section one...",
                "max_tokens": 800,
            },
            {
                "name": "Section Two",
                "prompt": f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nWrite section two...",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "my_skill.md", response)
        return response
```

Then:
1. Register it in `jarvis_mcp/skills/__init__.py`: `"my_skill": MySkill`
2. Add the MCP tool in `jarvis_mcp_server.py` (copy any existing tool definition)
3. Restart Claude Desktop

That's it. Your skill is live with parallel generation built in.

---

## Technical Stack

For those who want to understand what's running:

| Component | What It Is |
|---|---|
| **Claude Desktop** | The UI — where you chat. Acts as the MCP client |
| **JARVIS MCP Server** | A Python process that runs alongside Claude, exposes 24 tools |
| **MCP Protocol** | How Claude and JARVIS communicate — think of it as a plugin API |
| **Kimi K2 Thinking** | The AI model doing the actual generation — hosted on NVIDIA NIM |
| **NVIDIA NIM** | NVIDIA's hosted inference API — OpenAI-compatible endpoint |
| **CRM Sidecar** | A separate Python process that serves the web dashboard |
| **asyncio.gather** | Python's parallel execution — fires multiple LLM calls simultaneously |

The model: **moonshotai/kimi-k2-thinking** via `https://integrate.api.nvidia.com/v1`. It's a thinking model — it reasons through the deal before writing, which is why outputs are strategic rather than surface-level.

---

## License

MIT — fork it, customize it, use it commercially, make it yours.

---

## Contributing

PRs welcome. If you add a skill that works well, open a PR — other AEs/SCs will benefit.

The codebase is intentionally simple: 24 skill files, one base class, one LLM manager. No frameworks, no abstractions beyond what's needed. You don't need to understand MCP or async Python to add a skill — just copy an existing one and change the prompts.

---

**Built by an AE/SC who was tired of doing both jobs manually. One tool. Zero admin. Everything grounded in real deal data.**
