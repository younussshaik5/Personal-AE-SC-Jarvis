# JARVIS v2.0 Quick Start

**Get JARVIS running in 3 minutes**

## Step 1: Clone (30 seconds)
```bash
git clone https://github.com/younussshaik5/Personal-AE-SC-Jarvis.git
cd Personal-AE-SC-Jarvis
```

## Step 2: Set API Key (30 seconds)
Get your NVIDIA API key from [api.nvidia.com](https://api.nvidia.com)

```bash
export NVIDIA_API_KEY="your_key_here"
```

## Step 3: Add to Claude Desktop (2 minutes)

Open `~/.claude/config.json` and add this block:

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python3",
      "args": ["/full/path/to/Personal-AE-SC-Jarvis/jarvis_mcp/mcp_server.py"],
      "env": {
        "NVIDIA_API_KEY": "your_key_here"
      }
    }
  }
}
```

Replace `/full/path/to/` with your actual path:
```bash
pwd  # Copy this output and use it above
```

## Step 4: Restart Claude Desktop

Close Claude Desktop completely, then reopen it.

## Try It Out

In any Claude cowork session:

```
Create a new account for Acme Corporation
```

JARVIS will:
- Ask for confirmation ✓
- Create `~/Documents/claude space/ACCOUNTS/Acme/` ✓
- Add deal_stage.json, discovery.md, company_research.md, CLAUDE.md ✓
- Generate dashboard.html ✓

Done! Start working on your account.

## Next Steps

See [README.md](README.md) for:
- How to create sub-accounts (Acme → AcmeEdu, AcmeSaaS)
- How to view dashboards
- All 25+ available skills
- Settings & customization

---

**Questions?** Check [README.md](README.md#troubleshooting)
