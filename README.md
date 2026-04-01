# JARVIS MCP - AI Sales Intelligence Platform

**Zero-Config AI Assistant for Any Sales Team**

Everything auto-configures. Just clone, add API key, and start winning deals.

---

## What Is This?

JARVIS is an **AI sales consultant** that:
- Generates proposals, battlecards, demo strategies automatically
- Understands your accounts from your own notes
- Works with Claude Code (MCP protocol)
- Self-learns your preferences
- Anyone can use (sales reps, presales, managers)

**24 AI-powered skills** all working together.

---

## Quick Start (3 Steps)

### 1. Clone
```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

### 2. Auto-Setup (Everything Automatic!)
```bash
bash setup_auto.sh
```

This automatically:
- ✅ Creates Python environment
- ✅ Installs dependencies
- ✅ Sets up account folders  
- ✅ Copies 3 example accounts
- ✅ Creates .env file
- ✅ Runs tests

### 3. Add NVIDIA Key
```bash
nano .env
# Add: NVIDIA_API_KEY=your_key_here
```

**Done!** JARVIS is ready to use.

---

## How to Use

### In Claude Code

Add to your MCP settings:
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

### Then Use It
```
@jarvis-mcp get_proposal account=Acme Corp
```

Returns: A professional sales proposal based on your account data.

```
@jarvis-mcp get_battlecard account=Acme Corp competitor=ServiceCo
```

Returns: Competitive positioning and objection handling.

---

## The 24 Skills

**Core (5):** Proposal, Battlecard, Demo Strategy, Risk Report, Value Architecture  
**Discovery (5):** Discovery, Competitive Intelligence, Meeting Prep, Call Analysis, MEDDPICC  
**Deal (5):** Deal Tracker, SOW, Follow-up Email, Account Summary, Pricing Analysis  
**Advanced (9):** Technical Risk, Architecture Diagram, Documentation, HTML Export, Knowledge Graph, + 4 more

All work automatically based on your account files.

---

## How It Works

### For Each Account
```
Your Account Folder:
├── company_research.md    ← You fill this (company info)
├── discovery.md           ← You fill this (discovery notes)
├── deal_stage.json        ← You fill this (stage, probability, timeline)
└── proposal.md            ← Auto-generated
    battlecard.md          ← Auto-generated  
    demo_strategy.md       ← Auto-generated
    ... (more auto-generated)
```

### When You Ask for Something
1. You: `@jarvis-mcp get_proposal account=Acme Corp`
2. JARVIS reads: company_research.md, discovery.md, deal_stage.json
3. JARVIS generates: Professional proposal using AI
4. JARVIS saves: To proposal.md
5. You get: The content in Claude Code

**Automatic. Intelligent. Context-aware.**

---

## Self-Setup, Self-Load, Self-Do

### Auto-Setup
```bash
bash setup_auto.sh  # One command, everything ready
```

### Auto-Load
- Detects all 24 skills ✓
- Loads your accounts ✓
- Reads API key from .env ✓
- Sets up preferences ✓

**No manual configuration needed.**

### Auto-Do
- Automatically reads account files ✓
- Automatically chooses best AI model ✓
- Automatically generates content ✓
- Automatically saves results ✓
- Automatically learns your preferences ✓

---

## Preferences & Self-Learning

JARVIS stores your preferences automatically:

```
.claude/CLAUDE.md  ← Your config (auto-updated)
```

What it learns:
- Which models work best for you
- How detailed you like content
- Your company terminology
- Your sales process
- What has worked in the past

**You don't configure it.** It learns from your usage.

---

## Adding New Accounts

### Option 1: Manual (2 minutes)
```bash
mkdir ~/Documents/claude\ space/ACCOUNTS/YourAccount

# Create company_research.md
cat > ~/Documents/claude\ space/ACCOUNTS/YourAccount/company_research.md << 'EOF'
# Your Company Name
## Overview
- Founded: YYYY
- Employees: XXX
## Pain Points
- Issue 1
- Issue 2
EOF

# Create discovery.md  
cat > ~/Documents/claude\ space/ACCOUNTS/YourAccount/discovery.md << 'EOF'
# Discovery Notes
## MEDDPICC
- Metrics: XXX
- Economic Buyer: XXX
- Budget: XXX
EOF

# Create deal_stage.json
cat > ~/Documents/claude\ space/ACCOUNTS/YourAccount/deal_stage.json << 'EOF'
{
  "stage": "Demo",
  "probability": 70,
  "deal_size": 500000,
  "timeline": "Q3 2026"
}
EOF
```

### Option 2: Copy Example
```bash
cp -r ~/Documents/claude\ space/ACCOUNTS/AcmeCorp ~/Documents/claude\ space/ACCOUNTS/YourAccount
# Edit the files
```

### Then Use It
```
@jarvis-mcp get_proposal account=YourAccount
```

JARVIS auto-detects and generates everything.

---

## Can Anyone Use This?

**YES:**
- ✅ Sales Reps - proposals, follow-ups, account summaries
- ✅ Presales - demo strategies, technical docs, architecture
- ✅ Managers - risk reports, deal analysis, pipeline insights
- ✅ Anyone with Claude Code - it's designed for you

No special skills needed. If you can use Claude, you can use JARVIS.

---

## New Folder Usage

### Create Your Project Folder
```bash
mkdir ~/my-sales-project
cd ~/my-sales-project
```

### Use JARVIS from Anywhere
```
@jarvis-mcp get_proposal account=Acme Corp
```

JARVIS still reads from:
```
~/Documents/claude space/ACCOUNTS/Acme Corp/
```

**Account data is centralized.** All your projects use the same accounts. This means:
- ✅ Easy to share with team
- ✅ Easy to backup
- ✅ Consistent across projects
- ✅ One source of truth

---

## Auto-Population

When you clone, example accounts auto-populate:
```
~/Documents/claude space/ACCOUNTS/
├── AcmeCorp/           ✓ Ready to use
├── TechStartup/        ✓ Ready to use
└── GlobalBank/         ✓ Ready to use
```

When you create a NEW account, just add 3 files:
```
YourAccount/
├── company_research.md
├── discovery.md
└── deal_stage.json
```

JARVIS auto-generates all others:
```
YourAccount/
├── proposal.md         ← Auto-created
├── battlecard.md       ← Auto-created
├── demo_strategy.md    ← Auto-created
├── risk_report.md      ← Auto-created
└── ... (more auto-created)
```

**No empty files needed.** JARVIS creates what's needed, when it's needed.

---

## Real Example

### Day 1: Start
```bash
bash setup_auto.sh
nano .env  # Add NVIDIA_API_KEY
```

Example accounts ready. You're done.

### Day 2: Use with Example Account
```
@jarvis-mcp get_proposal account=AcmeCorp
```

JARVIS returns a proposal for AcmeCorp (from examples).

### Day 3: Add Your Account
```bash
mkdir ~/Documents/claude\ space/ACCOUNTS/MyCustomer
# Create 3 files with your info
```

### Day 4: Use with Your Account
```
@jarvis-mcp get_proposal account=MyCustomer
@jarvis-mcp get_battlecard account=MyCustomer
@jarvis-mcp get_demo_strategy account=MyCustomer
```

All automatic. All smart. All contextual.

### Day 5+: JARVIS Learns
```
JARVIS stores:
- What you asked for
- How you used the results
- What worked
- Your preferences

Next time, it's even better.
```

---

## File Structure

```
Personal-AE-SC-Jarvis/
├── jarvis_mcp/              # Core (24 skills + infrastructure)
├── tests/                   # Full test suite (24 tests)
├── examples/accounts/       # Example accounts
├── .claude/                 # Claude Code config
├── setup_auto.sh            # Auto-setup script
├── setup.py                 # Package setup
├── requirements.txt         # Dependencies
├── Makefile                 # Dev commands
├── README.md                # This file
├── README_COMPLETE.md       # Full guide (read this for details!)
└── .env.example             # Environment template

~/Documents/claude space/ACCOUNTS/
└── YourAccount/
    ├── company_research.md  # You fill
    ├── discovery.md         # You fill
    ├── deal_stage.json      # You fill
    ├── proposal.md          # Auto-generated
    ├── battlecard.md        # Auto-generated
    └── ... (more auto-generated)
```

---

## Commands

```bash
# Run tests
make test

# Format code
make format

# Check code quality
make lint

# Run the server
python -m jarvis_mcp.mcp_server

# See all commands
make help
```

---

## Full Documentation

For complete explanations, examples, and troubleshooting, read:
```
README_COMPLETE.md
```

That file has:
- Detailed architecture
- All 24 skills explained
- Complete workflow examples
- Troubleshooting guide
- Advanced configuration

---

## Next Steps

1. **Clone & Auto-Setup** (3 minutes)
   ```bash
   git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
   cd Personal-AE-SC-Jarvis
   bash setup_auto.sh
   ```

2. **Add Your NVIDIA Key** (30 seconds)
   ```bash
   nano .env
   # Add: NVIDIA_API_KEY=your_key_here
   ```

3. **Add to Claude Code** (1 minute)
   - Open Claude Code settings
   - Add MCP server config
   - Restart Claude Code

4. **Start Using** (immediately)
   ```
   @jarvis-mcp get_proposal account=AcmeCorp
   ```

5. **Add Your Accounts** (as needed)
   - Create account folders
   - Add your data
   - JARVIS handles the rest

---

## Questions?

- **How does it work?** → Read README_COMPLETE.md
- **What are the 24 skills?** → README_COMPLETE.md
- **How do I add accounts?** → README_COMPLETE.md
- **How do preferences work?** → README_COMPLETE.md
- **Issues?** → Check troubleshooting in README_COMPLETE.md

---

**Zero config. Self-setup. Self-learning. Self-doing.**

Just clone and start winning. 🚀

