#!/usr/bin/env bash

# Quick integration setup for MCP Observer

set -e

echo "=== MCP Observer Setup ==="

# Paths
PLUGIN_SRC="${PWD}"
PLUGIN_DEST="${HOME}/.local/share/opencode/storage/plugin/opencode-observer"
BIN_DEST="${HOME}/.local/share/opencode/bin/opencode-observer-mcp"

# Build
echo "[1] Building..."
npm run build

# Install plugin
echo "[2] Installing plugin to ${PLUGIN_DEST}..."
rm -rf "${PLUGIN_DEST}"
mkdir -p "${PLUGIN_DEST}"
cp -r config dist src/plugin.ts package.json "${PLUGIN_DEST}/" 2>/dev/null || true

# Install binary
echo "[3] Installing MCP server binary..."
cp dist/index.js "${BIN_DEST}"
chmod +x "${BIN_DEST}"

# Config
echo "[4] Updating OpenCode configuration..."
OBSERVER_CMD="[\"node\",\"${BIN_DEST}\"]"
OBSERVER_PLUGIN="file://${PLUGIN_DEST}"

CONFIG_FILES=(
  "${HOME}/.config/opencode/opencode.json"
  "${HOME}/.config/opencode/opencode.jsonc"
  "${HOME}/Library/Application Support/Accomplish/opencode/opencode.json"
)

for cfg in "${CONFIG_FILES[@]}"; do
  if [ -f "$cfg" ]; then
    echo "  Updating $cfg"
    if command -v jq &> /dev/null; then
      # Add MCP observer server
      jq --arg cmd "$OBSERVER_CMD" '
        .mcp.observer = {type: "local", command: ($cmd | fromjson), enabled: true}
        | .plugin += ["'"${OBSERVER_PLUGIN}"'"]
      ' "$cfg" > "${cfg}.tmp" && mv "${cfg}.tmp" "$cfg"
    else
      echo "    (jq not found - edit manually to add observer MCP)"
    fi
  fi
done

echo ""
echo "=== Setup Complete ==="
echo ""
echo "1. Restart OpenCode"
echo "2. The observer MCP tools are now available:"
echo "   - get_recent_sessions"
echo "   - get_session_chat"
echo "   - search_conversations"
echo "   - get_tool_output"
echo "   - get_agent_activity"
echo "   - get_live_updates"
echo ""
echo "3. To test, run:"
echo "   echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}' | node ${BIN_DEST}"