# Advanced Usage - For Sales/Presales Professionals

**How to leverage JARVIS for maximum impact in your daily workflow.**

---

## MCP Auto-Run on Claude Desktop Open

### Current Setup (One Time)
Your `.claude/settings.json` has:
```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python",
      "args": ["-m", "jarvis_mcp.mcp_server"],
      "env": {
        "NVIDIA_API_KEY": "your_key"
      }
    }
  }
}
```

### What Happens
When you open Claude Desktop:
- ✅ MCP server auto-starts
- ✅ All 24 skills auto-load
- ✅ Preferences auto-load from `~/.claude/preferences.json`
- ✅ Account folders auto-detected
- ✅ Ready to use immediately

**No manual steps.** Just open Claude Desktop and JARVIS is ready.

---

## Nested Folders & Auto-Detection

### Folder Structure That Works

```
~/Documents/claude space/ACCOUNTS/
│
├── AcmeCorp/                    (Flat - works ✓)
│   ├── company_research.md
│   ├── discovery.md
│   ├── deal_stage.json
│   └── proposal.md              (Auto-generated)
│
├── 2024_Q1_Deals/               (Nested - works ✓)
│   ├── Acme Corp/
│   │   ├── company_research.md
│   │   ├── discovery.md
│   │   ├── deal_stage.json
│   │   └── proposal.md
│   ├── TechCorp/
│   │   ├── company_research.md
│   │   ├── discovery.md
│   │   ├── deal_stage.json
│   │   └── proposal.md
│   └── GlobalBank/
│       ├── company_research.md
│       ├── discovery.md
│       ├── deal_stage.json
│       └── proposal.md
│
├── ByRegion/                    (Nested - works ✓)
│   ├── North America/
│   │   ├── EMEA Accounts/
│   │   │   ├── Account1/
│   │   │   ├── Account2/
│   │   │   └── Account3/
│   │   └── APAC Accounts/
│   └── ...
│
└── ByTeam/                      (Nested - works ✓)
    ├── Sarah's Team/
    │   ├── Account1/
    │   └── Account2/
    ├── Mike's Team/
    │   ├── Account1/
    │   └── Account2/
    └── Lisa's Team/
        ├── Account1/
        └── Account2/
```

### How JARVIS Auto-Detects

```
@jarvis-mcp get_proposal account=Account1
```

JARVIS searches:
1. Direct: `~/Documents/claude space/ACCOUNTS/Account1/`
2. Nested 1: `~/Documents/claude space/ACCOUNTS/*/Account1/`
3. Nested 2: `~/Documents/claude space/ACCOUNTS/*/*/Account1/`
4. Deep: `~/Documents/claude space/ACCOUNTS/**/Account1/`

**Finds it at any nesting level.**

### Using Nested Folders

```
# Top-level (works)
@jarvis-mcp get_proposal account=Acme Corp

# Nested one level (works)
@jarvis-mcp get_proposal account=Acme Corp
# Found in: 2024_Q1_Deals/Acme Corp/

# Nested deep (works)
@jarvis-mcp get_proposal account=Account1
# Found in: ByRegion/North America/EMEA Accounts/Account1/

# Works anywhere
@jarvis-mcp get_proposal account=Account1
# Found automatically at any depth
```

---

## Dashboard & Opportunity Reporting

### Current: File-Based Dashboard

Each account automatically generates:

```
Account Folder:
├── company_research.md           (Your company info)
├── discovery.md                  (Your discovery notes)
├── deal_stage.json               (Structured data)
│
├── proposal.md                   (Generated)
├── battlecard.md                 (Generated)
├── demo_strategy.md              (Generated)
├── risk_report.md                (Generated with risk analysis)
├── value_architecture.md         (Generated with ROI)
│
└── [20 more generated files]     (All auto-created)
```

### Viewing Your Dashboard

**Via Claude Code:**
```
Claude, give me a summary of Account1

Claude calls:
1. Read account1/company_research.md
2. Read account1/discovery.md
3. Read account1/deal_stage.json
4. Compile into: Deal status, timeline, risks, value

Returns: Your deal dashboard
```

**Via Text Editor:**
```
Open: ~/Documents/claude space/ACCOUNTS/Account1/
View all files
See generated content
```

### Available Dashboard Data

**From `deal_stage.json`:**
```json
{
  "stage": "Demo",                    ← Current stage
  "probability": 65,                  ← Win probability
  "deal_size": 500000,               ← Deal size
  "timeline": "Q3 2026",             ← Expected close
  "stakeholders": [                   ← Who's involved
    "CTO",
    "VP Sales",
    "CFO"
  ],
  "last_updated": "2026-04-01"       ← When updated
}
```

**From `risk_report.md` (auto-generated):**
```
# Risk Report

## Critical Risks
- Implementation complexity
- Team readiness
- Budget approval

## Timeline Risks
- 6-month implementation window
- Executive approval lag

## Competition
- ServiceCo counter-proposal
- Internal build evaluation

## Mitigation Strategy
[Auto-generated recommendations]
```

**From `value_architecture.md` (auto-generated):**
```
# ROI Analysis

## Cost Savings
- Automated processing: $300k/year
- Team efficiency: $200k/year
- Total: $500k/year

## Implementation Cost
- Licensing: $300k
- Implementation: $200k
- Total: $500k

## ROI Timeline
- Year 1: Break-even
- Year 2: $500k net gain
- Year 3: $1.5M net gain
```

---

## Workflow for Sales/Presales

### Daily Workflow

**Morning:**
```
1. Open Claude Desktop
   → JARVIS auto-starts
   → MCP loaded
   → All skills ready

2. Ask Claude
   @jarvis-mcp get_risk_report account=YourAccount
   
   Returns: Current deal risks to mitigate

3. Check your calendar
   Upcoming meeting with CTO
```

**Before Meeting:**
```
1. Ask Claude
   @jarvis-mcp get_demo_strategy account=YourAccount audience=CTO
   
   Returns: Demo flow optimized for CTO
   
2. Get competitive positioning
   @jarvis-mcp get_battlecard account=YourAccount competitor=ServiceCo
   
   Returns: How to position vs ServiceCo
   
3. Claude compiles
   → Demo talking points
   → Competitive angles
   → Technical differentiators
   → ROI impact
```

**After Meeting:**
```
1. Update your files
   Edit: YourAccount/discovery.md
   (Add what you learned)

2. JARVIS auto-regenerates
   @jarvis-mcp get_risk_report account=YourAccount
   
   Returns: Updated risks based on new info
   
3. Generate follow-up
   @jarvis-mcp generate_followup account=YourAccount
   
   Returns: Personalized follow-up email
```

**Weekly:**
```
1. Check pipeline health
   Claude calls JARVIS for all accounts:
   
   @jarvis-mcp quick_insights account=Account1
   @jarvis-mcp quick_insights account=Account2
   @jarvis-mcp quick_insights account=Account3
   
   Returns: Risk levels, timeline status, next steps

2. Pipeline Review
   All deal statuses in one place
   
3. Update forecasts
   Based on risk assessments
```

---

## Advanced Features for Teams

### Shared Team Dashboard

**Structure:**
```
~/Documents/claude space/ACCOUNTS/

2024_Q1_Pipeline/
├── Sarah_Accounts/
│   ├── Acme Corp/
│   ├── TechCorp/
│   └── GlobalBank/
│
├── Mike_Accounts/
│   ├── Enterprise1/
│   ├── Enterprise2/
│   └── Startup1/
│
└── Lisa_Accounts/
    ├── Fintech1/
    ├── Fintech2/
    └── Fintech3/
```

**How it Works:**
```
Team Meeting:

1. Each rep can use JARVIS on their accounts
   Sarah: @jarvis-mcp get_risk_report account=Acme Corp
   
2. Manager can review all risks
   @jarvis-mcp quick_insights account=Acme Corp
   @jarvis-mcp quick_insights account=TechCorp
   @jarvis-mcp quick_insights account=GlobalBank
   
3. See pipeline health across team
   High risk: Acme Corp (needs attention)
   On track: TechCorp (good progress)
   Early: GlobalBank (just starting)
```

### Real-Time Pipeline Visibility

Ask Claude:
```
Claude, give me a dashboard of my Q1 pipeline with:
1. All account stages
2. Win probability for each
3. Risks by account
4. Timeline status
5. What needs attention
```

Claude auto-compiles from all your accounts.

---

## How Data Flows

```
You Create Account:
└─ Folder: ~/Documents/claude space/ACCOUNTS/MyAccount/
   ├─ company_research.md   (You write)
   ├─ discovery.md          (You write)
   └─ deal_stage.json       (You write)

When You Ask JARVIS:
└─ @jarvis-mcp get_proposal account=MyAccount
   ├─ Reads all 3 input files
   ├─ Sends to NVIDIA AI
   ├─ Gets intelligent response
   ├─ Saves as: proposal.md
   └─ Returns to you

On Next Use:
└─ @jarvis-mcp get_battlecard account=MyAccount
   ├─ Reads proposal.md (context!)
   ├─ Reads other files
   ├─ Generates battlecard.md
   └─ Each generation gets smarter

Preferences Track:
└─ ~/.claude/preferences.json
   ├─ Tracks what you use
   ├─ Learns what works
   ├─ Optimizes next time
   └─ Personalized to you
```

---

## Data Organization Best Practices

### For Individual Reps
```
~/Documents/claude space/ACCOUNTS/
├── 2024_Q1/
│   ├── Acme Corp/
│   ├── TechCorp/
│   └── GlobalBank/
├── 2024_Q2/
│   └── ...
└── Pipeline/
    ├── Hot Leads/
    │   └── ...
    └── Prospects/
        └── ...
```

### For Teams
```
~/Documents/claude space/ACCOUNTS/
├── AE_Team/
│   ├── Sarah/
│   ├── Mike/
│   └── Lisa/
├── Presales/
│   ├── John/
│   └── Maria/
└── Shared_Accounts/
    ├── Enterprise/
    └── Strategic/
```

### For Complex Organizations
```
~/Documents/claude space/ACCOUNTS/
├── By_Region/
│   ├── North_America/
│   │   ├── East_Coast/
│   │   │   └── Accounts/
│   │   └── West_Coast/
│   │       └── Accounts/
│   ├── EMEA/
│   └── APAC/
├── By_Segment/
│   ├── Enterprise/
│   ├── Mid_Market/
│   └── SMB/
└── By_Stage/
    ├── Pipeline/
    ├── Negotiation/
    └── Closed_Won/
```

**JARVIS auto-finds accounts at any nesting level.**

---

## Going Further

### 1. Auto-Update Deal Data
When you update `discovery.md`, JARVIS auto-regenerates:
- risk_report.md
- value_architecture.md
- demo_strategy.md
- proposal.md

**Just edit discovery.md and everything updates.**

### 2. Team Forecasting
```
Manager asks:
"Show me all deals at risk"

JARVIS reads all risk_reports.md
Returns: List of deals needing attention
```

### 3. Knowledge Base
```
Over time, JARVIS learns:
- What proposals work best
- Which messaging resonates
- Optimal deal structures
- Common objection patterns

Results: Better deals faster
```

### 4. Competitive Intelligence
```
@jarvis-mcp get_competitive_intelligence

JARVIS learns:
- Your competitors' strategies
- Market positioning
- Pricing patterns
- Your advantages

Results: Better positioning
```

---

## Summary: How This Helps Sales/Presales

**Before JARVIS:**
- Manually write proposals (hours)
- Create battlecards from memory
- Build ROI models from scratch
- No visibility into risks
- Manual follow-ups

**With JARVIS:**
- ✅ Proposals in minutes (auto-generated)
- ✅ Battlecards instant (auto-generated)
- ✅ ROI models automatic (auto-generated)
- ✅ Risk visibility real-time (auto-analyzed)
- ✅ Follow-ups instant (auto-generated)
- ✅ All learned and optimized over time

**Time saved:** 10-15 hours/week per rep

**Quality improved:** Data-driven, consistent, intelligent

**Results:** Higher win rates, faster closes, bigger deals

---

## Getting Started with Advanced Features

1. **Set up nested folders** (organize your way)
2. **Update .env once** with your NVIDIA key
3. **Start using** @jarvis-mcp in your daily workflow
4. **Watch preferences auto-save** to ~/.claude/preferences.json
5. **Get smarter results** as JARVIS learns

**That's it.**

Everything else is automatic.

