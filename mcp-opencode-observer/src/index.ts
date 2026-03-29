import { ConversationDB } from './db';
import { createServer as createHttpServer } from 'http';
import { readFileSync, existsSync, unlinkSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { WebSocketServer } from 'ws';
import { startAutonomy, getStatus } from './autonomy';

function expandHome(p: string): string {
  if (p.startsWith('~/') || p === '~') {
    return join(homedir(), p.slice(2));
  }
  return p;
}

// Load configuration
const configPath = process.env.OPENCODE_OBSERVER_CONFIG || join(process.cwd(), 'config', 'mcp-observer.json');
let config: any = {};

try {
  if (existsSync(configPath)) {
    config = JSON.parse(readFileSync(configPath, 'utf-8'));
  }
} catch (e: any) {
  console.error('Failed to load config:', e.message);
  config = {};
}

// Portable defaults — detect OpenCode DB per OS
if (!config.opencode) {
  config.opencode = {};
}
if (!config.opencode.dbPath) {
  config.opencode.dbPath = expandHome(
    process.env.OPENCODE_DB_PATH || '~/.local/share/opencode/opencode.db'
  );
}
if (!config.opencode.toolOutputDir) {
  config.opencode.toolOutputDir = expandHome(
    process.env.OPENCODE_TOOL_OUTPUT_DIR || '~/.local/share/opencode/tool-output'
  );
}
if (!config.observer) {
  config.observer = {
    port: parseInt(process.env.OPENCODE_OBSERVER_PORT || '3000', 10),
    wsPort: parseInt(process.env.OPENCODE_OBSERVER_WS_PORT || '3001', 10),
    pollInterval: parseInt(process.env.OPENCODE_OBSERVER_POLL_INTERVAL || '1000', 10)
  };
}

// Expand ~ in all path fields
config.opencode.dbPath = expandHome(config.opencode.dbPath);
config.opencode.toolOutputDir = expandHome(config.opencode.toolOutputDir);

// Initialize database
const db = new ConversationDB(config.opencode.dbPath);

// ============ Start Autonomous Observer ============
startAutonomy(db);

// ============ HTTP + WebSocket Server (optional monitoring) ============
const httpServer = createHttpServer();
const wsPort = config.observer.wsPort || 3001;
const wss = new WebSocketServer({ port: wsPort });
const wsClients = new Set<any>();

wss.on('connection', (ws) => {
  console.error('[Observer] WebSocket client connected');
  wsClients.add(ws);
  ws.on('close', () => wsClients.delete(ws));
});

function broadcastUpdate(data: any) {
  const msg = JSON.stringify(data);
  for (const client of wsClients) {
    if ((client as any).readyState === 1) (client as any).send(msg);
  }
}

httpServer.listen(config.observer.port || 3000, () => {
  console.error(`[Observer] HTTP on ${config.observer.port || 3000}, WS on ${wsPort}`);
});

console.error('[Observer] MCP stdio server started');
console.error('[Observer] Monitoring conversations in:', config.opencode.dbPath);

// ============ MCP STDIO SERVER ============

let requestBuffer = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', (chunk: string) => {
  requestBuffer += chunk;
  const lines = requestBuffer.split('\n');
  requestBuffer = lines.pop() || '';

  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const req = JSON.parse(line);
      handleRequest(req);
    } catch (error: any) {
      console.error('Failed to parse request:', error.message);
    }
  }
});

async function handleRequest(req: any) {
  const { id, method, params } = req;
  let result: any, error: any = null;

  try {
    switch (method) {
      case 'initialize':
        result = {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: { name: 'conversation-observer', version: '1.0.0' }
        };
        break;

      case 'tools/list':
        result = {
          tools: [
            {
              name: 'observer_status',
              description: 'Get observer status and change count',
              inputSchema: { type: 'object', properties: {} }
            },
            {
              name: 'get_recent_sessions',
              description: 'Get recent OpenCode and Claude sessions',
              inputSchema: { type: 'object', properties: { limit: { type: 'number', default: 10 } } }
            },
            {
              name: 'get_session_chat',
              description: 'Get messages in a session',
              inputSchema: { type: 'object', properties: { session_id: { type: 'string' } }, required: ['session_id'] }
            }
          ]
        };
        break;

      case 'tools/call':
        result = await callTool(params.name, params.arguments || {});
        break;

      default:
        error = { code: -32601, message: `Method not found: ${method}` };
    }
  } catch (err: any) {
    error = { code: -32603, message: err.message };
  }

  sendResponse(id, result, error);
}

async function callTool(name: string, args: any) {
  switch (name) {
    case 'observer_status':
      return { content: [{ type: 'text', text: JSON.stringify(getStatus(), null, 2) }] };
      
    case 'get_recent_sessions':
      const sessions = await db.getSessions(args.limit || 10);
      return { content: [{ type: 'text', text: JSON.stringify(sessions, null, 2) }] };
      
    case 'get_session_chat':
      if (!args.session_id) throw new Error('session_id required');
      const messages = await db.getSessionMessages(args.session_id);
      return { content: [{ type: 'text', text: JSON.stringify(messages, null, 2) }] };
      
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

function sendResponse(id: number, result: any, error: any) {
  const response = { jsonrpc: '2.0', id };
  if (error) (response as any).error = error;
  else (response as any).result = result;
  console.log(JSON.stringify(response));
}

// ============ Graceful Shutdown ============
process.on('SIGINT', () => { db.close(); process.exit(0); });
process.on('SIGTERM', () => { db.close(); process.exit(0); });

console.error('[Observer] MCP server ready on stdio');