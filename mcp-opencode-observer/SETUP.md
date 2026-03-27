# MCP Observer Setup Guide

## What Is This?

An autonomous MCP server that runs alongside OpenCode, continuously observing your conversations and updating memory files, persona context, and organizing sessions by date. First 50 changes require approval; after that it's fully autonomous.

## Prerequisites

- Node.js 18+ installed
- OpenCode running and accessible on localhost:4096
- OpenCode workspace at: `/path/to/your/workspace`

## Installation Already Done

The MCP observer is already built in this directory with `npm install` and `npm run build`.

## Configuration

Edit `~/.config/opencode/opencode.jsonc` (or create if not exists) and add:

```json
{
  "mcp": {
    "observer": {
      "type": "local",
      "command": ["node", "/path/to/your/workspace/mcp-opencode-observer/dist/index.js"],
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

**Important**: Use the absolute path to `dist/index.js`.

## How It Works

1. OpenCode reads its config and launches the MCP observer on startup
2. Observer starts polling the OpenCode SQLite DB (`~/.local/share/opencode/opencode.db`)
3. Each new message is analyzed using keyword + simple NLP
4. Updates are applied to:
   - `MEMORY/active_persona.json` (auto persona switching)
   - `MEMORY/patterns/*.json` (preferences, skills used)
   - `MEMORY/YYYY/MMMM/persona/sessions/` (date-based archiving)
   - `MEMORY/audit_log.json` (complete change history)
   - `MEMORY/competitor_mentions.json` (for battlecards)
5. First 50 changes are logged as requiring approval (auto-approved by default in this version)
6. After 50 changes, runs 100% autonomously

## Rules Customization

Edit `mcp-opencode-observer/config/rules.yaml` to change triggers, actions, or approval threshold.

## Testing

1. Restart OpenCode (or launch if not running)
2. Start a conversation mentioning "yellow.ai" or "demo"
3. Check `MEMORY/active_persona.json` - it should update automatically
4. Check logs: `mcp-opencode-observer/logs/combined.log`

## Verification

Run this to see observer status (as an MCP tool call from OpenCode or via the tool UI):
```
observer_status
```

Should return JSON with changeCount, currentPersona, etc.

## Stopping

- To stop observer: kill the process. OpenCode will respawn it on next start.
- To disable: set `"enabled": false` in OpenCode config and restart.

## Troubleshooting

- **Observer not starting**: Check OpenCode config syntax (JSONC). Validate with `jq . ~/.config/opencode/opencode.jsonc`
- **No updates**: Ensure OpenCode DB exists and is being written to. Verify poll messages in logs.
- **Permission errors**: Observer must have write access to workspace MEMORY/ folder.
- **Path not allowed**: Rules safety config restricts paths. Edit `config/rules.yaml` safety.allowed_paths.

## Development

```bash
cd mcp-opencode-observer
npm run dev   # watch mode with ts-node
npm run build # compile
npm start     # run standalone (not through OpenCode)
```

## Files

- `src/autonomy.ts` - core autonomous loop and update functions
- `src/db.ts` - OpenCode DB access layer
- `src/index.ts` - MCP server and tool definitions
- `config/rules.yaml` - trigger and action configuration
- `MEMORY/` - where updates are written (your workspace)

## Notes

- This observer uses keyword-based extraction (not a heavy LLM) for speed and reliability
- All file writes are backed up in `data/backups/`
- Audit log records every change with reason and timestamp
- Switch rules are easy to add; see rules.yaml examples

Enjoy your autonomous AI employee! 🚀