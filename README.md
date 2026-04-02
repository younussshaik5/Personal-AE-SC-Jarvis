# JARVIS — AI Sales Intelligence for Claude Desktop

> **You're spending 5-8 hours a week on proposals, battlecards, meeting prep, and MEDDPICC scoring. That's time you're not selling.** JARVIS cuts it to minutes.

---

## The Problem

You close a discovery call. Now you need to:
- Update CRM notes (30 min)
- Score MEDDPICC for your manager (45 min)
- Write a follow-up email (20 min)
- Build a battlecard before the next call (1-2 hours)
- Draft a proposal by Friday (2-3 hours)

That's a full day of writing instead of selling. Every week.

## The Fix

Paste your call notes into Claude. Ask for what you need. Get it in seconds -- grounded in your actual deal data, not generic templates.

```
You:  "Update Acme Corp -- Sarah confirmed $180k budget, Q3 deadline,
       competing with Freshdesk, champion is Mike in IT.
       Score MEDDPICC and give me a battlecard."

JARVIS (15 seconds later):
  MEDDPICC:
    Economic Buyer: AMBER -- budget confirmed but CFO not engaged
    Champion: GREEN -- Mike Torres, strong internal advocate
    Competition: GREEN -- Freshdesk confirmed, Zendesk eliminated
    Paper Process: RED -- no procurement contact identified
    >> Top gap: get CFO in the room before demo

  Battlecard vs Freshdesk:
    Their strength: lower price point, simple setup
    Their weakness: no enterprise SSO, limited API
    Your edge: Okta SSO + Salesforce integration (confirmed requirements)
    Killer question: "How are you handling SSO across 500 users today?"
```

No copy-pasting between tools. No blank templates. Everything references what the customer actually said.

---

## Who This Is For

| **Use it if you...** | **Skip it if you...** |
|---|---|
| Handle both AE and SC work | Have a dedicated sales ops team doing this for you |
| Manage 5-15 active deals | Are happy with your current CRM workflow |
| Already use Claude Desktop | Need a point-and-click GUI |
| Want better prep, faster | Want a tool that replaces your CRM |
| Are comfortable running a bash script once | Want zero terminal interaction |

---

## What It Is (One Paragraph)

JARVIS is a free plugin for Claude Desktop. It gives Claude 24 specialist sales tools -- battlecards, MEDDPICC scoring, proposals, risk reports, demo strategies, follow-up emails, and more. You keep a simple folder of notes for each deal on your computer. JARVIS reads those notes and generates intelligence from them. It never invents facts. If something isn't in your notes, it says "TBD -- needs discovery."

---

## Day 1 vs Day 30

Set expectations. JARVIS is only as good as the data you feed it.

| | What you get |
|---|---|
| **Day 1** | Generic templates. Lots of "TBD -- needs discovery." Useful for scaffolding, not much else. |
| **Day 7** | After 2-3 discovery calls worth of notes, outputs start referencing real stakeholders, real pain points, real competitors. Battlecards and meeting prep become genuinely useful. |
| **Day 30** | JARVIS knows your deals better than your CRM. Proposals pull actual ARR, risk reports flag specific gaps, MEDDPICC scores have evidence behind every dimension. You stop writing deliverables entirely. |

**The golden rule:** you add notes, JARVIS gets sharper. No notes = generic output.

---

## Quick Start (3 commands)

```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
bash setup.sh
```

`setup.sh` handles everything: installs Python dependencies, walks you through NVIDIA API key setup, registers JARVIS with Claude Desktop. Works on Mac, Windows (WSL), and Linux.

After setup: quit Claude Desktop (Cmd+Q on Mac) and reopen. Look for the hammer icon in the chat bar -- that's JARVIS.

<details>
<summary><strong>Detailed installation walkthrough</strong> (click to expand)</summary>

### Prerequisites

**1. Mac, Windows, or Linux**
- Mac: works natively
- Windows: use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) or Git Bash
- Linux: works natively

**2. Claude Desktop** (free)
- Download from [claude.ai/download](https://claude.ai/download)

**3. An NVIDIA API Key** (free tier available)
- Go to [build.nvidia.com](https://build.nvidia.com/) -> sign up -> API Keys -> Generate Key
- Copy the key (starts with `nvapi-`)

### What `setup.sh` does

```
+---------------------------------------------------+
|  JARVIS MCP -- Setup                               |
+---------------------------------------------------+

1. Checks Python 3.10+ (installs via Homebrew on Mac if missing)
2. Installs Python dependencies (mcp, openai, pydantic, etc.)
3. Fixes SSL certificates (macOS only)
4. Verifies JARVIS imports
5. Asks for your NVIDIA API key(s) interactively
6. Creates your ACCOUNTS folder at ~/JARVIS/ACCOUNTS/
7. Registers JARVIS + CRM sidecar in Claude Desktop config
8. Runs smoke test
```

You can run `setup.sh` again anytime -- it won't overwrite your `.env` keys or account data.

### After setup

1. Quit Claude Desktop completely (Cmd+Q on Mac, not just close the window)
2. Reopen Claude Desktop
3. Click the hammer icon in the chat bar -- you should see JARVIS tools listed
4. CRM dashboard auto-opens at http://localhost:8000
5. Say: "Create an account for [your first deal]"

</details>

---

## Your First 5 Minutes

### 1. Create an account

```
"Create an account for Acme Corp. They're a 500-person logistics company
evaluating us to replace Salesforce Service Cloud. Primary contact is
Sarah Chen, VP Operations. ARR target is $180k."
```

JARVIS creates a folder with all templates pre-filled.

### 2. Add discovery notes

```
"Update Acme Corp:
- Sarah confirmed budget $150-200k, approved
- Timeline Q3 -- Salesforce contract ends June 30
- Pain: agents spend 40% time switching between 5 systems
- Evaluated Zendesk last year, eliminated for pricing
- Need SSO with Okta and Salesforce integration
- Champion: Mike Torres, IT Director, very engaged"
```

### 3. Generate what you need

```
"Score MEDDPICC for Acme Corp"
"Battlecard vs Salesforce for Acme Corp"
"Prep me for my meeting with Sarah tomorrow"
"Write a proposal for Acme Corp"
```

Each fires in parallel -- a 7-section proposal generates all sections simultaneously.

---

## The 24 Skills

Every skill generates from your actual deal data. No hallucinated facts.

### Start Here (try these first)

| Skill | What you get |
|---|---|
| `get_account_summary` | Full deal dossier -- stage, stakeholders, risks, next actions |
| `track_meddpicc` | All 8 dimensions scored simultaneously with evidence and gaps |
| `get_battlecard` | Win/loss positioning vs the actual competitor in your deal |
| `get_meeting_prep` | Who's attending, what to ask, objection handlers, hard ask |
| `quick_insights` | Fast snapshot -- stage, risk level, recommended next action |

### All Skills by Category

<details>
<summary><strong>Deal Intelligence</strong></summary>

| Skill | What it generates | Parallel sections |
|---|---|---|
| `get_account_summary` | Full deal dossier from saved notes | 4 |
| `quick_insights` | Fast deal snapshot | 2 |
| `track_meddpicc` | MEDDPICC scorecard | **9** (one per dimension + summary) |
| `update_deal_stage` | Updates stage, ARR, probability | -- |

</details>

<details>
<summary><strong>Competitive & Positioning</strong></summary>

| Skill | What it generates | Parallel sections |
|---|---|---|
| `get_battlecard` | Competitor profile, differentiators, objection handlers | 3 |
| `get_competitive_intelligence` | Deep competitive analysis | 3 |
| `analyze_competitor_pricing` | Pricing comparison + strategy | 3 |

</details>

<details>
<summary><strong>Deal Execution</strong></summary>

| Skill | What it generates | Parallel sections |
|---|---|---|
| `get_proposal` | Full commercial proposal | 4 |
| `generate_sow` | Statement of Work | 3 |
| `get_value_architecture` | ROI model, TCO, value case | 3 |
| `generate_followup` | 2 email options (direct + consultative) | 2 |

</details>

<details>
<summary><strong>Risk & Discovery</strong></summary>

| Skill | What it generates | Parallel sections |
|---|---|---|
| `get_risk_report` | RED/AMBER/GREEN risk report | 4 |
| `assess_technical_risk` | Technical blocker analysis | 2 |
| `get_discovery` | Discovery framework + gaps | 2 |
| `get_meeting_prep` | Pre-meeting brief | 3 |

</details>

<details>
<summary><strong>Meeting & Communication</strong></summary>

| Skill | What it generates | Parallel sections |
|---|---|---|
| `process_meeting` | Meeting summary + deal impact | 2 |
| `summarize_conversation` | Conversation analysis | 2 |
| `extract_intelligence` | MEDDPICC signals from any text | 2 |
| `get_demo_strategy` | Demo flow + script | 3 |

</details>

<details>
<summary><strong>Technical & Documentation</strong></summary>

| Skill | What it generates | Parallel sections |
|---|---|---|
| `generate_architecture` | Mermaid.js solution diagram | 2 |
| `build_knowledge_graph` | Stakeholder + deal map | 2 |
| `generate_documentation` | Technical/sales docs | 2 |
| `generate_html_report` | HTML report for stakeholders | 2 |
| `generate_custom_template` | Any custom document | 2 |

</details>

---

## How Parallel Generation Works

**Without parallel:** Score Metrics -> then Economic Buyer -> then Decision Criteria -> ... -> 9 sequential LLM calls. ~70 seconds total.

**With parallel:** All 9 MEDDPICC dimensions fire simultaneously. ~10 seconds total.

JARVIS splits every skill into independent sections and generates them all at once using `asyncio.gather`. A 4-section proposal takes the same wall-clock time as generating 1 section.

**Why multiple NVIDIA keys matter:** If you fire 9 parallel requests on 1 key, you'll hit NVIDIA's rate limit. With 5 keys, requests round-robin automatically -- each key handles 1-2 requests, none hit limits.

---

## Your Account Folders

Everything lives in a folder on your computer. JARVIS reads from it and writes back to it.

### Where

```
~/JARVIS/ACCOUNTS/
```

- **Mac:** Finder -> Cmd+Shift+G -> paste `~/JARVIS/ACCOUNTS`
- **Windows:** File Explorer -> `%USERPROFILE%\JARVIS\ACCOUNTS`
- **Linux:** `~/JARVIS/ACCOUNTS`

### What's inside each account

```
~/JARVIS/ACCOUNTS/AcmeCorp/
|
|  -- YOU WRITE THESE ------------------------------------
|-- discovery.md           <- YOUR MOST IMPORTANT FILE
|                             Paste call notes here. Everything
|                             JARVIS generates improves as this fills up.
|-- company_research.md    <- Company background, LinkedIn, news
|-- CLAUDE.md              <- Account-specific instructions for JARVIS
|                             "Don't mention pricing until technical
|                              validation is done."
|-- deal_stage.json        <- Deal metadata (JARVIS auto-manages this)
|
|  -- JARVIS WRITES THESE (don't edit) -------------------
|-- battlecard.md
|-- meddpicc.md
|-- risk_report.md
|-- proposal.md
|-- ... (one file per skill)
```

### How to add notes

**Easiest -- just tell Claude:**
```
"Update Acme Corp discovery notes:
- CFO confirmed $180k budget
- Timeline hard: contract ends June 30
- Champion is Mike Torres, IT Director"
```

**Or edit the file directly:** Open `~/JARVIS/ACCOUNTS/AcmeCorp/discovery.md` in any text editor. Plain English, no special format needed. JARVIS reads it next time you ask for anything.

**Or paste a transcript:**
```
"Process this meeting for Acme Corp: [paste transcript]"
```

### Enterprise accounts (parent/child)

For large companies with multiple deals:

```
ACCOUNTS/
+-- Tata/                        <- parent
|   |-- company_research.md      <- shared across all Tata deals
|   |-- TataTeleservices/        <- child deal (own pipeline)
|   |   |-- deal_stage.json
|   |   +-- discovery.md
|   +-- TataSky/                 <- separate child deal
|       |-- deal_stage.json
|       +-- discovery.md
```

Write company research once, every child deal inherits it. Create with: `scaffold_account` with parent name `Tata`.

### Don't do this

- Don't rename JARVIS-generated files -- it looks for them by exact name
- Don't edit `deal_stage.json` manually -- tell Claude to update it
- Don't worry about formatting in `discovery.md` -- plain sentences work fine

---

## MEDDPICC Framework

JARVIS uses MEDDPICC as the backbone for all deal qualification.

| Dimension | What JARVIS looks for | Why it matters |
|---|---|---|
| **M**etrics | ROI, cost savings, productivity gains | No metrics = no business case |
| **E**conomic Buyer | Person with budget authority confirmed | Wrong sponsor = deal dies in procurement |
| **D**ecision Criteria | Evaluation requirements documented | Don't know criteria = can't win eval |
| **D**ecision Process | Procurement steps, approval chain | Process surprises = timeline slips |
| **P**aper Process | Legal, security review, MSA status | Paper = months of surprise delays |
| **I**mplications | Pain points with business impact | No pain = no urgency |
| **C**hampion | Internal advocate selling for you | No champion = no inside track |
| **C**ompetition | Competitors named, status known | Blind to competition = ambushed at close |

**Scoring:** GREEN = confirmed with evidence. AMBER = partial or assumed. RED = missing or unknown.
Below 40% GREEN = under-qualified. Above 70% = well qualified.

---

## CRM Dashboard

Auto-starts at **http://localhost:8000** when Claude Desktop opens.

```
Pipeline Overview
|-- Open Pipeline: $2.4M
|-- Weighted Pipeline: $980k
|-- Win Rate: 34%
|-- MEDDPICC Health: 58% (AMBER)

Deal Stage Funnel
Discovery (3) -> Qualify (2) -> Demo (4) -> Negotiate (1) -> Close (2)

Pipeline Table
Account      | Stage     | ARR    | MEDDPICC | Risk
AcmeCorp     | Demo      | $180k  | 62%      | AMBER
RetailCo     | Qualify   | $95k   | 38%      | RED
TechCo       | Negotiate | $240k  | 78%      | GREEN
```

Click any account for full drill-down: MEDDPICC scorecard, risk breakdown, all skill outputs, "Generate All" button, PDF export.

---

## Real User Journeys

<details>
<summary><strong>Journey 1: AE working a new logo (Monday-Friday)</strong></summary>

**Monday morning:**
```
You: "What's my pipeline look like?"
JARVIS: [pulls quick_insights for all active deals]
  Acme Corp: AMBER -- no economic buyer confirmed
  TechCo: RED -- timeline risk, 3 weeks to close
  StartupX: GREEN -- strong champion, paper process started
```

**Tuesday -- discovery call:**
```
You: "Create account for RetailCo. Here are my notes: [paste]"
JARVIS:
  -> Creates RetailCo account
  -> Extracts stakeholders, pain, competitors, timeline
  -> Scores MEDDPICC: M=AMBER, E=RED, D=GREEN...
  -> "Economic Buyer is RED -- contact exists but no budget authority confirmed"
```

**Wednesday -- demo prep:**
```
You: "Demo strategy for RetailCo"
JARVIS generates in parallel:
  -> Demo objective: get POC approval
  -> Audience: CTO cares about integrations, CFO cares about ROI
  -> Demo flow ordered by their confirmed pain points
  -> What NOT to show: enterprise features they can't afford yet
  -> Objection handlers
  -> Hard ask: POC start date
```

**Thursday -- competitive objection:**
```
You: "RetailCo re-evaluating Freshdesk. Battlecard?"
JARVIS:
  -> Freshdesk strengths in their segment
  -> Weaknesses tied to what RetailCo actually said they need
  -> Killer questions to expose Freshdesk's gap
```

**Friday -- proposal requested:**
```
You: "Generate proposal for RetailCo"
JARVIS fires 4 sections in parallel:
  -> Executive Summary (from discovery notes)
  -> Proposed Solution (maps requirements to features)
  -> Pricing & Timeline (actual ARR + their deadline)
  -> Competitive Positioning (vs Freshdesk)
```

</details>

<details>
<summary><strong>Journey 2: SC working a technical deal</strong></summary>

**RFP response:**
```
You: "Technical risk assessment for Acme Corp"
JARVIS identifies in parallel:
  -> Integration risks: SSO with Okta, Salesforce API complexity
  -> Security risks: data residency requirements mentioned
  -> Unknown gaps: no mention of data migration scope
  For each: Severity, Evidence, Pre-sales action, Resolution path
```

**Architecture review:**
```
You: "Generate solution architecture for Acme Corp"
JARVIS:
  -> Architecture narrative: components + data flows
  -> Mermaid.js diagram (paste into mermaid.live for visual)
```

**QBR prep:**
```
You: "Full MEDDPICC for Acme Corp"
JARVIS fires all 9 sections simultaneously:
  Metrics: AMBER -- ROI mentioned but not quantified
  Economic Buyer: RED -- budget confirmed but CFO not engaged
  Decision Criteria: GREEN -- full eval list from RFP
  Champion: GREEN -- Mike Torres, strong advocate
  Overall: AMBER -- 2 critical gaps before commit
```

</details>

<details>
<summary><strong>Journey 3: Morning routine</strong></summary>

```
[Open Claude Desktop at 8am]
CRM dashboard opens at http://localhost:8000

You: "Brief me -- Acme Corp, RetailCo, TechCo"
  -> RetailCo: MEDDPICC gaps -- no economic buyer confirmed
  -> Acme Corp: timeline tight, paper process RED
  -> TechCo: last activity 8 days ago -- suggest follow-up

You: "Meeting prep for Acme Corp call at 2pm"
  -> Who's attending, what to ask, objection handlers, hard ask
  -> ~15 seconds
```

Note: JARVIS doesn't read your calendar. You tell it what's happening, it generates what you need.

</details>

---

## What We Can Build Next -- Full Sales Cycle via MCP

JARVIS is the intelligence layer. MCP can connect it to every system in your sales stack. Here's the full picture from lead to close.

<details>
<summary><strong>Stage 1: Lead Born & Research</strong> -- LinkedIn, Google Search, Crunchbase MCPs</summary>

```
You: "Research RetailCo before my call tomorrow"
Claude:
  -> [LinkedIn MCP]      -- company page, decision-maker profiles
  -> [Google Search MCP] -- recent news, funding, tech stack
  -> [JARVIS]            -- scaffold account + populate company_research.md
  -> Full pre-call brief in 30 seconds
```

| Integration | MCP exists? |
|---|---|
| LinkedIn | Yes (unofficial) |
| Google Search | Yes |
| Crunchbase | Possible (API wrappable) |

</details>

<details>
<summary><strong>Stage 2: CRM Sync (Bi-directional)</strong> -- Salesforce, HubSpot, Pipedrive MCPs</summary>

```
You: "Sync Acme Corp"
Claude:
  -> [CRM MCP]  -- pulls Opportunity, Contacts, Activities
  -> [JARVIS]   -- populates deal data, runs MEDDPICC + risk report
  -> [CRM MCP]  -- pushes back: MEDDPICC score, risk level, next actions as Tasks
```

What gets written back automatically: MEDDPICC score, risk level, stage changes, top 3 next actions, champion/EB confirmation, key insights.

| CRM | MCP Status |
|---|---|
| Salesforce | Official MCP in beta |
| HubSpot | Community MCP available |
| Pipedrive | API wrappable |

</details>

<details>
<summary><strong>Stage 3: Discovery & Meetings</strong> -- Zoom, Gmail, Calendar MCPs</summary>

```
After a call:
  -> [Zoom MCP]                  -- pulls transcript
  -> [JARVIS process_meeting]    -- extracts signals, updates deal
  -> [Gmail MCP]                 -- drafts follow-up email
  -> [CRM MCP]                   -- logs activity, creates tasks
  -> [Calendar MCP]              -- schedules next meeting
```

</details>

<details>
<summary><strong>Stage 4: Demo & Technical</strong> -- Confluence, Jira MCPs</summary>

```
  -> [JARVIS get_demo_strategy]     -- custom flow from discovery
  -> [JARVIS generate_architecture] -- Mermaid.js diagram
  -> [Confluence MCP]               -- pulls internal solution docs
  -> [Jira MCP]                     -- checks similar past implementations
```

</details>

<details>
<summary><strong>Stage 5: Proposal & Commercial</strong> -- Google Drive, DocuSign MCPs</summary>

```
  -> [CRM MCP]             -- pulls ARR, terms
  -> [Drive MCP]           -- pulls approved templates
  -> [JARVIS get_proposal] -- generates grounded proposal
  -> [Drive MCP]           -- saves to shared folder
  -> [Gmail MCP]           -- drafts send email
```

</details>

<details>
<summary><strong>Stage 6: Negotiation & Close</strong> -- DocuSign, Slack MCPs</summary>

```
  -> [JARVIS get_risk_report] -- RED blockers
  -> [DocuSign MCP]           -- contract status, who hasn't signed
  -> [Slack MCP]              -- deal room signals
  -> [Email MCP]              -- days since last response
```

</details>

<details>
<summary><strong>Stage 7: Closed Won -> Handoff</strong> -- Jira, Slack MCPs</summary>

```
  -> [JARVIS generate_sow]        -- SOW from actual discovery
  -> [Jira MCP]                   -- creates implementation project
  -> [Slack MCP]                  -- posts to #new-customers
  -> [CRM MCP]                   -- updates account record
```

</details>

### The Full Pipeline

```
Lead Born        -> LinkedIn + Search MCPs -> company_research.md
    |
CRM Sync         -> Salesforce/HubSpot MCP -> deal_stage.json (bi-directional)
    |
Discovery        -> Zoom/Meet MCP -> transcripts -> JARVIS -> CRM updated
    |
Demo & Technical -> Confluence/Jira -> solution docs + architecture
    |
Proposal         -> Drive MCP -> templates -> JARVIS -> Drive (saved)
    |
Negotiation      -> DocuSign + Slack -> blocker tracking + deal room
    |
Closed Won       -> Jira + Slack + CRM -> full handoff, zero context lost
```

JARVIS is the intelligence layer. MCP is the connectivity layer. Together they cover the full revenue cycle.

---

## Why Kimi K2 Thinking?

Most AI writing tools generate from templates. Kimi K2 Thinking reasons through your deal first -- it evaluates gaps, weighs tradeoffs, identifies what's missing -- then writes. That's why the MEDDPICC scores feel strategic rather than mechanical, and the proposals reference specific customer pain points instead of generic value props.

The model runs on NVIDIA's hosted inference (NIM). Free tier is enough for daily use.

### Getting NVIDIA keys

1. Go to [build.nvidia.com](https://build.nvidia.com/)
2. Sign in -> profile -> API Keys -> Generate Key
3. Add to `.env`:

```bash
NVIDIA_API_KEY=nvapi-key1...
NVIDIA_API_KEY_2=nvapi-key2...    # optional
NVIDIA_API_KEY_3=nvapi-key3...    # optional
```

**How many?** 1 works. 3-5 recommended if you run JARVIS heavily -- parallel generation spreads requests across keys automatically.

---

## Troubleshooting

<details>
<summary><strong>JARVIS not showing in Claude Desktop (no hammer icon)</strong></summary>

```bash
bash setup.sh   # re-run setup
# Then Cmd+Q Claude Desktop and reopen (don't just close the window)
```
</details>

<details>
<summary><strong>"All NVIDIA keys exhausted" or API errors</strong></summary>

1. Check `.env` -- verify `NVIDIA_API_KEY=nvapi-...` is correct
2. Test at [build.nvidia.com](https://build.nvidia.com/) playground
3. If rate-limited: wait 60 seconds (auto-recovers) or add more keys
4. Keys must be in `.env` file, not just shell environment
</details>

<details>
<summary><strong>Skills returning "TBD -- needs discovery"</strong></summary>

This is correct behavior. JARVIS only generates from your data. Add more notes to `discovery.md` for that account.
</details>

<details>
<summary><strong>CRM dashboard not loading</strong></summary>

```bash
# Check if registered
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep jarvis-crm
# If missing, re-run setup.sh
```
</details>

<details>
<summary><strong>Python or import errors</strong></summary>

```bash
bash setup.sh   # safe to re-run, won't overwrite .env or accounts
```
</details>

---

## Adding Your Own Skills

Each skill is one Python file. Copy any existing skill and change the prompts:

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

Register in `jarvis_mcp/skills/__init__.py`, add the MCP tool in `jarvis_mcp_server.py`, restart Claude Desktop. Done.

---

## Technical Stack

| Component | What it is |
|---|---|
| Claude Desktop | The UI -- where you chat. MCP client. |
| JARVIS MCP Server | Python process exposing 24 tools via MCP |
| Kimi K2 Thinking | `moonshotai/kimi-k2-thinking` -- reasoning model on NVIDIA NIM |
| NVIDIA NIM | Hosted inference API at `integrate.api.nvidia.com/v1` |
| CRM Sidecar | Separate Python process serving the web dashboard |
| `asyncio.gather` | Parallel execution -- fires multiple LLM calls simultaneously |

---

## License

MIT -- fork it, customize it, use it commercially.

## Contributing

PRs welcome. The codebase is intentionally simple: 24 skill files, one base class, one LLM manager. No frameworks beyond what's needed. You don't need to understand MCP or async Python to add a skill -- just copy one and change the prompts.

---

**Built by an AE/SC who got tired of spending more time writing about deals than working them. Try it on one deal this week.**

*Used daily across 40+ deals. Proposal time: 3 hours -> 12 minutes. Meeting prep: 1 hour -> 15 seconds.*
