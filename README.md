# JARVIS — AI Sales Intelligence for Claude Desktop

> **You're spending 5-8 hours a week on proposals, battlecards, meeting prep, and MEDDPICC scoring. That's time you're not selling.** JARVIS cuts it to minutes.

---

## The Problem

You close a discovery call. Now you need to:
- Update your deal notes (30 min)
- Score MEDDPICC for your manager (45 min)
- Write a follow-up email (20 min)
- Build a battlecard before the next call (1-2 hours)
- Draft a proposal by Friday (2-3 hours)

That's a full day of writing instead of selling. Every week.

## The Fix

Paste your call notes into Claude. Ask for what you need. Get it in seconds — grounded in your actual deal data, not generic templates.

```
You:  "Update Acme Corp — Sarah confirmed $180k budget, Q3 deadline,
       competing with Freshdesk, champion is Mike in IT.
       Score MEDDPICC and give me a battlecard."

JARVIS (15 seconds later):

  MEDDPICC:
    Economic Buyer: AMBER — budget confirmed but CFO not engaged
    Champion: GREEN — Mike Torres, strong internal advocate
    Competition: GREEN — Freshdesk confirmed, Zendesk eliminated
    Paper Process: RED — no procurement contact identified
    >> Top gap: get CFO in the room before demo

  Battlecard vs Freshdesk:
    Their weakness: no enterprise SSO, limited API
    Your edge: Okta SSO + Salesforce integration (confirmed requirements)
    Killer question: "How are you handling SSO across 500 users today?"
```

No copy-pasting between tools. No blank templates. Everything references what the customer actually said.

---

## Who This Is For

| **Use it if you...** | **Skip it if you...** |
|---|---|
| Handle AE and/or SC work | Have a dedicated sales ops team doing this for you |
| Manage 5-15 active deals | Need a point-and-click tool with no setup |
| Already use Claude Desktop | Want something that connects to your CRM automatically (yet) |
| Want better prep, faster | |

---

## Day 1 vs Day 30

| | What you get |
|---|---|
| **Day 1** | Generic templates with "TBD — needs discovery" placeholders. Good structure, not yet sharp. |
| **After first discovery call** | Paste your notes once. JARVIS auto-runs MEDDPICC, risk report, battlecard, value architecture, discovery gaps — all in parallel, all automatically. By the time you close your laptop, the account folder is fully populated. |
| **Day 7** | JARVIS has seen 2-3 calls worth of notes. Every output references real stakeholders, real pain, real competitors. Proposals auto-update when deal data changes. |
| **Day 30** | You stop thinking about deliverables. Drop a transcript → everything regenerates. Ask a question → JARVIS already knows the deal. Every output knows what every previous output found. |

The system evolves itself. You add context — it does the rest.

---

## Self-Evolving Intelligence

JARVIS learns from everything — chat, files you drop in, and its own outputs. You don't have to trigger anything.

### Any input feeds the knowledge base

```
Chat with Claude          → skill output → intel extracted → discovery.md updated
Drop a .txt / .md file    → file watcher detects → intel extracted → discovery.md updated
Drop a transcript         → same
Ask for a SOW             → SOW output → new requirements extracted → merged back
MEDDPICC runs             → output extracted → new signals merged → cascade re-fires
```

**The extraction engine** reads any text and pulls out only concrete, new facts:
- Stakeholders (name, title, role)
- Pain points and problems
- Requirements and success criteria
- Metrics, ROI, cost savings
- Competitors and their status
- Timelines and deadlines
- Budget signals
- Champion/sponsor signals
- Technical requirements and blockers

Everything gets appended to `discovery.md` with a timestamp and source — never overwritten, always traceable.

### The cascade (what happens after any update)

```
discovery.md or deal_stage.json updated (by anything above)
  |
  ├─ FIRST: intelligence_brief (Nemotron, priority 2)
  |    Reads ALL files → synthesizes intelligence_brief.md
  |    BriefCoordinator begins accumulating skill deltas into brief
  |
  └─ intelligence_brief completes → HIGH priority cascade fires:
       meddpicc, battlecard, competitive_intelligence, technical_risk,
       discovery, risk_report, value_architecture, account_summary,
       quick_insights
       (each reads intelligence_brief.md as primary context)
       (BriefCoordinator appends each skill's key findings as delta)
  |
  ├─ meddpicc → risk_report, value_architecture, account_summary,
  |             discovery, knowledge_builder, quick_insights
  ├─ battlecard → demo_strategy, competitor_pricing
  ├─ competitive_intelligence → battlecard
  ├─ technical_risk → meeting_prep, architecture_diagram
  ├─ risk_report → meeting_prep, demo_strategy
  ├─ value_architecture → proposal → sow, documentation
  ├─ discovery → meeting_prep → followup_email
  ├─ account_summary → knowledge_builder → html_generator
  ├─ demo_strategy → meeting_prep
  └─ company_research → battlecard, competitive_intelligence,
                        demo_strategy, account_summary

User action (process_meeting / summarize_conversation / extract_intelligence)
  → meeting_summary / conversation_summarizer / conversation_extractor
    → meddpicc, account_summary, risk_report, quick_insights
      → full downstream cascade above

Cycle guard: FEEDBACK_SKILLS write extracted intel to discovery.md.
The file watcher suppresses re-triggering intelligence_brief for 30 min
after each merger write — preventing the cascade from restarting itself
while still running. After the cascade exhausts, the system goes quiet
until new source data arrives.
```

**Result:** After any input, the full cascade runs in the background — typically 1-3 hours for all skills across one account (skills run sequentially to stay within NVIDIA rate limits). Each skill reads the intelligence brief plus all deltas accumulated so far — so later skills in the cascade always have richer context than earlier ones.

> **Confirmed end-to-end:** file watcher starts on Claude Desktop boot, skill calls route through the intelligence layer, outputs feed back into discovery.md, cycle guard (30-min cooldown) prevents re-triggering while the cascade is still running, cascade runs in correct priority order.

### What gets added to every account folder

| File | What it is |
|---|---|
| `_skill_timeline.json` | When each skill last ran, what triggered it, success/error |
| `_evolution_log.md` | Append-only log — every entry timestamped and sourced, read by all skills |

### Two-stage intelligence architecture

Every skill run goes through two stages:

**Stage 1 — Nemotron synthesis (intelligence_brief)**
Nemotron-120B reads ALL account files with zero truncation (discovery notes, MEDDPICC, battlecard, risk report, company research, evolution log) and synthesizes a comprehensive `intelligence_brief.md`. This is the single source of truth for the deal.

**Stage 2 — Skill execution**
All other skills (meddpicc, battlecard, proposal, etc.) read `intelligence_brief.md` as their primary context instead of raw files. Every skill starts with the full deal picture — not fragments.

**BriefCoordinator — live enrichment**
After each skill completes, a coordinator appends its key findings as a delta block to `intelligence_brief.md`. This means Wave 2 skills read a richer brief than Wave 1 — the brief gets smarter as the cascade runs. On the next intelligence_brief run, Nemotron absorbs all accumulated deltas into the new synthesis and the file resets clean.

Zero extra API calls — coordinator is pure file I/O.

### Model routing — right model for each task

| Type | Skills | Chain (failover order) |
|---|---|---|
| `synthesis` | Intelligence Brief only | **Nemotron-120B (1M ctx)** with extended reasoning — dedicated key |
| `reasoning` | MEDDPICC, risk, competitive, value arch, technical risk | kimi-k2-thinking → step-3.5-flash → qwq-32b |
| `writing` | Proposals, SOW, battlecards, demo strategy, docs | kimi-k2-instruct → qwq-32b → kimi-k2-thinking |
| `fast` | Quick insights, meeting prep, summaries, follow-ups, extraction | kimi-k2-instruct → qwen2-7b → kimi-k2-thinking |
| `default` | Everything else | kimi-k2-instruct → kimi-k2-thinking → qwq-32b |

**Nemotron-120B** (`nvidia/nemotron-3-super-120b-a12b`) is reserved exclusively for intelligence synthesis. Its 1M token context window absorbs every account file at once — no truncation, no sampling. All reasoning skills (kimi, step3.5, qwq) then read the synthesized brief rather than raw files, so they reason over a clean, complete picture.

If a key hits rate limits on model 1, it cascades to model 2 automatically. With 6 keys across 5 model options, failures are essentially impossible.

---

## Before You Start — What You Need

You need 3 things. All free.

### 1. Claude Desktop

This is the desktop app for Claude (different from the website). Download it at **claude.ai/download** and sign in.

### 2. An NVIDIA API Key

JARVIS uses an AI reasoning model called Kimi K2 — it thinks through your deal before writing, which is why outputs are strategic rather than generic. It runs on NVIDIA's platform (free tier).

1. Go to **build.nvidia.com**
2. Click "Sign In" → create a free account
3. Click your profile picture → "API Keys" → "Generate Key"
4. Copy the key — it starts with `nvapi-`

Keep that key handy. The setup script will ask for it.

### 3. The Setup Script

One script handles everything — installs all dependencies, asks for your key, connects JARVIS to Claude Desktop. You run it once.

---

## Installation

### Step 1 — Download JARVIS

Go to **github.com/younussshaik5/Personal-AE-SC-Jarvis**

Click the green **"Code"** button → **"Download ZIP"**

Unzip the file somewhere easy to find (like your Desktop or Documents folder).

### Step 2 — Open Terminal

Terminal is a text-based window where you run commands. Don't worry — you only need to run one command, and it's copy-paste.

**On Mac:**
- Press **Cmd + Space**, type `Terminal`, press Enter
- A black/white window opens — that's Terminal

**On Windows:**
- First, install WSL (Windows Subsystem for Linux) — it's a free Microsoft tool that lets you run these commands on Windows
- Open the Microsoft Store, search "Ubuntu", install it
- Open Ubuntu — that's your Terminal
- *(If you're comfortable with Git Bash, that works too)*

**On Linux:**
- You already know where Terminal is

### Step 3 — Run the Setup Script

In Terminal, type `cd ` (with a space after it), then drag the JARVIS folder into the Terminal window. The folder path fills in automatically. Press Enter.

Then copy-paste this and press Enter:

```
bash setup.sh
```

**What happens next:**

The script walks you through everything:

```
1. Checks if Python is installed (installs it automatically on Mac if not)
2. Installs required packages
3. Asks for your NVIDIA API key — paste the nvapi-... key you copied earlier
4. Creates your ACCOUNTS folder at ~/JARVIS/ACCOUNTS/
5. Connects JARVIS to Claude Desktop
6. Runs a quick test to confirm everything works
```

When it says "Setup Complete" — you're done.

### Step 4 — Restart Claude Desktop

**Important:** Close Claude Desktop completely, then reopen it.
- Mac: press **Cmd + Q** (not just the red X — that keeps it running)
- Windows: right-click the Claude icon in the taskbar → Quit
- Then reopen Claude Desktop normally

### Step 5 — Confirm JARVIS Is Running

In Claude Desktop, look at the chat input bar. You should see a **hammer icon (🔨)**. Click it — if you see tools like `get_account_summary`, `track_meddpicc`, `get_proposal` listed, JARVIS is live.

You should also see a dashboard open at **http://localhost:8000** in your browser — that's your pipeline view.

---

## Your First 5 Minutes

### Create your first account

Just tell Claude:

```
"Create an account for Acme Corp. They're a 500-person logistics company
evaluating us to replace Salesforce Service Cloud. Primary contact is
Sarah Chen, VP Operations. ARR target is $180k."
```

JARVIS creates a folder on your computer with all the templates for that deal.

### Add your discovery notes

After a call, paste your notes:

```
"Update Acme Corp:
- Sarah confirmed budget $150-200k, approved
- Timeline Q3 — Salesforce contract ends June 30
- Pain: agents spend 40% time switching between 5 systems
- Champion: Mike Torres, IT Director, very engaged
- Competing with Freshdesk"
```

### Ask for what you need

```
"Score MEDDPICC for Acme Corp"
"Battlecard vs Salesforce for Acme Corp"
"Prep me for my meeting with Sarah tomorrow"
"Write a proposal for Acme Corp"
```

Each one generates in seconds — multiple sections built at the same time, not one after another.

---

## Where Your Deal Data Lives

JARVIS keeps a folder for each account on your computer at:

```
Mac/Linux:   ~/JARVIS/ACCOUNTS/
Windows:     C:\Users\YourName\JARVIS\ACCOUNTS\
```

**To open it on Mac:** Open Finder → press **Cmd + Shift + G** → paste `~/JARVIS/ACCOUNTS` → Enter. Bookmark it.

**To open it on Windows:** Open File Explorer → click the address bar → paste `%USERPROFILE%\JARVIS\ACCOUNTS` → Enter.

### What's inside each account folder

```
AcmeCorp/
|
|  -- YOU WRITE THESE ----------------------------------
|-- discovery.md          Your call notes go here.
|                         This is the most important file.
|                         The more you add, the better everything gets.
|
|-- company_research.md   Background on the company —
|                         LinkedIn info, news, what you know
|                         before engaging.
|
|-- CLAUDE.md             Notes you want JARVIS to always remember
|                         for this account. Free text, no format.
|                         Example: "Don't mention pricing until
|                         technical validation is done."
|
|  -- JARVIS WRITES THESE (don't touch) ---------------
|-- battlecard.md
|-- meddpicc.md
|-- risk_report.md
|-- proposal.md
|-- ... (one file per skill)
```

### How to add notes

**Easiest — just tell Claude:**
```
"Update Acme Corp: CFO confirmed budget, timeline is hard Q3,
 Mike Torres is our champion."
```
JARVIS updates the files automatically.

**Or open the file directly:**
Open `discovery.md` in any text editor (Notepad, TextEdit, anything). Paste your notes. Save. Next time you ask JARVIS anything about Acme Corp, it reads the updated file.

**Or paste a transcript:**
```
"Process this meeting for Acme Corp: [paste transcript]"
```
JARVIS pulls out the MEDDPICC signals and saves a summary.

### Don't do this

- Don't rename the files JARVIS generates — it looks for them by exact name
- Don't edit `deal_stage.json` manually — tell Claude to update it instead
- Don't worry about formatting in your notes — plain sentences work fine

### Enterprise accounts (one company, multiple deals)

If you're selling into a large company with separate business units:

```
ACCOUNTS/
+-- Tata/                         One company
|   |-- company_research.md       Research written once, shared everywhere
|   |-- TataTeleservices/         Separate deal with its own pipeline
|   +-- TataSky/                  Another separate deal
```

Create it with: `"Create account TataTeleservices with parent Tata"`

---

## The 27 Skills

### Start here (try these first)

| What you ask | What you get |
|---|---|
| `"Account summary for Acme Corp"` | Full deal dossier — stage, stakeholders, risks, next actions |
| `"Score MEDDPICC for Acme Corp"` | All 8 dimensions scored with evidence and gaps |
| `"Battlecard vs [competitor] for Acme Corp"` | Win/loss positioning tied to what that customer actually said |
| `"Meeting prep for Acme Corp"` | Who's attending, what to ask, objection handlers, hard ask |
| `"Quick insights on Acme Corp"` | Fast snapshot — risk level, next recommended action |

### All 26 skills

<details>
<summary>Deal Intelligence</summary>

| Skill | What it generates |
|---|---|
| `get_account_summary` | Full deal dossier |
| `quick_insights` | Fast deal snapshot |
| `track_meddpicc` | MEDDPICC scorecard (all 8 dimensions) |
| `update_deal_stage` | Updates stage, ARR, probability |

</details>

<details>
<summary>Competitive & Positioning</summary>

| Skill | What it generates |
|---|---|
| `get_battlecard` | Competitor profile, your differentiators, objection handlers |
| `get_competitive_intelligence` | Deep competitive analysis |
| `analyze_competitor_pricing` | Pricing comparison + strategy |

</details>

<details>
<summary>Deal Execution</summary>

| Skill | What it generates |
|---|---|
| `get_proposal` | Full commercial proposal |
| `generate_sow` | Statement of Work |
| `get_value_architecture` | ROI model, TCO, value case |
| `generate_followup` | Two email options (direct + consultative) |

</details>

<details>
<summary>Risk & Discovery</summary>

| Skill | What it generates |
|---|---|
| `get_risk_report` | RED/AMBER/GREEN risk report with mitigations |
| `assess_technical_risk` | Technical blockers and pre-sales actions |
| `get_discovery` | Discovery questions + MEDDPICC gap analysis |
| `get_meeting_prep` | Pre-meeting brief |

</details>

<details>
<summary>Meetings & Communication</summary>

| Skill | What it generates |
|---|---|
| `process_meeting` | Meeting summary + deal impact |
| `extract_intelligence` | MEDDPICC signals from any text |
| `get_demo_strategy` | Demo flow + objection handlers |
| `summarize_conversation` | Conversation summary + next steps |

</details>

<details>
<summary>Technical & Documentation</summary>

| Skill | What it generates |
|---|---|
| `generate_architecture` | Solution architecture diagram |
| `build_knowledge_graph` | Stakeholder + deal map |
| `generate_documentation` | Technical/sales documentation |
| `generate_html_report` | HTML report for stakeholders |
| `generate_custom_template` | Any custom document |

</details>

<details>
<summary>Research</summary>

| Skill | What it generates |
|---|---|
| `company_research` | Structured company profile — overview, business model, pain points, tech stack, competitive landscape, budget & timeline, key contacts, strategic initiatives — auto-generated from all account intel |

</details>

<details>
<summary>Intelligence</summary>

| Skill | What it generates |
|---|---|
| `intelligence_brief` | Full-context synthesis via Nemotron-120B — reads every account file at once, produces `intelligence_brief.md` as the primary context source for all downstream skills. Runs automatically before the reasoning cascade; you can also trigger it manually to force a full re-synthesis. |

</details>

---

## MEDDPICC — What JARVIS Is Scoring

Every skill output references MEDDPICC. Here's what each letter means and why it matters:

| Letter | What it checks | Why it matters |
|---|---|---|
| **M** — Metrics | Do you have ROI numbers, cost savings, or productivity gains? | No metrics = no business case |
| **E** — Economic Buyer | Is the person who controls the budget confirmed? | Wrong sponsor = deal dies in procurement |
| **D** — Decision Criteria | Do you know their evaluation requirements? | Don't know criteria = can't win the evaluation |
| **D** — Decision Process | Do you know the approval steps and who's involved? | Process surprises = timeline slips |
| **P** — Paper Process | Has legal/security review started? | Paper = months of surprise delays |
| **I** — Implications | Have you confirmed pain with business impact? | No confirmed pain = no urgency |
| **C** — Champion | Do you have an internal advocate? | No champion = no inside track |
| **C** — Competition | Do you know who you're competing against? | Blind to competition = ambushed at close |

**Score:** GREEN = confirmed with evidence. AMBER = partial or assumed. RED = missing.
Below 40% GREEN = under-qualified. Above 70% GREEN = well qualified.

---

## CRM Dashboard

Opens automatically at **http://localhost:8000** when Claude Desktop starts.

```
Pipeline Overview
  Open Pipeline: $2.4M   |   Win Rate: 34%   |   MEDDPICC Health: 58%

Deals
  Acme Corp   | Demo       | $180k | AMBER risk
  RetailCo    | Qualify    | $95k  | RED risk
  TechCo      | Negotiate  | $240k | GREEN risk
```

Click any account for the **VP-level executive report**:

- **Deal Health Score** — composite (MEDDPICC + Discovery + Risk + Win Prob) shown as Healthy / At Risk / Critical
- **Stakeholder Map** — every contact as a card: Champion (starred), Economic Buyer, Blocker, or Stakeholder — detected automatically from deal notes
- **MEDDPICC full breakdown** — each dimension scored GREEN / AMBER / RED with evidence
- **Value Case & ROI** — full value architecture in context
- **Competitive Intelligence** — competitive position, battlecard, and pricing analysis in one view
- **Deal Health gauges** — 4 bars: MEDDPICC %, Discovery %, Risk Score, Win Probability
- **Export to PDF** — clean print CSS, VP-shareable without CRM access

The report shows everything a VP needs for a deal review in one scroll — no toggling between tabs or tools.

---

## Real Journeys

<details>
<summary><strong>AE: Monday to Friday on a new logo</strong></summary>

**Monday — morning brief:**
```
You: "What's my pipeline look like — Acme, RetailCo, TechCo?"
JARVIS:
  Acme Corp: AMBER — no economic buyer confirmed
  TechCo: RED — timeline risk, 3 weeks to close
  RetailCo: GREEN — strong champion, paper process started
```

**Tuesday — new discovery call:**
```
You: "Create RetailCo. Here are my call notes: [paste]"
JARVIS:
  -> Creates account
  -> Extracts stakeholders, pain, competitors, timeline
  -> "Economic Buyer is RED — contact exists, budget authority not confirmed"
```

**Wednesday — demo prep:**
```
You: "Demo strategy for RetailCo"
JARVIS:
  -> Who's in the room and what each person cares about
  -> Demo flow ordered by their confirmed pain points
  -> What NOT to show
  -> Objection handlers
  -> Hard ask: get POC approval
```

**Thursday — competitive surprise:**
```
You: "RetailCo is re-evaluating Freshdesk. Give me a battlecard."
JARVIS:
  -> Freshdesk's strengths in their segment
  -> Their weaknesses mapped to what RetailCo actually said they need
  -> Killer questions to expose the gap
```

**Friday — proposal requested:**
```
You: "Write a proposal for RetailCo"
JARVIS generates:
  -> Executive Summary (from their discovery notes)
  -> Proposed Solution (maps each requirement to a feature)
  -> Pricing & Timeline (actual ARR + their deadline)
  -> Competitive Positioning (vs Freshdesk)
```

</details>

<details>
<summary><strong>SC: Technical deal and RFP</strong></summary>

**Technical risk assessment:**
```
You: "Technical risk for Acme Corp"
JARVIS:
  -> Integration risks (SSO with Okta, Salesforce API)
  -> Security risks (data residency mentioned)
  -> Gaps (no migration scope discussed yet)
  -> For each: severity, evidence, pre-sales action
```

**Architecture review:**
```
You: "Generate solution architecture for Acme Corp"
JARVIS:
  -> Architecture narrative based on their requirements
  -> Mermaid.js diagram (paste into mermaid.live to visualize)
```

**QBR prep:**
```
You: "Full MEDDPICC for Acme Corp"
JARVIS (all 8 dimensions at once):
  Economic Buyer: RED — budget confirmed but CFO not engaged
  Champion: GREEN — Mike Torres, strong advocate
  Overall: AMBER — 2 critical gaps before commit
```

</details>

<details>
<summary><strong>Morning routine (8am, every day)</strong></summary>

```
Open Claude Desktop
CRM dashboard opens at http://localhost:8000

You: "Brief me — Acme, RetailCo, TechCo"
JARVIS:
  RetailCo: no economic buyer confirmed — priority today
  Acme Corp: paper process RED — follow up on procurement contact
  TechCo: no activity in 8 days — send a nudge

You: "Meeting prep for Acme Corp 2pm call"
JARVIS:
  -> Who's attending, what they care about
  -> Questions to ask, objections to expect
  -> Hard ask
  -> 15 seconds
```

JARVIS doesn't read your calendar automatically — you tell it what's happening, it generates what you need.

</details>

---

## What We Can Build Next

JARVIS is a conversation tool today — you paste context in, it generates intelligence. The next step is connecting it to the systems you already use so data flows automatically.

<details>
<summary><strong>Stage 1: Lead research</strong> — LinkedIn, Google, news</summary>

```
You: "Research RetailCo before my call tomorrow"
Claude:
  -> Pulls company info from LinkedIn
  -> Pulls recent news, funding signals
  -> Creates the account + pre-fills company research
  -> Full brief in 30 seconds
```

</details>

<details>
<summary><strong>Stage 2: CRM sync (two-way)</strong> — Salesforce, HubSpot</summary>

```
You: "Sync Acme Corp with Salesforce"
Claude:
  -> Pulls deal data from CRM
  -> Runs MEDDPICC + risk report
  -> Pushes back: score, risk level, next actions as CRM tasks
```

Salesforce has an official MCP connection in beta. HubSpot has a community one.

</details>

<details>
<summary><strong>Stage 3: Auto-process meetings</strong> — Zoom, Gmail, Calendar</summary>

```
After a call:
  -> Pulls transcript from Zoom recording
  -> Extracts MEDDPICC signals
  -> Drafts follow-up email
  -> Logs activity in CRM
  -> Books next meeting if date was mentioned
```

</details>

<details>
<summary><strong>Stages 4–7: Demo, Proposal, Close, Handoff</strong></summary>

Each stage adds more automation:
- Demo prep pulls from your internal knowledge base (Confluence, Notion)
- Proposals pull from approved pricing templates in Google Drive
- Contract status visible from DocuSign
- On close won: Jira tickets created, CS team notified, full context transferred

**The full picture:**
```
Lead Born     -> Research MCPs   -> account created automatically
Discovery     -> Zoom MCP        -> notes extracted, CRM updated
Demo          -> Confluence MCP  -> solution docs pulled in
Proposal      -> Drive MCP       -> templates used, proposal saved
Close         -> DocuSign MCP    -> contract tracked
Handoff       -> Jira + Slack    -> implementation kicked off, nothing lost
```

</details>

---

## NVIDIA Keys — Getting More

You can get up to 5 free keys from the same account:

1. Go to **build.nvidia.com**
2. Profile → API Keys → Generate Key
3. Open the `.env` file in the JARVIS folder (any text editor) and add:

```
NVIDIA_API_KEY=nvapi-firstkey...
NVIDIA_API_KEY_2=nvapi-secondkey...
NVIDIA_API_KEY_3=nvapi-thirdkey...
```

After saving `.env`, restart Claude Desktop for the new keys to load.

**Why more than one?** JARVIS generates multiple sections of a document at the same time (e.g. MEDDPICC scores all 8 dimensions simultaneously). With one key, you can occasionally hit NVIDIA's usage limits mid-generation. With 3-5 keys, requests rotate automatically — no waiting, no failed outputs.

---

## Troubleshooting

<details>
<summary>JARVIS not showing in Claude Desktop (no hammer icon)</summary>

Open Terminal and run:
```
bash setup.sh
```
Then fully quit Claude Desktop (Cmd+Q on Mac) and reopen it.
</details>

<details>
<summary>"All NVIDIA keys exhausted" error</summary>

1. Open the `.env` file in the JARVIS folder
2. Confirm `NVIDIA_API_KEY=nvapi-...` is there and correct
3. If rate-limited: wait 60 seconds, JARVIS recovers automatically
4. Or add more keys as shown above
</details>

<details>
<summary>Skills returning "TBD — needs discovery"</summary>

This is correct, not an error. JARVIS only generates from your notes. Open `discovery.md` for that account and add more context from your calls.
</details>

<details>
<summary>CRM dashboard not loading at http://localhost:8000</summary>

Run `bash setup.sh` again — it'll re-register the dashboard with Claude Desktop. Then restart Claude Desktop.
</details>

<details>
<summary>Setup script fails on Windows</summary>

Make sure you're running it inside WSL (Ubuntu) or Git Bash, not the regular Windows Command Prompt or PowerShell. The script requires a Unix-style shell.
</details>

---

## Technical Stack (for the curious)

| What | What it actually is |
|---|---|
| Claude Desktop | The app you chat in. Loads JARVIS as a plugin. |
| JARVIS MCP Server | Python process exposing 28 tools via MCP protocol |
| Multi-model router | Routes each task to the right model type (synthesis/reasoning/writing/fast) with cascade failover |
| NVIDIA NIM | Hosted inference API — **nemotron-3-super-120b** (1M ctx, synthesis only), kimi-k2-thinking, kimi-k2-instruct, qwq-32b, qwen2-7b, step-3.5-flash |
| IntelligenceBriefSkill | Nemotron-powered synthesis — reads ALL account files with zero truncation, writes `intelligence_brief.md` as primary context for all downstream skills |
| BriefCoordinator | Pure async Python — appends key findings from each completed skill as delta blocks to `intelligence_brief.md`; zero extra API calls; per-account asyncio.Lock prevents write corruption |
| File Watcher | watchdog OS-level monitor — detects source file changes + any new file dropped in |
| Skill Queue | Priority queue (HIGH → MEDIUM → LOW) with deduplication |
| Queue Worker | Async background worker — runs skills, triggers BriefCoordinator delta append + cascade |
| IntelligenceExtractor | LLM-powered — extracts structured deal intel from any text (files, outputs, chat) |
| KnowledgeMerger | Appends extracted intel to discovery.md — append-only, timestamped, never overwrites |
| SelfLearner | `_skill_timeline.json` + `_evolution_log.md` per account — read by all skills as context |
| CRM Sidecar | Small web server at localhost:8000 — VP-level executive pipeline dashboard |

---

## Adding Your Own Skills

Each skill is one Python file. Copy an existing one, change the prompts, register it. You don't need to understand MCP or async Python — the pattern is always the same.

<details>
<summary>See the template</summary>

```python
# jarvis_mcp/skills/my_skill.py
from jarvis_mcp.skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {"name": "Section One", "prompt": f"{base} write section one...", "max_tokens": 800},
            {"name": "Section Two", "prompt": f"{base} write section two...", "max_tokens": 800},
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "my_skill.md", response)
        return response
```

Then register in `jarvis_mcp/skills/__init__.py`, add the tool in `jarvis_mcp_server.py`, restart Claude Desktop.

</details>

---

## Is This Production Ready?

**For one AE or SC using it personally: yes.**

| What works | Status |
|---|---|
| 27 skills generate grounded outputs | ✅ |
| Autonomous retry with quality validation | ✅ |
| Rate limit recovery — waits and retries automatically | ✅ |
| Startup scan — skips already-generated outputs on restart | ✅ |
| Multi-model routing with cascade failover | ✅ |
| File watcher starts on Claude Desktop boot | ✅ |
| Any dropped file auto-ingested into knowledge base | ✅ |
| Skill outputs feed back into discovery.md | ✅ |
| Full cascade fires in correct priority order | ✅ |
| Cycle guard prevents infinite feedback loops | ✅ |
| Cross-platform: Mac, Linux, Windows (WSL) | ✅ |
| Fresh clone → `bash setup.sh` → works | ✅ |

**Not ready for (would need additional build):**

| What's missing | Impact |
|---|---|
| No multi-user support | One person per installation |
| Deal data stored as plain text | Anyone with file access reads everything |
| NVIDIA keys in `.env` plain text | Single point of compromise |
| No multi-device sync | Deal data tied to one machine |
| No sync across devices | Tied to one machine |

Bottom line: fork it, run `setup.sh`, add your NVIDIA keys, restart Claude Desktop. It works for one salesperson managing their own deals. For a company deploying it across a team — that's a different build.

---

## License

MIT — fork it, customize it, use it commercially.

## Contributing

PRs welcome. If you build a skill that works well in your workflow, open a PR — other AEs and SCs will benefit.

---

**Built by an AE/SC who got tired of spending more time writing about deals than working them.**

*Proposal time: 3 hours → 12 minutes. Meeting prep: 1 hour → 15 seconds. Zero deliverables written manually.*

*Fork it. Add your keys. Try it on one deal today.*
