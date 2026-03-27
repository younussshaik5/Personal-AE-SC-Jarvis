# MCP OpenCode Observer

Autonomous MCP server that observes OpenCode conversations in real-time, providing tools to query chat history, sessions, and tool outputs.

## Features

- **Real-time monitoring** of OpenCode sessions via database polling and SSE
- **MCP tools** to query conversations, sessions, messages
- **Event streaming** via WebSocket for live updates
- **Persistent storage** of observed conversation history
- **Configurable filters** for sessions, users, agents

## Setup

```bash
npm install
npm run build
```

## Configuration

Create `config/mcp-observer.json`:

```json
{
  "opencode": {
    "dbPath": "~/.local/share/opencode/opencode.db",
    "logDir": "~/.local/share/opencode/log",
    "toolOutputDir": "~/.local/share/opencode/tool-output"
  },
  "observer": {
    "port": 3000,
    "wsPort": 3001,
    "pollInterval": 1000,
    "maxSessions": 100
  },
  "mcp": {
    "serverName": "opencode-observer",
    "transport": "stdio"
  }
}
```

## Integration with OpenCode

Add to `~/.config/opencode/opencode.jsonc`:

```json
{
  "mcp": {
    "observer": {
      "type": "local",
      "command": ["node", "/path/to/mcp-opencode-observer/dist/server.js"],
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

## MCP Tools Provided

- `get_sessions(limit, workspace)` - List recent sessions
- `get_session_messages(session_id)` - Get all messages in a session
- `get_session_details(session_id)` - Full session metadata
- `get_tool_output(tool_id)` - Retrieve tool execution output
- `search_conversations(query, limit)` - Full-text search
- `get_recent_messages(limit, agent)` - Latest messages across all sessions
- `get_live_updates()` - Stream real-time updates (SSE)
- `get_agent_stats(agent, hours)` - Agent activity statistics

## Running

```bash
# Standalone MCP server (stdio)
node dist/server.js

# With monitoring dashboard
npm start

# Development
npm run dev
```