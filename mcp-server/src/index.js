#!/usr/bin/env node
/**
 * JARVIS v3 MCP Server - Portable, no hard paths
 * Provides tools for Claude Desktop to interact with JARVIS
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Path resolution - uses environment variables, never hardcoded
function getJarvisRoot() {
  return process.env.JARVIS_ROOT || process.env.JARVIS_HOME || path.join(process.env.HOME, 'JARVIS');
}

function getWorkspaceRoot() {
  return process.env.WORKSPACE_ROOT || process.cwd();
}

function getAccountsDir() {
  const workspace = getWorkspaceRoot();
  const localAccounts = path.join(workspace, 'ACCOUNTS');
  // If local ACCOUNTS exists, use it; otherwise fall back to JARVIS_ROOT/ACCOUNTS
  if (fs.existsSync(localAccounts)) {
    return localAccounts;
  }
  return path.join(getJarvisRoot(), 'ACCOUNTS');
}

// Tool implementations
async function callTool(name, args) {
  const accountsDir = getAccountsDir();

  switch (name) {
    case 'jarvis_list_accounts': {
      try {
        const accounts = execSync(`find "${accountsDir}" -maxdepth 1 -type d ! -name ".*" ! -name "_template" -printf "%f\\n" 2>/dev/null`)
          .toString()
          .trim()
          .split('\n')
          .filter(Boolean);
        return { accounts };
      } catch (e) {
        return { accounts: [] };
      }
    }

    case 'jarvis_find_account': {
      const query = (args.name || '').toLowerCase();
      const allAccounts = args.allAccounts || [];
      const matches = allAccounts.filter(acc => acc.toLowerCase().includes(query));
      const best = matches[0] || null;
      return { account: best, confidence: best ? 0.8 : 0, alternatives: matches.slice(1, 4) };
    }

    case 'jarvis_get_account': {
      const accountName = args.account;
      const accountPath = path.join(accountsDir, accountName);
      try {
        const lookupPath = path.join(accountPath, 'lookup.md');
        const summaryPath = path.join(accountPath, 'summary.md');
        const stagePath = path.join(accountPath, 'deal_stage.json');

        const lookup = fs.existsSync(lookupPath) ? fs.readFileSync(lookupPath, 'utf8') : '';
        const summary = fs.existsSync(summaryPath) ? fs.readFileSync(summaryPath, 'utf8') : '';
        const dealStage = fs.existsSync(stagePath) ? JSON.parse(fs.readFileSync(stagePath, 'utf8')) : {};

        return {
          account: accountName,
          lookup,
          summary,
          dealStage,
          path: accountPath
        };
      } catch (e) {
        return { error: `Account not found: ${accountName}` };
      }
    }

    case 'jarvis_save_conversation': {
      const convAccount = args.account;
      const convDir = path.join(accountsDir, convAccount, 'INTEL');
      const convPath = path.join(convDir, 'conversations.jsonl');

      const convEntry = {
        role: args.role || 'user',
        content: args.content,
        timestamp: new Date().toISOString(),
        model: args.model || 'unknown'
      };

      try {
        if (!fs.existsSync(convDir)) {
          fs.mkdirSync(convDir, { recursive: true });
        }
        fs.appendFileSync(convPath, JSON.stringify(convEntry) + '\n');
        return { saved: true, path: convPath };
      } catch (e) {
        return { error: `Failed to save: ${e.message}` };
      }
    }

    default:
      return { error: `Unknown tool: ${name}` };
  }
}

async function main() {
  const server = new Server(
    { name: 'jarvis-mcp', version: '3.0.0' },
    { capabilities: { tools: {} } }
  );

  // Use 'request' handler for all tool calls
  server.on('request', async (request) => {
    const { method, params } = request;
    if (method.startsWith('tools/')) {
      if (method === 'tools/list') {
        const tools = [
          {
            name: 'jarvis_list_accounts',
            description: 'List all accounts in JARVIS',
            inputSchema: { type: 'object', properties: {} }
          },
          {
            name: 'jarvis_find_account',
            description: 'Find account by fuzzy name match',
            inputSchema: {
              type: 'object',
              properties: {
                name: { type: 'string', description: 'Company name to search' },
                allAccounts: { type: 'array', items: { type: 'string' } }
              },
              required: ['name']
            }
          },
          {
            name: 'jarvis_get_account',
            description: 'Get full account dossier',
            inputSchema: {
              type: 'object',
              properties: {
                account: { type: 'string', description: 'Account folder name' }
              },
              required: ['account']
            }
          },
          {
            name: 'jarvis_save_conversation',
            description: 'Save conversation to JARVIS brain',
            inputSchema: {
              type: 'object',
              properties: {
                account: { type: 'string' },
                role: { type: 'string', enum: ['user', 'assistant'] },
                content: { type: 'string' },
                model: { type: 'string' }
              },
              required: ['account', 'content']
            }
          }
        ];
        return { tools };
      } else if (method === 'tools/call') {
        const { name, arguments: args } = params;
        const result = await callTool(name, args);
        return { content: [{ type: 'text', text: JSON.stringify(result) }] };
      }
    }
    // Unknown method
    return { error: `Unknown method: ${method}` };
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('JARVIS MCP Server running (portable, no hard paths)');
}

main().catch(err => {
  console.error('MCP Server error:', err);
  process.exit(1);
});