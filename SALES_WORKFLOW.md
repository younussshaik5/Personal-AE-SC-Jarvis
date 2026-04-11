# JARVIS Sales Workflow — From Download to First Skill

> **Complete guide for sales people. Non-technical. Works on Windows, Mac, Linux.**

---

## 🎯 Day 1: Setup (One-Time, 5 Minutes)

### Step 1: Download JARVIS

1. Go to: **https://github.com/younussshaik5/Personal-AE-SC-Jarvis**
2. Click green **"Code"** button → **"Download ZIP"**
3. Extract the ZIP file to your Desktop or Documents folder

### Step 2: Open in Claude Code

Option A (Claude Code):
- Open Claude Code app
- Click **"Open Folder"**
- Select the JARVIS folder you just extracted
- Claude will detect it's a JARVIS project

Option B (VS Code with Claude Extension):
- Open the JARVIS folder in VS Code
- Claude extension should recognize JARVIS
- Open Claude chat within VS Code

Option C (Claude Desktop):
- Skip this setup
- JARVIS runs in the background
- Use Claude Desktop chat to work with JARVIS

### Step 3: Run Setup

In Claude, you'll see a message like:

```
🤖 JARVIS detected!
Missing API key. 

Run: python install.py

This will take 2-3 minutes and:
✓ Check Python
✓ Create virtual environment
✓ Install all dependencies
✓ Ask for NVIDIA API key
✓ Set up ACCOUNTS folder
✓ Configure Claude Desktop
```

In your terminal, run:
```
python install.py
```

When prompted:
1. **NVIDIA API Key** — Go to https://build.nvidia.com
   - Sign up (free, no credit card)
   - Copy your API key (starts with `nvapi-`)
   - Paste it when prompted

2. Wait 2-3 minutes for everything to install

3. When it says "✅ Setup Complete!" — you're done

### Step 4: Restart Claude

- **Claude Desktop**: Cmd+Q (Mac) or right-click → Quit (Windows), then reopen
- **Claude Code**: Close and reopen the folder

---

## 📊 Day 1-5: Your First Deal (5 Minutes Setup)

### Create Your First Account

In Claude, ask:

```
"Create account for Acme Corp.
They're a 500-person company evaluating us.
Primary contact: Sarah Chen, VP Operations.
ARR target: $180k.
Timeline: March deadline."
```

Claude will create: `~/JARVIS/ACCOUNTS/AcmeCorp/`

This folder contains:
- `deal_stage.json` — Deal state (stage, ARR, stakeholders)
- `discovery.md` — Your discovery notes
- `company_research.md` — Background research
- `CLAUDE.md` — Deal-specific configuration

### Open the Account Folder

1. In Claude, open the account folder: `~/JARVIS/ACCOUNTS/AcmeCorp/`
2. Claude automatically reads the deal files
3. Claude shows:

```
📌 ACME CORP — Deal Summary

Current Stage: Discovery
ARR Target: $180k
Health: AMBER (watch closely)

Key Pain: Consolidate 5 customer service systems
Champion: Sarah Chen, VP Operations
Competitor: Freshdesk

MEDDPICC Status:
  ✓ Metrics: Not yet
  ✓ Economic Buyer: Not engaged
  ✓ Decision Criteria: Partial
  ✓ Decision Process: Partial
  ✗ Paper Process: Not started
  ✓ Implications: Confirmed
  ✓ Champion: Identified
  ✓ Competition: Identified

Next Action: Run MEDDPICC scoring to close gaps
```

---

## 🎬 Day 2+: Running Skills

### After a Discovery Call

Paste your call notes:

```
"Update AcmeCorp: Sarah confirmed budget $150-200k.
Timeline is hard Q3 (contract ends June 30).
Pain: agents switch between 5 systems daily (40% wasted time).
Mike Torres (IT Director) is champion.
Also evaluating Freshdesk and Zendesk.
Next demo with CFO in 2 weeks."
```

Claude automatically:
1. **Extracts intelligence** (MEDDPICC signals found)
2. **Updates discovery.md**
3. **Suggests next action**: "Run MEDDPICC scoring to update deal state"

### Running Skills

Ask Claude for what you need:

#### Deal Analysis (30 sec)
```
"Score MEDDPICC for AcmeCorp"
```
Returns:
- All 8 dimensions scored RED/AMBER/GREEN
- Evidence for each
- Biggest gaps

#### Meeting Prep (15 sec)
```
"Meeting prep for AcmeCorp — I'm meeting with Sarah and Mike tomorrow"
```
Returns:
- Who's attending and what they care about
- Discovery questions to ask
- Objection handlers
- Hard ask recommendation

#### Competitive Prep (15 sec)
```
"Battlecard vs Freshdesk for AcmeCorp"
```
Returns:
- What Freshdesk does well
- Where you have edge
- Killer questions to expose their weakness

#### Proposal (20 sec)
```
"Proposal for AcmeCorp"
```
Returns:
- Executive summary (grounded in their pain)
- Your solution vs their requirements
- Pricing and ROI
- Competitive positioning

#### Deal Health (10 sec)
```
"Risk report for AcmeCorp"
```
Returns:
- Overall health: RED/AMBER/GREEN
- What's blocking them
- What could kill the deal
- Recommended next steps

---

## 📁 Your Folder Structure

After setup, you'll have:

```
~/JARVIS/
├── .env                          ← API keys (created by install.py)
├── install.py                    ← Setup script (run once)
├── README.md                     ← Full documentation
├── jarvis_mcp_launcher.py        ← Runs in background
└── ACCOUNTS/                     ← Your deals
    ├── AcmeCorp/
    │   ├── deal_stage.json       ← Deal state (stage, ARR, timeline)
    │   ├── discovery.md          ← Your discovery notes
    │   ├── company_research.md   ← Company background
    │   ├── CLAUDE.md             ← Deal-specific config
    │   ├── meddpicc.md           ← Auto-generated MEDDPICC score
    │   ├── battlecard.md         ← Auto-generated battlecard
    │   ├── risk_report.md        ← Auto-generated risk report
    │   └── proposal.md           ← Auto-generated proposal
    │
    ├── RetailCo/
    │   ├── deal_stage.json
    │   ├── discovery.md
    │   └── ...
    │
    └── TechCorp/
        └── ...
```

All files are **local** (on your computer). Nothing uploaded to cloud.

---

## 🧠 Smart Context Detection

### Project Level
When you open the main JARVIS folder in Claude:
- Claude checks if setup is complete
- Lists all active deals
- Shows pipeline health
- Suggests which deals need attention

### Account Level
When you open `ACCOUNTS/[AccountName]/` in Claude:
- Claude reads the deal files
- Shows current deal state
- Suggests most relevant skills
- Tracks MEDDPICC progress

### Folder Updates
When you **paste notes** or **open a meeting transcript**:
- Claude extracts MEDDPICC signals
- Updates discovery.md automatically
- Suggests next action

---

## ⚡ Quick Reference

| You Say | Claude Does |
|---------|-------------|
| "Create account AcmeCorp..." | Creates account folder with templates |
| "Update AcmeCorp: [notes]" | Extracts signals, updates discovery |
| "Score MEDDPICC for AcmeCorp" | Generates MEDDPICC breakdown |
| "Meeting prep for AcmeCorp" | Creates meeting brief |
| "Battlecard vs Salesforce" | Competitive positioning |
| "Proposal for AcmeCorp" | Sales proposal |
| "Risk report for AcmeCorp" | Deal health assessment |
| "What's my pipeline?" | Summary of all deals |

---

## 🔑 API Key Management

### Getting Keys

1. Go to: https://build.nvidia.com
2. Sign up (free tier, no credit card)
3. Profile → API Keys → Generate Key
4. Copy key (starts with `nvapi-`)

### Adding More Keys

If you get rate-limited, add more keys to `.env`:

```
NVIDIA_API_KEY=nvapi-key1
NVIDIA_API_KEY_2=nvapi-key2
NVIDIA_API_KEY_3=nvapi-key3
```

JARVIS rotates between them automatically.

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Download Python from python.org |
| "API key error" | Check `.env` has `NVIDIA_API_KEY=nvapi-...` |
| "Account not found" | Make sure account folder exists in `~/JARVIS/ACCOUNTS/` |
| "Skills don't work" | Restart Claude Desktop, restart Claude Code |
| "Rate limited" | Add more API keys to `.env` |

---

## 📈 Typical Deal Workflow

### Day 1: New Lead
```
"Create account for Acme Corp..."
→ Folder created with templates
```

### Day 2: After Discovery
```
"Update AcmeCorp: [call notes]"
→ Claude extracts signals, updates discovery
→ "Run MEDDPICC scoring next"
```

### Day 3: Before Next Call
```
"Meeting prep for AcmeCorp"
→ Brief created with discovery questions
```

### Day 4: Demo Ready
```
"Demo strategy for AcmeCorp"
→ Demo flow tailored to their pain
```

### Day 5: Competitor Alert
```
"Battlecard vs Freshdesk"
→ Competitive positioning
```

### Day 7: Closing
```
"Proposal for AcmeCorp"
→ Sales proposal with ROI
```

---

## 🎓 Best Practices

1. **Update discovery.md after every call** — Keep notes fresh
2. **Check deal_stage.json weekly** — Keep status current
3. **Run MEDDPICC monthly** — See progress on gaps
4. **Use meeting prep before every call** — Prepare with intelligence
5. **Check risk report before big calls** — Know what could kill the deal

---

## 📞 Getting Help

- **README.md** — Full technical documentation
- **FINAL_DELIVERY.md** — What JARVIS does
- **COMPLETION_SUMMARY.md** — Features and capabilities
- **GitHub Issues** — Report problems

---

## 🚀 That's It!

You're ready. One sales person. One command. Full deal intelligence.

**Remember:**
- All files stay on your machine
- All skills work offline (except LLM API calls)
- Everything is encrypted (your API key stays in `.env`)
- No sales data uploaded anywhere

You own your deals. JARVIS just helps you work faster.

---

**Setup Time:** 5 minutes  
**First skill run:** 30 seconds  
**Time saved per week:** 5-8 hours  
**ROI:** Immediate  

**Questions?** Read README.md or ask Claude — it's here to help.
