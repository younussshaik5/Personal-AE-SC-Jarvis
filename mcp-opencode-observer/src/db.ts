import Database from 'better-sqlite3';
import { readFileSync, existsSync, watch, statSync, readdirSync } from 'fs';
import { join, basename } from 'path';
import { EventEmitter } from 'events';

export interface OpenCodeSession {
  id: string;
  project_id: string;
  parent_id: string | null;
  slug: string;
  directory: string;
  title: string;
  version: string;
  share_url: string | null;
  summary_additions: number;
  summary_deletions: number;
  summary_files: number;
  summary_diffs: string | null;
  revert: string | null;
  permission: string | null;
  time_created: number;
  time_updated: number;
  time_compacting: number | null;
  time_archived: number | null;
  workspace_id: string;
}

export interface OpenCodeMessage {
  id: string;
  session_id: string;
  time_created: number;
  time_updated: number;
  data: {
    role: 'user' | 'assistant' | 'system';
    time: { created: number; completed?: number };
    summary?: { diffs: any[] };
    agent?: string;
    model?: { providerID: string; modelID: string };
    path?: { cwd: string; root: string };
    cost?: number;
    tokens?: { input: number; output: number; reasoning: number; cache?: { read: number; write: number } };
    error?: any;
    parentID?: string;
  };
}

export class OpenCodeDB extends EventEmitter {
  private db: Database.Database;

  constructor(dbPath: string) {
    super();
    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
  }

  async getSessions(limit: number = 10, workspace?: string): Promise<any[]> {
    let query = `SELECT * FROM session`;
    const params: any[] = [];

    if (workspace) {
      query += ' WHERE directory LIKE ?';
      params.push(`%${workspace}%`);
    }

    query += ' ORDER BY time_created DESC LIMIT ?';
    params.push(limit);

    return this.db.prepare(query).all(...params);
  }

  async getSession(sessionId: string): Promise<any | null> {
    return this.db.prepare('SELECT * FROM session WHERE id = ?').get(sessionId);
  }

  async getSessionMessages(sessionId: string, limit?: number): Promise<any[]> {
    let query = `SELECT id, session_id, time_created, data FROM message
                 WHERE session_id = ? ORDER BY time_created ASC`;
    const params: any[] = [sessionId];

    if (limit) {
      query += ' LIMIT ?';
      params.push(limit);
    }

    const rows: any[] = this.db.prepare(query).all(...params);
    return rows.map(row => ({
      ...row,
      data: typeof row.data === 'string' ? JSON.parse(row.data) : row.data
    }));
  }

  async getRecentMessages(limit: number = 50, agent?: string): Promise<any[]> {
    let query = `SELECT id, session_id, time_created, data FROM message`;
    const params: any[] = [];

    if (agent) {
      query += ' WHERE json_extract(data, "$.agent") = ?';
      params.push(agent);
    }

    query += ' ORDER BY time_created DESC LIMIT ?';
    params.push(limit);

    const rows: any[] = this.db.prepare(query).all(...params);
    return rows.map(row => ({
      ...row,
      data: typeof row.data === 'string' ? JSON.parse(row.data) : row.data
    }));
  }

  async getMessageFromTime(after: number, workspaceRoot?: string): Promise<any[]> {
    const params: any[] = [];
    let query = `SELECT m.id, m.session_id, m.time_created, m.data FROM message m`;

    if (workspaceRoot) {
      query += `
        JOIN session s ON m.session_id = s.id
        WHERE m.time_created > ? AND (s.directory = ? OR s.directory LIKE ?)
      `;
      params.push(after, workspaceRoot, workspaceRoot + '/%');
    } else {
      query += ` WHERE m.time_created > ?`;
      params.push(after);
    }

    query += ` ORDER BY m.time_created ASC`;

    const rows: any[] = this.db.prepare(query).all(...params);

    return rows.map(row => ({
      ...row,
      data: typeof row.data === 'string' ? JSON.parse(row.data) : row.data
    }));
  }

  async searchMessages(query: string, limit: number = 20): Promise<OpenCodeMessage[]> {
    // Get recent messages to search (limit scope for performance)
    const recent = await this.getRecentMessages(1000);

    const lowerQuery = query.toLowerCase();
    return recent.filter(msg =>
      JSON.stringify(msg.data).toLowerCase().includes(lowerQuery)
    ).slice(0, limit);
  }

  async getAgentStats(hours: number = 24): Promise<any[]> {
    const cutoff = Date.now() - (hours * 60 * 60 * 1000);
    return this.db.prepare(`
      SELECT
        json_extract(data, '$.agent') as agent,
        COUNT(*) as message_count,
        MIN(time_created) as first_seen,
        MAX(time_created) as last_seen
      FROM message
      WHERE time_created > ?
      GROUP BY agent
    `).all(cutoff);
  }

  async getToolOutput(toolId: string, toolOutputDir: string): Promise<string | null> {
    const filePath = join(toolOutputDir, `tool_${toolId}`);
    return existsSync(filePath) ? readFileSync(filePath, 'utf-8') : null;
  }

  startPolling(intervalMs: number, callback: (messages: OpenCodeMessage[]) => void, workspaceRoot?: string): void {
    let lastPoll = Date.now();

    setInterval(async () => {
      try {
        const newMessages = await this.getMessageFromTime(lastPoll, workspaceRoot);
        if (newMessages.length > 0) {
          lastPoll = newMessages[newMessages.length - 1].time_created;
          callback(newMessages);
        }
      } catch (error) {
        this.emit('error', error);
      }
    }, intervalMs);
  }

  close(): void {
    this.db.close();
  }
}

// Log file watcher for additional context
export class LogWatcher extends EventEmitter {
  private logDir: string;
  private currentFile: string | null = null;
  private lastPosition: number = 0;

  constructor(logDir: string) {
    super();
    this.logDir = logDir;

    // Watch for new log files
    watch(logDir, { recursive: false }, (eventType, filename) => {
      if (filename && filename.endsWith('.log')) {
        this.currentFile = join(logDir, filename);
        this.tailNewFile();
      }
    });

    // Start with most recent log file
    this.initializeCurrentFile();
  }

  private initializeCurrentFile() {
    try {
      const files = this.getLogFiles().sort().reverse();
      if (files.length > 0) {
        this.currentFile = join(this.logDir, files[0]);
        this.lastPosition = 0; // Skip existing content, only tail new
      }
    } catch (error) {
      this.emit('error', error);
    }
  }

  private getLogFiles(): string[] {
    if (!existsSync(this.logDir)) return [];
    try {
      return readdirSync(this.logDir)
        .filter(f => f.endsWith('.log'));
    } catch {
      return [];
    }
  }

  private tailNewFile() {
    if (!this.currentFile || !existsSync(this.currentFile)) return;

    const stats = statSync(this.currentFile);
    this.lastPosition = stats.size;

    // Watch current log file for changes
    watch(this.currentFile, (eventType) => {
      if (eventType === 'change') {
        this.readNewLines();
      }
    });
  }

  private readNewLines() {
    if (!this.currentFile || !existsSync(this.currentFile)) return;

    try {
      const content = readFileSync(this.currentFile, 'utf-8');
      const lines = content.split('\n');

      if (lines.length > 0) {
        const newContent = lines.slice(
          Math.floor(this.lastPosition / 100) // Approximate line start
        ).join('\n');

        if (newContent.trim()) {
          this.emit('log', {
            file: basename(this.currentFile),
            content: newContent,
            timestamp: Date.now()
          });
        }
      }

      this.lastPosition = content.length;
    } catch (error) {
      this.emit('error', error);
    }
  }

  stop(): void {
    // Cleanup if needed
  }
}