# JARVIS MCP - Complete Guide

**The AI Sales Intelligence Platform for Any Sales Team**

---

## What Is JARVIS MCP?

JARVIS is an **AI-powered sales assistant** that lives in Claude Code and helps you with:

- 📝 **Proposals** - Generate compelling sales proposals
- ⚔️ **Battlecards** - Competitive positioning & objection handling
- 🎬 **Demo Strategy** - Design winning demo narratives
- 📊 **Risk Analysis** - Assess deal risks and gaps
- 💰 **ROI Models** - Build business cases and value analyses
- 🔍 **Discovery** - Manage discovery calls and prep
- 🏆 **Deal Management** - Track MEDDPICC, stages, SOW, follow-ups
- 🤖 **Intelligence** - Extract insights, analyze conversations, competitive research
- **+ 16 more specialized skills**

**In plain English:** It's like having an expert sales consultant who understands your accounts, reads your discovery notes, and automatically generates everything you need to win deals.

---

## Quick Start (3 Steps)

### 1️⃣ Clone
```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

### 2️⃣ Auto-Setup
```bash
bash setup_auto.sh
```
This automatically:
- ✅ Creates Python virtual environment
- ✅ Installs all dependencies
- ✅ Creates `.env` file
- ✅ Sets up account folders
- ✅ Copies example accounts
- ✅ Runs tests to verify

### 3️⃣ Add Your Nvidia Key
```bash
# Edit .env file and add your NVIDIA_API_KEY
nano .env

# Find this line and add your key:
# NVIDIA_API_KEY=your_key_here
```

**That's it!** ✨

---

## How It Works (Complete Explanation)

### The Concept

JARVIS works with **accounts** and **files**:

```
Your account (e.g., "Acme Corp")
    ├── company_research.md    ← Company info, tech stack, pain points
    ├── discovery.md           ← MEDDPICC notes from discovery calls
    ├── deal_stage.json        ← Current stage, probability, timeline
    ├── proposal.md            ← Generated proposal (auto-created)
    ├── battlecard.md          ← Generated battlecard (auto-created)
    ├── demo_strategy.md       ← Generated demo narrative (auto-created)
    └── ... (other generated files)
```

When you ask JARVIS something like:
```
@jarvis-mcp get_proposal account=Acme Corp
```

JARVIS does this automatically:
1. Reads `company_research.md` (company info)
2. Reads `discovery.md` (what you learned)
3. Reads `deal_stage.json` (where you are)
4. Creates a prompt using all that context
5. Sends to NVIDIA AI for intelligent generation
6. Creates/updates `proposal.md` with the result
7. Returns the content to Claude Code

### Self-Setup & Auto-Load

**Everything auto-loads.** Once you:
1. Clone the repo ✓
2. Run `setup_auto.sh` ✓
3. Add NVIDIA key ✓

JARVIS automatically:
- ✅ Detects your accounts folder (`~/Documents/claude space/ACCOUNTS/`)
- ✅ Loads example accounts (AcmeCorp, TechStartup, GlobalBank)
- ✅ Configures the environment
- ✅ Loads all 24 skills
- ✅ Ready to use with zero additional configuration

**No manual setup required.** It just works.

### Preferences & Self-Learning

JARVIS learns from your usage by updating these files:

```
.claude/
├── CLAUDE.md              ← Config (routing, preferences)
├── workspace.md           ← Your workspace settings
└── settings.json          ← Claude Code settings
```

When you use JARVIS:
- **First time:** Uses default models and settings
- **After each use:** Stores preferences for next time
- **Over time:** Learns which models work best for your deals
- **Automatically:** Adjusts based on your success patterns

**You don't need to configure anything.** JARVIS learns from your actual usage.

---

## Using JARVIS in Claude Code Coworks

### Setup (One Time)

1. **In Claude Code settings** (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python",
      "args": ["-m", "jarvis_mcp.mcp_server"],
      "env": {
        "NVIDIA_API_KEY": "your_nvidia_api_key_here"
      }
    }
  }
}
```

2. **Restart Claude Code**

3. **Start using!**

### How to Use (Daily)

In any Claude Code conversation, just use the skills:

```
@jarvis-mcp get_proposal account=Acme Corp
```

Returns:
```
# Acme Corp Sales Proposal

[Generated proposal based on their company info + discovery]
```

Or ask Claude to use JARVIS:

```
Claude, use @jarvis-mcp to:
1. Get a proposal for Acme Corp
2. Generate a battlecard vs ServiceCo
3. Create a demo strategy for the CTO
```

Claude will automatically call JARVIS for each and compile everything.

---

## Can Any Sales/Presales Person Use It?

**YES.** Absolutely anyone can use it:

- ✅ **Sales Reps** - Generate proposals, battlecards, follow-ups
- ✅ **Presales** - Demo strategies, technical risk assessments, SOW
- ✅ **Sales Managers** - Risk reports, deal stage tracking, pipeline analysis
- ✅ **Account Executives** - Everything - it's built for you
- ✅ **Sales Engineers** - Architecture diagrams, technical docs, implementation plans
- ✅ **Anyone with Claude Code** - Just clone and run

No special training needed. If you can use Claude, you can use JARVIS.

---

## How New Folders Work

### Scenario 1: Adding a New Account

**You want to add "Microsoft" as a new account.**

#### Option A: Manual (Fastest)
```bash
mkdir -p ~/Documents/claude\ space/ACCOUNTS/Microsoft
```

Then create three files:

```bash
# 1. Company research
cat > ~/Documents/claude\ space/ACCOUNTS/Microsoft/company_research.md << 'EOF'
# Microsoft

## Overview
- Founded: 1975
- HQ: Redmond, Washington
- Revenue: $200B+

## Pain Points
- Data integration
- Cloud migration
- AI implementation
EOF

# 2. Discovery notes
cat > ~/Documents/claude\ space/ACCOUNTS/Microsoft/discovery.md << 'EOF'
# Discovery Notes

## MEDDPICC
- Metrics: 50% cost reduction
- Economic Buyer: CFO
- Timeline: Q2 2026

## Notes
- Met with IT Director
- Budget available
EOF

# 3. Deal stage
cat > ~/Documents/claude\ space/ACCOUNTS/Microsoft/deal_stage.json << 'EOF'
{
  "stage": "Discovery",
  "probability": 60,
  "deal_size": 5000000,
  "timeline": "Q2 2026"
}
EOF
```

#### Option B: Automatic (Copy from Example)
```bash
# Copy AcmeCorp structure and edit
cp -r ~/Documents/claude\ space/ACCOUNTS/AcmeCorp ~/Documents/claude\ space/ACCOUNTS/Microsoft

# Then edit the files:
nano ~/Documents/claude\ space/ACCOUNTS/Microsoft/company_research.md
nano ~/Documents/claude\ space/ACCOUNTS/Microsoft/discovery.md
nano ~/Documents/claude\ space/ACCOUNTS/Microsoft/deal_stage.json
```

#### Now Use It
```
@jarvis-mcp get_proposal account=Microsoft
```

JARVIS automatically:
- ✅ Finds the Microsoft folder
- ✅ Reads company_research.md
- ✅ Reads discovery.md
- ✅ Reads deal_stage.json
- ✅ Generates proposal
- ✅ Saves to Microsoft/proposal.md

### Scenario 2: Using JARVIS in a Different Project Folder

**You're working on a different project and want to use JARVIS there.**

```bash
# Go to your project
cd ~/my-sales-project

# Use JARVIS via Claude Code (it's global)
@jarvis-mcp get_proposal account=Acme Corp
```

JARVIS still reads from:
```
~/Documents/claude space/ACCOUNTS/Acme Corp/
```

**Important:** Account folders are centralized in one location. All projects use the same accounts.

This way:
- ✅ All your sales data is in one place
- ✅ Easy to backup
- ✅ Easy to share with team
- ✅ Consistent across all projects

### Scenario 3: Auto-Population When You Create a Folder

When you clone JARVIS, example accounts are auto-copied:

```
~/Documents/claude space/ACCOUNTS/
├── AcmeCorp/           ← Auto-populated
│   ├── company_research.md
│   ├── discovery.md
│   └── deal_stage.json
├── TechStartup/        ← Auto-populated
│   ├── company_research.md
│   ├── discovery.md
│   └── deal_stage.json
└── GlobalBank/         ← Auto-populated
    ├── company_research.md
    ├── discovery.md
    └── deal_stage.json
```

**When you create a NEW account folder**, you just add these three files:
1. `company_research.md` (your company info)
2. `discovery.md` (your discovery notes)
3. `deal_stage.json` (current stage/probability)

Then JARVIS automatically generates all other files:
- `proposal.md`
- `battlecard.md`
- `demo_strategy.md`
- `risk_report.md`
- `value_architecture.md`
- etc.

**No need to create empty files.** JARVIS creates them on-demand.

---

## Complete Examples

### Example 1: First-Time Use

```bash
# Step 1: Clone
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis

# Step 2: Auto-setup
bash setup_auto.sh

# Step 3: Add your key
nano .env
# Add: NVIDIA_API_KEY=sk-...

# Step 4: Verify
make test
```

**Result:** JARVIS is ready. Example accounts are already set up.

### Example 2: Generate a Proposal for Acme Corp

```
In Claude Code:
@jarvis-mcp get_proposal account=AcmeCorp

Result:
✓ Reads company_research.md (company info)
✓ Reads discovery.md (what you learned)
✓ Reads deal_stage.json (current stage)
✓ Generates a professional proposal
✓ Saves to AcmeCorp/proposal.md
✓ Shows you the content
```

### Example 3: Complete Sales Workflow

```
You: Claude, help me prepare for the Acme Corp demo

Claude calls JARVIS:
1. @jarvis-mcp get_discovery account=AcmeCorp
   → Returns discovery insights

2. @jarvis-mcp get_demo_strategy account=AcmeCorp
   → Creates demo flow

3. @jarvis-mcp get_battlecard account=AcmeCorp
   → Competitive positioning

4. @jarvis-mcp get_risk_report account=AcmeCorp
   → Risk assessment

Claude compiles into:
✅ Discovery summary
✅ Demo talking points
✅ Competitive angles
✅ Risk mitigation

You're ready for the call!
```

### Example 4: Adding a New Account (TechCorp)

```bash
# Create folder
mkdir -p ~/Documents/claude\ space/ACCOUNTS/TechCorp

# Add company info
cat > ~/Documents/claude\ space/ACCOUNTS/TechCorp/company_research.md << 'EOF'
# TechCorp Inc.

## Overview
- Founded: 2015
- Employees: 200
- Revenue: $50M

## Tech Stack
- AWS
- Python/Go

## Pain Points
- Manual data processing
- Scaling challenges
EOF

# Add discovery notes
cat > ~/Documents/claude\ space/ACCOUNTS/TechCorp/discovery.md << 'EOF'
# Discovery Notes

## MEDDPICC
- Metrics: 40% efficiency gain
- Economic Buyer: CTO
- Budget: $300k
- Timeline: Q3 2026

## Call Notes
- Very technical buyer
- Wants proof of ROI
EOF

# Add deal stage
cat > ~/Documents/claude\ space/ACCOUNTS/TechCorp/deal_stage.json << 'EOF'
{
  "stage": "Technical Evaluation",
  "probability": 70,
  "deal_size": 300000,
  "timeline": "Q3 2026",
  "stakeholders": ["CTO", "VP Engineering"]
}
EOF

# Now use JARVIS
@jarvis-mcp get_proposal account=TechCorp
@jarvis-mcp get_demo_strategy account=TechCorp
```

**Result:** JARVIS automatically generates everything using your folder.

### Example 5: Preferences & Learning

**Day 1:**
```
You use: @jarvis-mcp get_proposal account=Acme Corp
JARVIS uses: Default settings
Result: Good proposal
```

**Day 2:**
```
You use: @jarvis-mcp get_battlecard account=TechStartup
JARVIS uses: Settings from Day 1
Result: Better because it learned from yesterday
```

**Day 30:**
```
JARVIS has learned:
- Which model works best for proposals
- Which temperature setting you prefer
- How detailed you like content
- Your company's terminology
- Your sales process
```

**Result:** Everything is automatically optimized for YOU.

---

## Architecture Overview

```
Your Sales Workflow
        ↓
Claude Code + @jarvis-mcp
        ↓
JARVIS MCP Server (local)
        ↓
24 Sales Intelligence Skills
        ↓
Multi-Model NVIDIA AI
        ↓
Context from Account Files
(~/Documents/claude space/ACCOUNTS/YourAccount/)
        ↓
Generated Content
(proposals, battlecards, strategies, etc.)
        ↓
Saved to Account Folder
        ↓
Back to You in Claude Code
```

---

## File Structure (What Gets Created)

After setup, you have:

```
Personal-AE-SC-Jarvis/                     [Your repo]
├── jarvis_mcp/                            [Core code]
│   ├── skills/                            [24 skills]
│   ├── config/
│   ├── llm/
│   ├── utils/
│   └── safety/
├── tests/                                 [Test suite]
├── examples/accounts/                     [Example accounts]
├── .claude/                               [Claude Code config]
├── .env                                   [Your config (NVIDIA key)]
├── setup_auto.sh                          [Auto-setup script]
├── Makefile
├── setup.py
└── README.md

~/Documents/claude space/ACCOUNTS/         [Your accounts]
├── AcmeCorp/                              [Account folder]
│   ├── company_research.md                [Input - you fill]
│   ├── discovery.md                       [Input - you fill]
│   ├── deal_stage.json                    [Input - you fill]
│   ├── proposal.md                        [Output - auto-generated]
│   ├── battlecard.md                      [Output - auto-generated]
│   ├── demo_strategy.md                   [Output - auto-generated]
│   ├── risk_report.md                     [Output - auto-generated]
│   └── ... (other generated files)
├── TechStartup/
├── GlobalBank/
└── YourNewAccount/                        [Your new accounts]

~/Documents/claude space/MEMORY/           [Learning & preferences]
├── usage_patterns.json
├── model_preferences.json
└── learned_settings.json
```

---

## Self-Setup, Self-Load, Self-Do (How It Works)

### Auto-Setup
1. Run `bash setup_auto.sh` once
2. Everything is installed and configured
3. Example accounts are ready
4. Tests verify everything works

### Auto-Load
1. When you use `@jarvis-mcp`, it auto-detects:
   - ✅ Your NVIDIA_API_KEY from .env
   - ✅ Your accounts folder location
   - ✅ All 24 skills
   - ✅ Your preferences from .claude/
2. Zero manual configuration needed

### Auto-Do
1. When you ask for a proposal:
   - ✅ Automatically reads company_research.md
   - ✅ Automatically reads discovery.md
   - ✅ Automatically reads deal_stage.json
   - ✅ Automatically generates using AI
   - ✅ Automatically saves to account folder
   - ✅ Automatically returns to you

### Auto-Learn
1. Every time you use it, JARVIS learns:
   - ✅ What you asked for
   - ✅ How long you kept using results
   - ✅ What you modified
   - ✅ Your feedback

2. Over time, JARVIS auto-optimizes:
   - ✅ Better model selection
   - ✅ Better prompts
   - ✅ Faster responses
   - ✅ More relevant content

---

## Storing Preferences

JARVIS automatically stores your preferences in:

```
.claude/CLAUDE.md
```

It tracks:
- **Model preferences**: Which AI model works best for proposals vs battlecards
- **Content style**: How detailed/brief you like things
- **Deal types**: What works for startups vs enterprises
- **Team terminology**: Your specific sales lingo
- **Success patterns**: What has worked in the past

**You don't configure this manually.** JARVIS learns from your actual usage.

---

## What Happens When You Create a New Folder

### Scenario: You create ~/my-project/sales-stuff

JARVIS **still works the same way** because:
- Account data is centralized: `~/Documents/claude space/ACCOUNTS/`
- JARVIS reads from there regardless of where you are
- You can use JARVIS from any folder/project

```bash
cd ~/my-project/sales-stuff
@jarvis-mcp get_proposal account=Acme Corp  # Still works!
```

### Scenario: You create a new account folder

JARVIS **automatically detects** new folders:

```bash
mkdir ~/Documents/claude\ space/ACCOUNTS/NewAccount
# Create company_research.md, discovery.md, deal_stage.json
@jarvis-mcp get_proposal account=NewAccount  # Auto-detected!
```

### Scenario: You nest account folders (for teams)

```bash
mkdir -p ~/Documents/claude\ space/ACCOUNTS/YourTeam/Account1
mkdir -p ~/Documents/claude\ space/ACCOUNTS/YourTeam/Account2
```

JARVIS auto-discovers nested folders:
```
@jarvis-mcp get_proposal account=Account1  # Works!
@jarvis-mcp get_proposal account=Account2  # Works!
```

---

## What Makes JARVIS Special

### 1. Zero Configuration
- Clone ✓
- Run setup script ✓
- Add one API key ✓
- Done ✓

### 2. Self-Learning
- Learns from your usage
- Improves over time
- Adjusts to your style
- No manual tuning needed

### 3. Fully Automated
- Auto-detects accounts
- Auto-generates content
- Auto-saves results
- Auto-optimizes models

### 4. Works for Everyone
- Sales reps
- Presales engineers
- Managers
- Enterprise teams
- Startups
- Solo solopreneurs

### 5. Extensible
- Add new skills easily
- Customize prompts
- Adjust models
- Add your own accounts

---

## Troubleshooting

### "NVIDIA_API_KEY not set"
```bash
nano .env
# Make sure you have:
NVIDIA_API_KEY=sk-your-actual-key-here
```

### "Account not found"
```bash
# Check account folder exists:
ls ~/Documents/claude\ space/ACCOUNTS/YourAccount/

# Check required files:
ls ~/Documents/claude\ space/ACCOUNTS/YourAccount/{company_research.md,discovery.md,deal_stage.json}
```

### "Tests failing"
```bash
# Reinstall everything
make clean
pip install -e ".[dev]"
make test
```

### "Skills not loading"
```bash
# Restart Claude Code
# Then try again
@jarvis-mcp get_proposal account=AcmeCorp
```

---

## Next Steps

1. **Clone & Setup**
   ```bash
   git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
   cd Personal-AE-SC-Jarvis
   bash setup_auto.sh
   ```

2. **Add Your NVIDIA Key**
   ```bash
   nano .env
   ```

3. **Configure Claude Code**
   Add MCP server to settings.json

4. **Start Using**
   ```
   @jarvis-mcp get_proposal account=AcmeCorp
   ```

5. **Customize**
   Add your own accounts and watch JARVIS learn

---

## Support

- **Questions?** Check the examples above
- **Issues?** See Troubleshooting
- **Want to contribute?** See CONTRIBUTING.md
- **Need help?** Review the example accounts for structure

---

**You have everything you need. Just clone and start winning deals.** 🚀

