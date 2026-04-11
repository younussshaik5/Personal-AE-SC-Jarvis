# JARVIS MCP — Quick Start (5 Minutes)

## Step 1: Get Free NVIDIA API Key

Visit **https://build.nvidia.com/** and grab a free API key (2 minutes, no credit card)

## Step 2: Run Setup (One Command)

After cloning the repo, just run:

```bash
bash setup.sh
```

During setup, it will create `.env` and prompt you to add your API key. The script will:

1. **Check/Install Homebrew** (if missing)
2. **Auto-install Python 3.13** (if you don't have 3.10+)
3. **Install all Python dependencies** (mcp, anthropic, pydantic, etc)
4. **Create ACCOUNTS folder** (where all account data lives)
5. **Register JARVIS in Claude Desktop config** (with correct paths for your machine)
6. **Run smoke tests** (verify everything works)

## Step 3: Add API Key to .env

During `bash setup.sh`, a `.env` file is created. Edit it:

```bash
# Open the JARVIS folder, find .env file
# Find the line: NVIDIA_API_KEY=
# Replace with your key from https://build.nvidia.com/
NVIDIA_API_KEY=nvapi-your_actual_key_here
```

Or verify it's configured:
```bash
python3 check_api_key.py
```

## Step 4: Restart Claude Desktop

1. **Quit Claude Desktop** (⌘Q)
2. **Reopen Claude Desktop**
3. **Look for 🔨 Tools** in the sidebar
4. **JARVIS appears** with 27 available skills

## Already have dependencies?

No problem. `setup.sh` will skip things that are already installed and update config.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Python not found" | `brew install python@3.13` |
| "mcp module not found" | Run `bash setup.sh` again |
| "NVIDIA API key missing" | Run `python3 check_api_key.py` and add your key |
| "LLM calls failing" | API key might be wrong — verify at https://build.nvidia.com/ |
| "Claude Desktop not connecting" | Quit Claude (⌘Q), wait 2 sec, reopen |
| Setup runs but tools don't appear | Check: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json` |

## What gets installed?

- **Python 3.13** (via Homebrew, if needed)
- **mcp** — Model Context Protocol SDK
- **anthropic** — Claude API client
- **pydantic** — Data validation
- **aiofiles** — Async file I/O

All listed in `requirements.txt`.

## Uninstall

```bash
# Remove JARVIS from Claude Desktop (optional)
rm -rf ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Remove ACCOUNTS folder (optional)
rm -rf ~/Documents/claude\ space/ACCOUNTS
```

## For Development

To rebuild the server after code changes:

```bash
# The server auto-restarts when you reopen Claude Desktop
# No manual restart needed
```

---

**That's all!** JARVIS is production-ready and auto-syncs with Claude Desktop.
