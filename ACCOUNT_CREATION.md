# Account Creation Workflow

**Zero manual setup. Just mention a company name.**

## Simple Account Creation

### The User Says:
```
I'm working on Tata
```

### Claude Does:
1. Detects "Tata" as a potential new account
2. Checks if it exists (it doesn't)
3. Asks for confirmation:
   ```
   Should I create a Tata account?
   - Revenue: (optional) 
   - Industry: (optional)
   ```

### User Confirms:
```
Yes, create it
```

### Claude Creates:
- ✓ Folder: `~/ACCOUNTS/Tata/`
- ✓ `deal_stage.json` - Deal metrics template
- ✓ `company_research.md` - Research notes template  
- ✓ `discovery.md` - Discovery call notes
- ✓ `CLAUDE.md` - Account settings
- ✓ `dashboard.html` - CRM dashboard

**That's it.** No manual folder creation. No manual file editing. Everything is scaffolded.

---

## Sub-Account Creation

### The User Says:
```
Create TataTele under Tata (telecom division)
```

### Claude Does:
1. Detects "TataTele" with parent "Tata"
2. Asks:
   ```
   Create TataTele as sub-account of Tata?
   - TataTele will inherit Tata's company_research.md
   - TataTele will have its own deal_stage.json, discovery.md
   - Industry: (optional)
   ```

### User Confirms:
```
Yes
```

### Claude Creates:
- ✓ Folder: `~/ACCOUNTS/Tata/TataTele/`
- ✓ `deal_stage.json` (own)
- ✓ `discovery.md` (own)
- ✓ `CLAUDE.md` (own)
- ✓ **Inherits**: `company_research.md` from Tata

**Hierarchy created.** Child shares parent's research, maintains own metrics.

---

## What Gets Created

### deal_stage.json
```json
{
  "account_name": "Tata Corporation",
  "stage": "Initial Contact",
  "probability": 0,
  "deal_size": 0,
  "timeline": "TBD",
  "stakeholders": [],
  "activities": [],
  "next_milestone": {
    "date": "TBD",
    "activity": "To be determined",
    "description": "Set after first discovery call"
  },
  "competitive_situation": {
    "primary_competitor": "TBD",
    "competitor_status": "Unknown",
    "our_price": "TBD",
    "win_probability_vs_competitor": 0
  },
  "constraints": [],
  "last_updated": "2025-04-01T..."
}
```

**You fill this in** as the deal progresses:
- Update `stage` after discovery calls
- Update `probability` after demos/meetings
- Add `stakeholders` as you meet them
- Track `activities` and `constraints`

### company_research.md
```markdown
# Tata - Company Research

## Overview
- **Name**: Tata Corporation
- **Industry**: Conglomerate
- **HQ**: Mumbai, India
- **Size**: 50,000+ employees

## Key Facts
(Add your research here)

## Market Position
(Your analysis)

## Relevant Competitors
(Who they compete with)
```

**Parent creates this.** Children inherit and reference it.

### discovery.md
```markdown
# Tata - Discovery Notes

## Call 1: Initial Discovery
- **Date**: TBD
- **Attendees**: TBD
- **Goals**: Understand their pain points
- **Key Findings**: (Add notes)

## Budget & Timeline
- Budget: TBD
- Timeline: TBD
- Approval Process: TBD

## Pain Points
1. (Add as discovered)
2. (Add as discovered)

## Success Criteria
(What would winning look like)
```

**Each account maintains its own.** Updated after discovery calls.

### CLAUDE.md
```markdown
# Tata - Account Settings

## Cascade Rules
- Inherit company research from parent: yes
- Inherit skill preferences: yes
- Override global settings: none

## Model Preferences
- Reasoning (discovery, analysis): Sonnet
- Fast responses (summaries): Haiku  
- Complex tasks (proposals): Opus

## Skill Preferences
- Auto-enable: discovery, battlecard
- Suggest: proposal, demo_strategy
- Hide: none

## Notes
- Key stakeholder: VP of Strategy
- Budget cycle: Q2
- Competitive threat: Oracle
```

**Auto-generated, can be edited.** Controls which skills are recommended.

### dashboard.html
```html
Acme Corporation - CRM Dashboard

┌─────────────────────────────────┐
│ DEAL STAGE: Initial Contact     │
│ PROBABILITY: 0%                 │
│ DEAL SIZE: $0                   │
│ TIMELINE: TBD                   │
├─────────────────────────────────┤
│ STAKEHOLDERS: 0                 │
│ NEXT MILESTONE: TBD             │
│ LAST ACTIVITY: Never            │
│ DAYS IN STAGE: 0                │
├─────────────────────────────────┤
│ COMPETITIVE: Unknown            │
│ OUR PRICE: TBD                  │
│ WIN PROBABILITY: 0%             │
└─────────────────────────────────┘
```

**Auto-generated.** Open in browser. Updates as deal_stage.json changes.

---

## Workflow Example: Tata Telco Deal

### Day 1: Account Creation
```
User: "I'm starting work on Tata's telecom division (TataTele)"
Claude: "Create TataTele under Tata? (Telecom industry)"
User: "Yes"
Result: TataTele account created, inherits Tata research
```

### Day 2: Discovery Call
```
User: "I just had discovery call with Tata's CTO. Here's what I learned:"
Claude: "Should I update discovery.md for TataTele?"
User: "Yes. They want to consolidate 3 vendors. Budget is $5M, decision in Q2."
Result: discovery.md updated, CLAUDE.md suggests next skill = battlecard
```

### Day 3: Competitive Analysis
```
User: "@jarvis battlecard"
Claude: "Using TataTele's context:
- Company: Tata Telecom
- Budget: $5M
- Timeline: Q2
- Stakeholders: CTO
→ Generating battlecard vs Oracle, SAP..."
Result: Battlecard generated with TataTele's specific context
```

### Day 5: Proposal Generation
```
User: "@jarvis proposal"
Claude: "Generating SOW for TataTele:
- Loads: TataTele's deal_stage.json (metrics)
- Loads: Tata's company_research.md (shared research)
- Loads: TataTele's discovery.md (call notes)
→ Generating professional SOW..."
Result: SOW ready for editing, auto-populated with real data
```

### Week 2: Progress Tracking
```
User: Opens ~/ACCOUNTS/Tata/TataTele/dashboard.html
Result: See deal progress, next milestones, competitive status
```

---

## Multiple Accounts Example

```
ACCOUNTS/
├── Tata/
│   ├── company_research.md (shared)
│   ├── deal_stage.json ($10M, Q2)
│   ├── TataTele/
│   │   ├── deal_stage.json ($5M, Q2) ← OWN
│   │   ├── discovery.md ← OWN
│   │   └── CLAUDE.md ← OWN
│   ├── TataSky/
│   │   ├── deal_stage.json ($3M, Q3) ← OWN
│   │   ├── discovery.md ← OWN
│   │   └── CLAUDE.md ← OWN
│   └── TataTV/
│       ├── deal_stage.json ($2M, Q4) ← OWN
│       ├── discovery.md ← OWN
│       └── CLAUDE.md ← OWN
│
├── Acme/
│   ├── company_research.md (shared)
│   ├── deal_stage.json ($8M, Q1)
│   ├── AcmeEdu/
│   │   ├── deal_stage.json ($4M, Q1) ← OWN
│   │   └── discovery.md ← OWN
│   └── AcmeSaaS/
│       ├── deal_stage.json ($4M, Q2) ← OWN
│       └── discovery.md ← OWN
```

**One research doc (Tata's), one research doc (Acme's). Multiple deals tracked separately.**

---

## Key Principles

1. **No Manual Work**: Everything is scaffolded automatically
2. **Minimal Questions**: Only ask for required info (company name)
3. **Smart Inference**: Auto-detect relationships (TataTele → child of Tata)
4. **Inheritance**: Children inherit parent's research, own their metrics
5. **Context Awareness**: Claude loads relevant files based on current folder
6. **Self-Updating**: CLAUDE.md learns what skills you use, suggests improvements

---

## Pro Tips

### Create Parent Only
```
User: "Create Tata"
Result: Parent account with research & metrics
```

### Create Multiple Children at Once
```
User: "Create TataTele, TataSky, TataTV all under Tata"
Result: All three created with parent inheritance
```

### Auto-Detect Existing Account
```
cd ~/ACCOUNTS/Tata/TataTele
User: "What's our deal status?"
Claude: Auto-loads TataTele's context (no explicit account needed)
```

### View All Accounts
```
User: "@jarvis list accounts"
Result: Shows all Tata divisions with deal sizes and stages
```

---

**That's it. Simple. Fast. No manual overhead.**
