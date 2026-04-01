# JARVIS MCP - Quick Start Guide

**Get up and running in 5 minutes.**

---

## What You'll Have

- ✅ AI sales assistant integrated with Claude Code
- ✅ 24 ready-to-use sales skills
- ✅ 3 example accounts (learn by doing)
- ✅ Auto-learning preferences system
- ✅ Full documentation and examples

---

## Step-by-Step (5 Minutes)

### Step 1: Clone (30 seconds)
```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

### Step 2: Auto-Setup (2 minutes)
```bash
bash setup_auto.sh
```

**What happens automatically:**
- Creates virtual environment
- Installs all dependencies
- Sets up account folders
- Copies 3 example accounts (AcmeCorp, TechStartup, GlobalBank)
- Creates .env file
- Runs tests to verify everything works

Just wait for it to finish.

### Step 3: Add NVIDIA Key (30 seconds)
```bash
nano .env
```

Find this line:
```
NVIDIA_API_KEY=
```

Add your key:
```
NVIDIA_API_KEY=sk-your-actual-nvidia-key-here
```

Save (Ctrl+O, Enter, Ctrl+X in nano)

### Step 4: Configure Claude Code (1 minute)

Open Claude Code settings file:
```
~/.claude/settings.json
```

Add this to `mcpServers` section:
```json
"jarvis": {
  "command": "python",
  "args": ["-m", "jarvis_mcp.mcp_server"],
  "env": {
    "NVIDIA_API_KEY": "your_key_here"
  }
}
```

Restart Claude Code.

### Done! ✨

You're ready to use JARVIS.

---

## Your First Use (1 minute)

### Open Claude Code
Start a conversation with Claude.

### Ask Claude
```
@jarvis-mcp get_proposal account=AcmeCorp
```

### Claude returns
A professional sales proposal for AcmeCorp based on:
- Their company info
- What you learned in discovery
- Their current deal stage

All automatic. All intelligent.

---

## Try These Immediately

```
# Get a proposal
@jarvis-mcp get_proposal account=AcmeCorp

# Get competitive positioning
@jarvis-mcp get_battlecard account=AcmeCorp competitor=ServiceCo

# Create demo strategy
@jarvis-mcp get_demo_strategy account=AcmeCorp

# Assess deal risks
@jarvis-mcp get_risk_report account=AcmeCorp

# Build ROI model
@jarvis-mcp get_value_architecture account=AcmeCorp
```

Each command:
- Reads your account data
- Generates professional content
- Saves to account folder
- Shows you the result

---

## Your Accounts

Example accounts are in:
```
~/Documents/claude space/ACCOUNTS/
├── AcmeCorp/           (ready to use)
├── TechStartup/        (ready to use)
└── GlobalBank/         (ready to use)
```

Each has:
```
company_research.md    (company info)
discovery.md           (discovery notes)
deal_stage.json        (stage, probability, timeline)
```

Edit these files with your own data and JARVIS adapts.

---

## Add Your Own Account (2 minutes)

### Create folder
```bash
mkdir ~/Documents/claude\ space/ACCOUNTS/YourCompanyName
```

### Create company_research.md
```bash
cat > ~/Documents/claude\ space/ACCOUNTS/YourCompanyName/company_research.md << 'EOF'
# Your Company Name

## Overview
- Founded: YYYY
- Employees: XXX
- Revenue: $XXM

## Tech Stack
- Cloud: AWS/GCP/Azure
- Languages: Python/Java/Node
- Key systems: list

## Pain Points
- Issue 1
- Issue 2
- Issue 3

## Competitive Landscape
- Main competitors
- Their advantages
- Our differentiation
EOF
```

### Create discovery.md
```bash
cat > ~/Documents/claude\ space/ACCOUNTS/YourCompanyName/discovery.md << 'EOF'
# Discovery Notes

## MEDDPICC Assessment

### Metrics
- What do they want to achieve
- Quantified impact

### Economic Buyer
- Who controls budget
- Approval process

### Decision Criteria
- What matters to them
- How they evaluate

### Budget
- Amount available
- Timeline
- Constraints

### Other Notes
- Key insights
- Next steps
- Stakeholders
EOF
```

### Create deal_stage.json
```bash
cat > ~/Documents/claude\ space/ACCOUNTS/YourCompanyName/deal_stage.json << 'EOF'
{
  "stage": "Discovery",
  "probability": 50,
  "deal_size": 500000,
  "timeline": "Q3 2026",
  "stakeholders": ["CTO", "VP Sales"]
}
EOF
```

### Start Using
```
@jarvis-mcp get_proposal account=YourCompanyName
```

JARVIS reads your files and generates everything automatically.

---

## How It All Works

```
You write:
@jarvis-mcp get_proposal account=AcmeCorp

JARVIS does this:
1. Finds ~/Documents/claude space/ACCOUNTS/AcmeCorp/
2. Reads company_research.md (your company info)
3. Reads discovery.md (what you learned)
4. Reads deal_stage.json (current progress)
5. Sends to NVIDIA AI with smart prompt
6. Gets back generated content
7. Saves to ~/Documents/claude space/ACCOUNTS/AcmeCorp/proposal.md
8. Shows you the result in Claude Code

All automatic.
```

---

## Self-Learning Preferences

Every time you use JARVIS, it learns:

**What it tracks:**
- Which skills you use most
- Your favorite accounts
- What AI models work best for you
- Your content preferences
- Your company terminology

**Where it stores:**
```
~/.claude/preferences.json
```

**What it improves:**
- Next time you use same skill → better results
- Faster execution
- More relevant content
- Personalized to your style

**You don't configure.** It learns automatically.

---

## Troubleshooting (2 minutes)

### "NVIDIA_API_KEY not set"
```bash
# Check .env file
cat .env | grep NVIDIA_API_KEY

# If empty, edit:
nano .env
# Add your key
```

### "Account not found"
```bash
# Check account folder exists
ls ~/Documents/claude\ space/ACCOUNTS/YourAccountName/

# Check required files
ls ~/Documents/claude\ space/ACCOUNTS/YourAccountName/company_research.md
ls ~/Documents/claude\ space/ACCOUNTS/YourAccountName/discovery.md
ls ~/Documents/claude\ space/ACCOUNTS/YourAccountName/deal_stage.json
```

### "Skills not showing"
```bash
# Restart Claude Code (full restart)
# Then try again
@jarvis-mcp get_proposal account=AcmeCorp
```

### "Tests failing"
```bash
# Reinstall
make clean
pip install -e ".[dev]"
make test
```

---

## What's Next?

### 1. Play with Examples
Use the 3 example accounts to see what JARVIS can do.

### 2. Add Your Accounts
Create account folders for your real deals.

### 3. Customize
Edit the discovery and company research files with real data.

### 4. Watch JARVIS Learn
Over time, it learns your preferences and improves.

### 5. Explore All 24 Skills
Try different skills to see what works best for your team.

---

## All 24 Skills (Quick Reference)

**By Category:**

**Proposals & Positioning (5)**
- `get_proposal` - Sales proposal
- `get_battlecard` - Competitive positioning
- `get_demo_strategy` - Demo narrative
- `get_risk_report` - Deal risk assessment
- `get_value_architecture` - ROI/TCO model

**Discovery & Intelligence (5)**
- `get_discovery` - Discovery prep/notes
- `get_competitive_intelligence` - Competitor research
- `get_meeting_prep` - Meeting preparation
- `process_meeting` - Call transcript analysis
- `summarize_conversation` - Conversation analysis

**Deal Management (5)**
- `track_meddpicc` - MEDDPICC tracking
- `update_deal_stage` - Stage management
- `generate_sow` - Scope of Work
- `generate_followup` - Follow-up email
- `get_account_summary` - Account overview

**Technical & Advanced (9)**
- `assess_technical_risk` - Tech risk assessment
- `analyze_competitor_pricing` - Pricing analysis
- `generate_architecture` - Architecture diagram
- `generate_documentation` - Tech documentation
- `generate_html_report` - HTML reports
- `extract_intelligence` - Text intelligence extraction
- `build_knowledge_graph` - Knowledge graph creation
- `quick_insights` - Quick deal insights
- `generate_custom_template` - Custom templates

---

## Key Features

✅ **Zero Configuration**
- Clone, run setup, add API key
- Everything else is automatic

✅ **Self-Learning**
- Learns from your usage
- Improves over time
- Personalizes to you

✅ **Fully Automated**
- Reads account files automatically
- Generates content automatically
- Saves results automatically
- Adjusts models automatically

✅ **Works for Everyone**
- Sales reps
- Presales engineers
- Sales managers
- Solo entrepreneurs
- Enterprise teams

✅ **Production Ready**
- Full test suite
- Professional code
- Enterprise-grade
- Extensible architecture

---

## Support & Documentation

**Need more details?**
- `README.md` - Quick reference
- `README_COMPLETE.md` - Full guide with examples
- `CONTRIBUTING.md` - How to add skills

**Questions?**
Check README_COMPLETE.md - it has everything.

---

## You're Ready!

That's it. You have everything you need.

1. ✅ Cloned the repo
2. ✅ Ran setup script
3. ✅ Added NVIDIA key
4. ✅ Configured Claude Code
5. ✅ Ready to use

**Start with:**
```
@jarvis-mcp get_proposal account=AcmeCorp
```

Then explore the other 23 skills.

---

**Happy selling! 🚀**

