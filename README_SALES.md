# JARVIS - Your AI Sales Assistant

**Stop manual work. Let AI handle discovery, proposals, and deal tracking.**

JARVIS runs inside Claude Desktop and does the boring stuff for you:
- Auto-create account folders
- Generate discovery templates
- Write competitive battlecards
- Draft proposals
- Track deal progress
- Create dashboards

## Setup (3 Steps)

### 1️⃣ Get Your API Key
Go to [nvidia.com/api](https://nvidia.com/api) and get your NVIDIA key.

### 2️⃣ Clone This Project
```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

### 3️⃣ Tell Claude Desktop to Use JARVIS

Open this file: `~/.claude/config.json`

Add this section (or add to existing `mcpServers`):

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python3",
      "args": ["/Users/YOUR_USERNAME/Personal-AE-SC-Jarvis/jarvis_mcp/mcp_server.py"],
      "env": {
        "NVIDIA_API_KEY": "paste_your_nvidia_key_here"
      }
    }
  }
}
```

**Replace:**
- `YOUR_USERNAME` with your macOS username
- `paste_your_nvidia_key_here` with your actual NVIDIA API key

### 4️⃣ Restart Claude Desktop

Close Claude Desktop completely, then reopen it.

**Done.** JARVIS is now active.

---

## How to Use

### Example 1: Create a New Opportunity

In Claude Desktop, write:
```
Create an account for Acme Corporation
```

JARVIS will:
- Ask for confirmation ✓
- Create folder: `~/Documents/claude space/ACCOUNTS/Acme/` ✓
- Add all templates (discovery notes, deal tracker, competitor analysis) ✓
- Generate a dashboard ✓

### Example 2: Add Sub-Opportunities

Acme has divisions? Create them as sub-accounts:
```
Create AcmeEdu and AcmeSaaS under Acme
```

JARVIS will:
- Create both as children of Acme ✓
- They inherit Acme's research ✓
- They track their own deals separately ✓

### Example 3: Run Discovery Call

You just finished discovery with Acme:
```
I met with their VP of Engineering. They have 3 pain points:
1. Current vendor is too expensive
2. Implementation takes too long  
3. Limited customization

Timeline: Want to pilot in Q2. Budget: $500K.
```

JARVIS will:
- Save notes to their discovery file ✓
- Update deal progress ✓
- Suggest next steps ✓

### Example 4: Generate a Proposal

```
@jarvis generate proposal for Acme
```

JARVIS will:
- Load all their info (discovery notes, budget, timeline) ✓
- Write a professional proposal ✓
- Include ROI based on their pain points ✓

### Example 5: Check Deal Progress

```
Show me Acme's current deal status
```

JARVIS will:
- Show stage, probability, deal size ✓
- List stakeholders and next steps ✓
- Highlight risks ✓

### Example 6: Create Competitive Analysis

```
@jarvis battlecard for Acme vs Oracle
```

JARVIS will:
- Compare your solution vs Oracle ✓
- List your strengths ✓
- Show their pricing ✓
- Provide talking points ✓

---

## What You Get

### 25+ Skills (Tools)

1. **Discovery** - MEDDPICC framework
2. **Battlecard** - Competitive positioning
3. **Proposal** - Generate SOWs
4. **Meeting Prep** - Pre-call research
5. **Risk Report** - Technical risks
6. **Deal Tracker** - Progress updates
7. **Competitor Analysis** - Market research
8. And 17 more...

### Smart Accounts

Each account has:
- **Deal tracker** - Stage, probability, deal size
- **Discovery notes** - All meeting notes
- **Competitor analysis** - How you compare
- **Dashboard** - Visual deal progress
- **Settings** - Auto-learns your preferences

### Parent/Child Accounts

```
Tata (parent)
├── TataTele (telecom division)
├── TataSky (streaming division)
└── TataTV (broadcast division)
```

Each child:
- Shares parent's research
- Tracks their own deal
- Has separate dashboard

---

## Dashboard

Each account has an HTML dashboard:

Open: `~/Documents/claude space/ACCOUNTS/Acme/dashboard.html`

Shows:
- Deal stage
- Probability
- Deal size
- Stakeholders
- Next steps
- Competitive threats
- Timeline

Updates automatically as you update the deal.

---

## Examples: What Claude Can Help With

### Create Account
```
Create account for Salesforce

or

Create sub-account: Salesforce Marketing Cloud under Salesforce
```

### Update Deal
```
Update Acme deal: Stage = Demo Scheduled, Probability = 40%, Size = $500K

or

We met VP Sales today. Add these notes:
- Budget approved Q2
- Wants 2-week pilot
- Competitor is Oracle
```

### Generate Content
```
Write discovery questions for a CRM sale

or

Generate SOW for Acme with these requirements:
- Implementation in 4 weeks
- Custom APIs
- 2 training sessions
```

### Get Analysis
```
Show me all deals in demo stage

or

Create competitive battlecard: Acme vs Salesforce

or

What's our win rate vs Oracle in the last 90 days?
```

---

## File Structure

```
~/Documents/claude space/
├── ACCOUNTS/
│   ├── Acme/
│   │   ├── deal_stage.json ← Deal metrics
│   │   ├── discovery.md ← Meeting notes
│   │   ├── company_research.md ← Company info
│   │   ├── CLAUDE.md ← Settings
│   │   ├── dashboard.html ← Visual dashboard
│   │   ├── AcmeEdu/ ← Sub-account
│   │   │   ├── deal_stage.json
│   │   │   ├── discovery.md
│   │   │   ├── CLAUDE.md
│   │   │   └── dashboard.html
│   │   └── AcmeSaaS/ ← Sub-account
│   │       └── ...
│   └── Tata/
│       ├── deal_stage.json
│       ├── TataTele/
│       └── TataSky/
```

Everything is in one folder. Easy to backup, easy to share.

---

## Important Notes

### ✅ What Happens Automatically

- JARVIS starts when you open Claude Desktop
- JARVIS stops when you close Claude Desktop
- All data saves to local folders (no cloud)
- Everything offline (no tracking)

### ⚠️ You Control

- You write the discovery notes
- You decide the deal stage
- You approve all proposals
- Claude assists, you decide

### 🔒 Privacy

- All data local (no servers)
- No tracking
- No sharing
- Just you and your deals

---

## Troubleshooting

### MCP Not Working?

1. Check NVIDIA API key is correct
2. Make sure path in config.json is right:
   ```bash
   pwd  # Copy this and use in config.json
   ```
3. Close Claude Desktop completely (force quit)
4. Reopen Claude Desktop
5. Try: `@jarvis server_status`

### Can't Find Account?

Check folder exists:
```bash
ls ~/Documents/claude\ space/ACCOUNTS/Acme/
```

Should show: `deal_stage.json`, `discovery.md`, etc.

### Dashboard Not Updating?

Refresh browser: `Cmd + R`

The dashboard reads from `deal_stage.json`, so update that file to see changes.

---

## Getting Started Right Now

1. ✅ You cloned the repo
2. ✅ You added API key to config.json
3. ✅ You restarted Claude Desktop
4. Try this in Claude:

```
Create account for my first customer
```

Done. You're ready to use JARVIS.

---

## Questions?

See **QUICKSTART.md** for more setup details.

See **ACCOUNT_CREATION.md** for detailed account workflows.

See **README.md** for technical details.

---

**That's it. Clone, add API key, restart Claude. Go sell.**
