#!/usr/bin/env node

/**
 * Setup script for integrating MCP Observer with OpenCode
 * Called by the main setup.sh — not meant to be run standalone.
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { homedir } from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function expandHome(p) {
  if (p.startsWith('~/') || p === '~') {
    return join(homedir(), p.slice(2));
  }
  return p;
}

const CONFIG_PATHS = [
  expandHome('~/.config/opencode/opencode.json'),
  expandHome('~/.config/opencode/opencode.jsonc'),
  join(homedir(), 'Library', 'Application Support', 'Accomplish', 'opencode', 'opencode.json')
];

const OBSERVER_PLUGIN_DIR = expandHome('~/.local/share/opencode/storage/plugin/opencode-observer');

function updateConfig(configPath) {
  try {
    const content = readFileSync(configPath, 'utf-8');
    const parsed = JSON.parse(content);

    if (!parsed.plugin) {
      parsed.plugin = [];
    }
    const pluginUrl = `file://${OBSERVER_PLUGIN_DIR}`;
    if (!parsed.plugin.includes(pluginUrl)) {
      parsed.plugin.push(pluginUrl);
    }

    if (!parsed.mcp) {
      parsed.mcp = {};
    }

    if (!parsed.mcp.observer) {
      parsed.mcp.observer = {
        type: 'local',
        command: [
          'node',
          expandHome('~/.local/share/opencode/bin/opencode-observer-mcp')
        ],
        enabled: true,
        timeout: 30000
      };
    }

    writeFileSync(configPath, JSON.stringify(parsed, null, 2) + '\n');
    console.log(`[OK] Updated config: ${configPath}`);
    return true;
  } catch (error) {
    console.error(`[ERROR] Failed to update ${configPath}:`, error.message);
    return false;
  }
}

function ensurePluginInstalled() {
  if (!existsSync(OBSERVER_PLUGIN_DIR)) {
    console.error('[ERROR] Plugin not installed. Run: npm run build && npm run install');
    return false;
  }
  return true;
}

// Main
console.log('=== OpenCode MCP Observer Setup ===\n');

if (!ensurePluginInstalled()) {
  process.exit(1);
}

let updated = false;
for (const configPath of CONFIG_PATHS) {
  if (existsSync(configPath)) {
    if (updateConfig(configPath)) {
      updated = true;
    }
  }
}

if (!updated) {
  console.log('\nNo config files found. OpenCode may need to run first to create them.');
  console.log('After OpenCode runs, execute this script again or manually add:');
  console.log(`
  "plugin": ["file://${OBSERVER_PLUGIN_DIR}"],
  "mcp": {
    "observer": {
      "type": "local",
      "command": ["node", "${expandHome('~/.local/share/opencode/bin/opencode-observer-mcp')}"],
      "enabled": true
    }
  }
  `);
} else {
  console.log('\n[SUCCESS] OpenCode is now configured with MCP Observer!');
  console.log('\nAvailable tools:');
  console.log('  - get_recent_sessions');
  console.log('  - get_session_chat');
  console.log('  - search_chats');
  console.log('  - get_tool_execution');
  console.log('\nRestart OpenCode to load the plugin.');
}
