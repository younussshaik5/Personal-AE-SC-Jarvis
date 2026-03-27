#!/usr/bin/env node

/**
 * Setup script for integrating MCP Observer with OpenCode
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CONFIG_PATHS = [
  '~/.config/opencode/opencode.json',
  '~/.config/opencode/opencode.jsonc',
  '~/Library/Application Support/Accomplish/opencode/opencode.json'
];

const OBSERVER_PLUGIN_URL = 'file://~/.local/share/opencode/storage/plugin/opencode-observer';

function updateConfig(configPath: string): boolean {
  try {
    const content = readFileSync(configPath, 'utf-8');
    const parsed = JSON.parse(content);

    // Add plugin if not present
    if (!parsed.plugin) {
      parsed.plugin = [];
    }
    if (!parsed.plugin.includes(OBSERVER_PLUGIN_URL)) {
      parsed.plugin.push(OBSERVER_PLUGIN_URL);
    }

    // Ensure mcp section exists (optional - can run standalone)
    if (!parsed.mcp) {
      parsed.mcp = {};
    }

    // Add as MCP server too (optional)
    if (!parsed.mcp.observer) {
      parsed.mcp.observer = {
        type: 'local',
        command: [
          'node',
          '~/.local/share/opencode/bin/opencode-observer-mcp'
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

function ensurePluginInstalled(): boolean {
  const pluginDir = '~/.local/share/opencode/storage/plugin/opencode-observer';
  if (!existsSync(pluginDir)) {
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
  "plugin": ["${OBSERVER_PLUGIN_URL}"],
  "mcp": {
    "observer": {
      "type": "local",
      "command": ["node", "~/.local/share/opencode/bin/opencode-observer-mcp"],
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