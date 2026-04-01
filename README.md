# JARVIS v2.0 - AI Sales Intelligence Platform

**Production-ready autonomous AI sales assistant for presales & AE workflows**

Zero manual setup. Just clone, set API key, and go.

## What is JARVIS v2.0?

JARVIS is an MCP (Model Context Protocol) server that runs inside Claude Desktop and provides 25+ intelligent skills for sales teams:

- **Account Management**: Auto-scaffold accounts with hierarchies (parent/child relationships like Tata → TataTele, TataSky)
- **Discovery & Intelligence**: Competitive analysis, battlecards, MEDDPICC, technical risk assessment
- **Proposal Generation**: SOWs, architecture diagrams, custom templates, value propositions
- **Deal Tracking**: Real-time deal stage tracking, risk reports, stakeholder management
- **Enterprise Dashboards**: CRM-like HTML dashboards for each opportunity
- **Self-Learning**: CLAUDE.md auto-evolves based on interaction patterns
- **Context-Aware**: Automatically detects which account you're working on

## Quick Start (5 minutes)

### 1. Clone
```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

### 2. Set API Key
```bash
export NVIDIA_API_KEY="your_nvidia_api_key_here"
```

Or add to your `.zshrc` / `.bashrc`:
```bash
echo 'export NVIDIA_API_KEY="your_key"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Setup Claude Desktop (MCP)

Edit `~/.claude/config.json` and add:

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python3",
      "args": [
        "/path/to/Personal-AE-SC-Jarvis/jarvis_mcp/mcp_server.py"
      ],
      "env": {
        "NVIDIA_API_KEY": "your_nvidia_api_key",
        "ACCOUNTS_ROOT": "/Users/YOUR_USERNAME/Documents/claude space/ACCOUNTS"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Close and reopen Claude Desktop. You should see "jarvis-mcp" in the available tools.

### 5. Try It Out

In any cowork session:
```
@jarvis create account for Tata

or

I'm working on discovering Tata's technical architecture
→ Claude auto-detects you're in Tata account context
→ Recommends relevant skills
→ Loads hierarchical settings
```

## Project Structure

```
Personal-AE-SC-Jarvis/
├── jarvis_mcp/                 # MCP Server (runs in Claude Desktop)
│   ├── config/                 # Configuration management
│   ├── llm/                    # LLM provider abstraction
│   ├── utils/                  # Logging, file utilities
│   ├── safety/                 # Safety guards & killswitch
│   ├── skills/                 # 25+ presales skills
│   ├── mcp_server.py           # Main MCP entry point
│   ├── account_hierarchy.py    # Parent/child account management
│   ├── context_detector.py     # Auto-detect current account
│   ├── claude_md_loader.py     # Hierarchical settings loading
│   ├── claude_md_evolve.py     # Self-learning CLAUDE.md
│   ├── scaffolder.py           # Auto-create accounts & templates
│   └── account_dashboard.py    # HTML dashboard generator
│
├── ACCOUNTS/                   # All opportunities (created on first use)
│   ├── Tata/                   # Parent company
│   │   ├── deal_stage.json     # Tata's deal metadata
│   │   ├── company_research.md # Tata research (inherited by children)
│   │   ├── discovery.md        # Tata's discovery notes
│   │   ├── CLAUDE.md           # Tata account settings
│   │   ├── dashboard.html      # Tata's CRM dashboard
│   │   ├── TataTele/           # Sub-account (inherits parent research)
│   │   │   ├── deal_stage.json
│   │   │   ├── discovery.md    # Own discovery (not inherited)
│   │   │   ├── CLAUDE.md
│   │   │   └── dashboard.html
│   │   └── TataSky/            # Another sub-account
│   │       ├── deal_stage.json
│   │       ├── discovery.md
│   │       ├── CLAUDE.md
│   │       └── dashboard.html
│   └── [Other Accounts]/
│
└── README.md (this file)
```

## Core Features

### 1. Zero-Manual Account Creation

**Old way**: Manually create folders, files, templates
**New way**: Just mention an account name, Claude asks for confirmation

```
User: "I'm working on Tata"
Claude: "Should I create a Tata account? (Revenue/Industry optional)"
User: "Yes, create it"
→ Instant: folder, deal_stage.json, company_research.md, discovery.md, CLAUDE.md
```

### 2. Account Hierarchies

Create parent accounts with child opportunities:

```
Tata (parent)
├── TataTele (child inherits company_research.md)
├── TataSky (child inherits company_research.md)
└── TataTV (child inherits company_research.md)
```

Each child:
- **Inherits**: Parent's `company_research.md` (shared research)
- **Owns**: Their own `discovery.md`, `deal_stage.json`, `CLAUDE.md`

### 3. Context-Aware Workflow

When you navigate into an account folder:

```bash
cd ~/Documents/claude\ space/ACCOUNTS/Tata/TataTele
# Now in cowork session:
```

JARVIS automatically:
- ✓ Detects you're in TataTele account
- ✓ Loads TataTele's deal_stage.json (deal metrics)
- ✓ Loads TataTele's CLAUDE.md settings
- ✓ Falls back to Tata's CLAUDE.md for inherited rules
- ✓ Loads shared company_research.md from parent
- ✓ Recommends relevant skills for this deal stage

### 4. Enterprise Dashboards

Each account has a `dashboard.html` CRM-like view:

```html
Open: ~/ACCOUNTS/Tata/dashboard.html in browser
→ Shows: Deal stage, probability, stakeholders, activities, risks, 
         competitive info, value metrics
→ Auto-updates from deal_stage.json
```

### 5. Self-Learning CLAUDE.md

JARVIS tracks your interactions and auto-evolves settings:

- Records which skills you use
- Learns your preferred models
- Detects success patterns
- Suggests CLAUDE.md improvements
- Auto-applies approved changes

Example: "I notice you use the Battlecard skill for every discovery call. Should I auto-enable it for this account?"

### 6. 25+ Skills (Always Growing)

Core skills:
- `scaffold_account` - Create new accounts/sub-accounts
- `account_summary` - Quick account overview
- `discovery` - MEDDPICC framework
- `battlecard` - Competitive positioning
- `proposal` - Generate SOWs
- `meeting_prep` - Pre-meeting intelligence
- `demo_strategy` - Demo customization
- `risk_report` - Technical/commercial risks
- `value_architecture` - Architecture-based value prop
- And 15+ more...

## Settings & Customization

### Per-Account: CLAUDE.md

Each account has a `CLAUDE.md` that controls:

```markdown
# CLAUDE.md for Tata/TataTele

## Cascade Rules
- Parent settings: inherit from Tata if not specified
- Global settings: inherit from ~/.claude/projects/...

## Model Preferences
- Use Sonnet for reasoning tasks (discovery, risk analysis)
- Use Haiku for quick summaries
- Use Opus for complex proposals

## Skill Preferences
- Auto-enable: discovery, battlecard
- Suggest: proposal, demo_strategy
- Hide: (not used for this deal)

## Routing Rules
- If mention competitor X → use competitive_intelligence
- If discovery call → use discovery + risk_report
```

### Global: Environment Variables

```bash
ACCOUNTS_ROOT=/path/to/accounts      # Where to store accounts
NVIDIA_API_KEY=your_key              # NVIDIA LLM access
NVIDIA_MODEL=meta/llama-3.1-405b    # Model choice
```

## Workflows

### Workflow 1: New Opportunity

```
1. In cowork: "Create account for Acme Corp"
2. Claude asks: "Create Acme with standard settings? (Optional: revenue, industry)"
3. You confirm: "Yes"
4. Instant: Folder created with all templates
5. Navigate: cd ACCOUNTS/Acme
6. Start discovery with auto-loaded context
```

### Workflow 2: Sub-Opportunity under Parent

```
1. "Create TataTele under Tata"
2. Claude: "TataTele will inherit Tata's company_research.md. Continue?"
3. You confirm
4. Result: TataTele has own metrics but shares Tata's research
```

### Workflow 3: Discovery Call

```
1. Navigate to account: cd ACCOUNTS/Tata/TataTele
2. Start cowork session
3. Claude auto-detects context
4. Use @jarvis discovery → auto-loads TataTele's discovery notes
5. After call: @jarvis update deal_stage (auto-saves to deal_stage.json)
6. View progress: Open dashboard.html in browser
```

### Workflow 4: Generate Proposal

```
1. In Tata/TataTele context
2. @jarvis proposal --type=sow
3. Claude loads:
   - TataTele's deal_stage.json (deal metrics)
   - Tata's company_research.md (shared research)
   - TataTele's discovery.md (notes)
   - Architecture from risk_report or demo_strategy
4. Generate: Professional SOW ready for editing
```

## API Key Setup

### Option 1: Environment Variable (Recommended)

```bash
export NVIDIA_API_KEY="nvidia-xxx-xxx"
```

### Option 2: .env File

Create `~/.claude/.env`:
```
NVIDIA_API_KEY=nvidia-xxx-xxx
```

### Option 3: Claude Desktop Config

Edit `~/.claude/config.json`:
```json
{
  "mcpServers": {
    "jarvis": {
      "env": {
        "NVIDIA_API_KEY": "nvidia-xxx-xxx"
      }
    }
  }
}
```

## Troubleshooting

### MCP Not Appearing in Claude Desktop

1. Check path in config.json is correct:
   ```bash
   ls ~/Personal-AE-SC-Jarvis/jarvis_mcp/mcp_server.py
   ```

2. Verify Python path:
   ```bash
   which python3
   ```

3. Test MCP directly:
   ```bash
   cd ~/Personal-AE-SC-Jarvis
   python3 -c "from jarvis_mcp.mcp_server import JarvisServer; print('OK')"
   ```

4. Restart Claude Desktop

### Accounts Folder Not Found

```bash
# Check default location
ls ~/Documents/claude\ space/ACCOUNTS/

# Or set custom location
export ACCOUNTS_ROOT="/your/custom/path"
```

### Skills Not Loading

```bash
cd ~/Personal-AE-SC-Jarvis
python3 -c "from jarvis_mcp.skills import SKILL_REGISTRY; print(len(SKILL_REGISTRY))"
# Should output: 25
```

## Architecture

### MCP Server
- **Entry**: `mcp_server.py` - Runs when Claude Desktop opens
- **Lifecycle**: Starts when Claude boots, stops when Claude closes
- **Transport**: stdio (built-in to MCP)
- **Skills**: 25+ registered as MCP tools

### Infrastructure
- **ConfigManager**: Loads settings from environment + CLAUDE.md
- **ContextDetector**: Detects current account from cwd
- **AccountHierarchy**: Manages parent/child relationships
- **ClaudeMDLoader**: Hierarchical settings (account → parent → global)
- **ClaudeMDEvolve**: Self-learning system
- **Scaffolder**: Auto-creates accounts with templates
- **AccountDashboard**: Generates HTML dashboards

### Data Structure
- **deal_stage.json**: Account metrics (stage, probability, deal_size, stakeholders, etc.)
- **company_research.md**: Shared research (inherited by children)
- **discovery.md**: Account-specific discovery notes
- **CLAUDE.md**: Settings & preferences (hierarchical)
- **dashboard.html**: CRM view (auto-generated)

## FAQ

**Q: Do I need to manually create account folders?**
A: No. Just mention the account name and Claude creates everything.

**Q: Can I have sub-accounts under sub-accounts?**
A: Yes. Unlimited nesting. Each level inherits parent's company_research.md.

**Q: How often does CLAUDE.md auto-evolve?**
A: Every 10 interactions. Suggestions are shown; you approve before changes apply.

**Q: What happens if I'm not in an ACCOUNTS folder?**
A: JARVIS uses ACCOUNTS_ROOT env var. You can work from anywhere.

**Q: Can I customize dashboard styling?**
A: Yes. Edit the HTML template in `account_dashboard.py` and regenerate.

**Q: Is this production-ready?**
A: Yes. Tested with 25+ skills, account hierarchies, and MCP integration.

## Support

- **Issues**: Report on GitHub
- **Features**: Suggest improvements
- **Questions**: Check troubleshooting section

## License

Internal tool for yellow.ai sales team. All rights reserved.

---

**Ready to use. Just set your NVIDIA_API_KEY and go.**
