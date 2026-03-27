#!/usr/bin/env node

/**
 * Integration script - adds MCP observer to OpenCode configuration
 */

const { readFileSync, writeFileSync, existsSync } = require('fs');
const { join } = require('path');

const HOME = process.env.HOME || process.env.USERPROFILE;

// Paths for OpenCode configs
const CONFIG_PATHS = [
  join(HOME, '.config', 'opencode', 'opencode.json'),
  join(HOME, '.config', 'opencode', 'opencode.jsonc'),
  join(HOME, 'Library', 'Application Support', 'Accomplish', 'opencode', 'opencode.json')
];

// Observer paths (where this script lives)
const OBSERVER_DIR = __dirname;
const OBSERVER_PLUGIN_URL = `file://${OBSERVER_DIR}`;
const OBSERVER_MCP_CMD = ['node', join(OBSERVER_DIR, 'dist', 'index.js')];

function updateConfig(configPath) {
  try {
    let config = JSON.parse(readFileSync(configPath, 'utf-8'));

    // Ensure arrays exist
    if (!Array.isArray(config.plugin)) {
      config.plugin = [];
    }
    if (!config.mcp) {
      config.mcp = {};
    }

    // Add plugin if missing
    if (!config.plugin.includes(OBSERVER_PLUGIN_URL)) {
      config.plugin.push(OBSERVER_PLUGIN_URL);
      console.log(`  ✓ Added plugin to: ${configPath}`);
    }

    // Add MCP server if missing
    if (!config.mcp.observer) {
      config.mcp.observer = {
        type: 'local',
        command: OBSERVER_MCP_CMD,
        enabled: true,
        timeout: 60000  // Longer timeout for continuous operation
      };
      console.log(`  ✓ Added MCP server to: ${configPath}`);
    }

    // Write updated config (preserve formatting)
    writeFileSync(configPath, JSON.stringify(config, null, 2) + '\n');
    return true;

  } catch (error) {
    console.error(`  ✗ Failed to update ${configPath}: ${error.message}`);
    return false;
  }
}

// Main
console.log(`
╔═══════════════════════════════════════════════════════════════╗
║         OpenCode MCP Observer - Integration Tool             ║
╚═══════════════════════════════════════════════════════════════╝
`);

// Check if we're in the right directory
if (!existsSync(join(OBSERVER_DIR, 'package.json'))) {
  console.error('Error: This script must be run from the mcp-opencode-observer directory');
  process.exit(1);
}

console.log('Configurations to update:');
CONFIG_PATHS.forEach(p => console.log(`  - ${p}`));
console.log('');

let updated = false;
CONFIG_PATHS.forEach(path => {
  if (existsSync(path)) {
    if (updateConfig(path)) {
      updated = true;
    }
  }
});

if (!updated) {
  console.log('\n⚠️  No OpenCode config files found.');
  console.log('   Make sure OpenCode has been launched at least once to create config files.');
  console.log('\n   Or create manually:');
  console.log(JSON.stringify({
    plugin: [OBSERVER_PLUGIN_URL],
    mcp: { observer: { type: 'local', command: OBSERVER_MCP_CMD, enabled: true } }
  }, null, 2));
  process.exit(1);
}

console.log('\n✅ Integration complete!');
console.log('\nNext steps:');
console.log('1. Restart OpenCode (quit and reopen)');
console.log('2. The observer MCP tools are now available to agents via the MCP system');
console.log('3. WebSocket server running on port 3001 for real-time updates');
console.log('\nTest with:');
console.log(`  echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node "${join(OBSERVER_DIR, 'dist', 'index.js')}"`);
console.log('\nOr from OpenCode, an agent can use:');
console.log('  - get_recent_sessions');
console.log('  - get_session_chat');
console.log('  - search_conversations');
console.log('  - get_tool_output');
console.log('  - get_agent_activity');
console.log('  - get_live_updates (returns WebSocket URL)');

// Create env file for manual runs
const envContent = `# OpenCode Observer environment
export OPENCODE_OBSERVER_DB="${HOME}/.local/share/opencode/opencode.db"
export OPENCODE_OBSERVER_PORT=3000
export OPENCODE_OBSERVER_WS_PORT=3001
`;
writeFileSync(join(OBSERVER_DIR, 'env.sh'), envContent);
console.log(`\n📝 Created env.sh - source it for manual testing:`);
console.log(`   source ${join(OBSERVER_DIR, 'env.sh')}`);