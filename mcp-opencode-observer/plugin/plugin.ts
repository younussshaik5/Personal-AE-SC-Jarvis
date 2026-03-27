// @ts-ignore
import { Plugin } from '@opencode-ai/plugin';
// @ts-ignore
import { tool } from '@opencode-ai/plugin';
import { z } from 'zod';
import { createRequire } from 'node:module';
const _require = createRequire(import.meta.url);

// This is the actual plugin entry point for OpenCode
// It exposes tools that access OpenCode data

export default Plugin({
  name: 'opencode-observer',
  version: '1.0.0',
  description: 'Query OpenCode and Claude sessions and conversations',

  async onInstall() {
    console.log('[Observer Plugin] Installed');
  },

  async onStart() {
    console.log('[Observer Plugin] Started');
    // Could start background monitoring here
  },

  tools: [
    tool({
      name: 'get_recent_sessions',
      description: 'Get recent OpenCode sessions from the database',
      args: {
        limit: z.number().min(1).max(100).default(10),
        workspace: z.string().optional()
      },
      async execute(args: any, context: any) {
        // Query the local database
        const dbPath = process.env.OPENCODE_DB_PATH || '~/.local/share/opencode/opencode.db';
        const db = _require('better-sqlite3')(dbPath);

        let query = 'SELECT id, title, directory, time_created FROM session';
        const params = [];

        if (args.workspace) {
          query += ' WHERE directory LIKE ?';
          params.push(`%${args.workspace}%`);
        }

        query += ' ORDER BY time_created DESC LIMIT ?';
        params.push(args.limit);

        const sessions = db.prepare(query).all(...params);
        db.close();

        return JSON.stringify(sessions, null, 2);
      }
    }),

    tool({
      name: 'get_session_chat',
      description: 'Get full conversation for a session',
      args: {
        session_id: z.string().describe('Session ID')
      },
      async execute(args: any) {
        const dbPath = process.env.OPENCODE_DB_PATH || '~/.local/share/opencode/opencode.db';
        const db = _require('better-sqlite3')(dbPath);

        const messages = db.prepare(`
          SELECT m.id, m.time_created, json_extract(m.data, '$.role') as role,
                 json_extract(m.data, '$.agent') as agent,
                 json_extract(m.data, '$.model.modelID') as model,
                 m.data as full_data
          FROM message m
          WHERE m.session_id = ?
          ORDER BY m.time_created ASC
          LIMIT 200
        `).all(args.session_id);

        db.close();

        return JSON.stringify(messages.map(m => ({
          id: m.id,
          time: new Date(m.time_created).toISOString(),
          role: m.role,
          agent: m.agent,
          model: m.model,
          content: JSON.parse(m.full_data)
        })), null, 2);
      }
    }),

    tool({
      name: 'search_chats',
      description: 'Search across all conversations',
      args: {
        query: z.string(),
        limit: z.number().max(100).default(20)
      },
      async execute(args: any) {
        const dbPath = process.env.OPENCODE_DB_PATH || '~/.local/share/opencode/opencode.db';
        const db = _require('better-sqlite3')(dbPath);

        // Get recent messages to search (performance optimization)
        const recent = db.prepare(`
          SELECT m.id, m.session_id, m.time_created, m.data
          FROM message m
          ORDER BY m.time_created DESC
          LIMIT 1000
        `).all();

        db.close();

        const lowerQuery = args.query.toLowerCase();
        const results = recent.filter((m: any) => {
          try {
            const data = JSON.parse(m.data);
            return JSON.stringify(data).toLowerCase().includes(lowerQuery);
          } catch {
            return false;
          }
        }).slice(0, args.limit);

        return JSON.stringify(results, null, 2);
      }
    }),

    tool({
      name: 'get_tool_execution',
      description: 'Get output from a tool execution',
      args: {
        tool_id: z.string()
      },
      async execute(args: any) {
        const _fs = _require('fs');
        const _path = _require('path');
        const toolOutputDir = process.env.OPENCODE_TOOL_OUTPUT_DIR ||
          '~/.local/share/opencode/tool-output';
        const filePath = _path.join(toolOutputDir, `tool_${args.tool_id}`);

        if (!_fs.existsSync(filePath)) {
          return `Tool output not found: ${args.tool_id}`;
        }

        return _fs.readFileSync(filePath, 'utf-8');
      }
    })
  ]
});