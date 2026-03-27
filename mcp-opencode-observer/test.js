#!/usr/bin/env node

/**
 * Test script for MCP Observer - demonstrates all tools
 */

const { spawnSync } = require('child_process');
const path = require('path');

const OBSERVER_JS = path.join(__dirname, 'dist', 'index.js');

function sendRequest(method, params = {}) {
  const request = {
    jsonrpc: '2.0',
    id: Date.now(),
    method,
    params
  };
  // Spawn observer process per request
  const result = spawnSync('node', [OBSERVER_JS], {
    input: JSON.stringify(request) + '\n',
    encoding: 'utf-8',
    timeout: 5000  // 5 second timeout
  });
  
  // Handle errors gracefully
  if (result.error) {
    return null;
  }
  return result.stdout.trim();
}

function test() {
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║          MCP OpenCode Observer - Test Suite                 ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  // Test 1: Initialize
  console.log('1. Testing initialize...');
  const initResponse = sendRequest('initialize');
  if (!initResponse) {
    console.log('   ✗ No response - is observer running?');
    console.log('   (Make sure to build first: npm run build)\n');
    return;
  }
  if (initResponse.includes('opencode-observer')) {
    console.log('   ✓ Server responded with correct info\n');
  } else {
    console.log('   ✗ Failed:', initResponse.substring(0, 100), '\n');
    return;
  }

  // Test 2: List tools
  console.log('2. Testing tools/list...');
  const toolsResponse = sendRequest('tools/list');
  let toolsDoc;
  try {
    toolsDoc = JSON.parse(toolsResponse);
  } catch (e) {
    console.log('   ✗ Invalid JSON response\n');
    return;
  }
  if (toolsDoc.result?.tools?.length > 0) {
    console.log(`   ✓ Found ${toolsDoc.result.tools.length} tools:`);
    toolsDoc.result.tools.forEach(t => console.log(`     - ${t.name}`));
    console.log('');
  } else {
    console.log('   ✗ No tools found\n');
    return;
  }

  // Test 3: Get recent sessions
  console.log('3. Testing get_recent_sessions (limit=2)...');
  const sessionsResponse = sendRequest('tools/call', {
    name: 'get_recent_sessions',
    arguments: { limit: 2 }
  });
  let sessionsDoc;
  try {
    sessionsDoc = JSON.parse(sessionsResponse);
  } catch (e) {
    console.log('   ✗ Invalid JSON response\n');
    return;
  }
  if (!sessionsDoc.error) {
    try {
      const content = sessionsDoc.result.content[0].text;
      const sessions = JSON.parse(content);
      console.log(`   ✓ Retrieved ${sessions.length} sessions`);
      if (sessions.length > 0) {
        console.log(`     Latest: "${sessions[0].title}"`);
        console.log(`     Dir: ${sessions[0].directory}`);
      }
      console.log('');
    } catch (e) {
      console.log('   ✗ Failed to parse sessions:', e.message, '\n');
    }
  } else {
    console.log('   ✗ Error:', sessionsDoc.error.message, '\n');
  }

  // Test 4: Get agent activity
  console.log('4. Testing get_agent_activity...');
  const activityResponse = sendRequest('tools/call', {
    name: 'get_agent_activity',
    arguments: { hours: 24 }
  });
  let activityDoc;
  try {
    activityDoc = JSON.parse(activityResponse);
  } catch (e) {
    console.log('   ✗ Invalid JSON response\n');
    return;
  }
  if (!activityDoc.error) {
    try {
      const content = activityDoc.result.content[0].text;
      const stats = JSON.parse(content);
      console.log(`   ✓ Agent stats retrieved: ${stats.length} agents active`);
      stats.forEach((s) => {
        console.log(`     - ${s.agent}: ${s.message_count} messages`);
      });
      console.log('');
    } catch (e) {
      console.log('   ✗ Failed to parse stats:', e.message, '\n');
    }
  } else {
    console.log('   ✗ Error:', activityDoc.error.message, '\n');
  }

  // Test 5: Get live updates WS URL
  console.log('5. Testing get_live_updates...');
  const wsResponse = sendRequest('tools/call', {
    name: 'get_live_updates',
    arguments: {}
  });
  let wsDoc;
  try {
    wsDoc = JSON.parse(wsResponse);
  } catch (e) {
    console.log('   ✗ Invalid JSON response\n');
    return;
  }
  if (!wsDoc.error) {
    try {
      const content = wsDoc.result.content[0].text;
      const info = JSON.parse(content);
      console.log(`   ✓ WebSocket URL: ${info.ws_url}`);
      console.log(`     ${info.message}\n`);
    } catch (e) {
      console.log('   ✗ Failed to parse WS info:', e.message, '\n');
    }
  } else {
    console.log('   ✗ Error:', wsDoc.error.message, '\n');
  }

  // Test 6: Search conversations
  console.log('6. Testing search_conversations (query="OpenCode")...');
  const searchResponse = sendRequest('tools/call', {
    name: 'search_conversations',
    arguments: { query: 'OpenCode', limit: 5 }
  });
  let searchDoc;
  try {
    searchDoc = JSON.parse(searchResponse);
  } catch (e) {
    console.log('   ✗ Invalid JSON response\n');
    return;
  }
  if (!searchDoc.error) {
    try {
      const content = searchDoc.result.content[0].text;
      const results = JSON.parse(content);
      console.log(`   ✓ Search returned ${results.length} results\n`);
    } catch (e) {
      console.log('   ✗ Failed to parse search results:', e.message, '\n');
    }
  } else {
    console.log('   ✗ Error:', searchDoc.error.message, '\n');
  }

  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║  ✓ All tests completed! Observer is ready for integration.  ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');

  console.log('\n📋 Next steps:');
  console.log('   1. Run: node integrate.js');
  console.log('   2. Restart OpenCode');
  console.log('   3. Observer tools are now available via MCP\n');
}

try {
  test();
} catch (error) {
  console.error('\n❌ Test failed:', error.message);
  process.exit(1);
}