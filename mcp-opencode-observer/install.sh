#!/usr/bin/env bash

# Install and configure MCP OpenCode Observer

set -e

echo "=== MCP OpenCode Observer Installer ==="
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Check OpenCode config location
OPENCODE_CONFIG="${HOME}/.config/opencode/opencode.jsonc"
if [ ! -f "$OPENCODE_CONFIG" ]; then
    echo "Warning: OpenCode config not found at $OPENCODE_CONFIG"
    echo "It will be created when OpenCode runs first."
fi

# Install dependencies
echo "[1/5] Installing dependencies..."
npm install

# Build
echo "[2/5] Building TypeScript..."
npm run build

# Determine install paths
INSTALL_DIR="${HOME}/.local/share/opencode/storage/plugin/opencode-observer"
echo "[3/5] Installing to: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r config dist package.json src "$INSTALL_DIR/" 2>/dev/null || true

# Update OpenCode config
echo "[4/5] Updating OpenCode configuration..."
if [ -f "$OPENCODE_CONFIG" ]; then
    # Add plugin to config using jq (if available)
    if command -v jq &> /dev/null; then
        jq '.plugin += ["file://'"${HOME}"'/.local/share/opencode/storage/plugin/opencode-observer"]' \
            "$OPENCODE_CONFIG" > "${OPENCODE_CONFIG}.tmp"
        mv "${OPENCODE_CONFIG}.tmp" "$OPENCODE_CONFIG"
        echo "  Plugin added to OpenCode config"
    else
        echo "  Manually add to $OPENCODE_CONFIG:"
        echo '  "plugin": ["file://'"${HOME}"'/.local/share/opencode/storage/plugin/opencode-observer"]'
    fi
else
    echo "  OpenCode config not found. Please add manually after first run."
fi

# Create standalone MCP script
echo "[5/5] Creating standalone MCP server script..."
cp dist/index.js "${HOME}/.local/share/opencode/bin/opencode-observer-mcp"
chmod +x "${HOME}/.local/share/opencode/bin/opencode-observer-mcp"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Integration options:"
echo ""
echo "Option A - Run as MCP server in OpenCode:"
echo "  Add to ~/.config/opencode/opencode.jsonc:"
echo '    "plugin": ["file://'"${HOME}"'/.local/share/opencode/storage/plugin/opencode-observer"]'
echo ""
echo "Option B - Run standalone (stdio):"
echo "  node ${HOME}/.local/share/opencode/bin/opencode-observer-mcp"
echo ""
echo "Option C - Add to OpenCode mcp config:"
echo "  Add to ~/.config/opencode/opencode.jsonc mcp section:"
echo '    "observer": {'
echo '      "type": "local",'
echo '      "command": ["node", "'"${HOME}"'/.local/share/opencode/bin/opencode-observer-mcp"],'
echo '      "enabled": true'
echo '    }'
echo ""
echo "Tools available:"
echo "  - get_recent_sessions"
echo "  - get_session (full messages)"
echo "  - search_conversations"
echo "  - get_agent_activity"
echo "  - get_tool_output"
echo "  - get_live_ws_url (WebSocket)"