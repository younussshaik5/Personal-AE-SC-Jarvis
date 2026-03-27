#!/bin/bash
# Quick setup: adds observer to OpenCode config and starts it

CONFIG_PATHS=(
  "$HOME/.config/opencode/opencode.jsonc"
  "$HOME/.local/share/opencode/opencode.json"
  "$HOME/Library/Application Support/Accomplish/opencode/opencode.json"
)

# Find config
CONFIG_PATH=""
for p in "${CONFIG_PATHS[@]}"; do
  if [ -f "$p" ]; then
    CONFIG_PATH="$p"
    break
  fi
done

if [ -z "$CONFIG_PATH" ]; then
  echo "❌ OpenCode config not found. Checked:"
  printf '   %s\n' "${CONFIG_PATHS[@]}"
  exit 1
fi

echo "✅ Found config: $CONFIG_PATH"

# Insert observer MCP entry (jq)
OBSERVER_CMD="node /path/to/your/workspace/mcp-opencode-observer/dist/index.js"
TMP_FILE=$(mktemp)

jq '.mcp.observer = {
  "type": "local",
  "command": ["node", "'"$OBSERVER_CMD"'"],
  "enabled": true,
  "timeout": 30000
}' "$CONFIG_PATH" > "$TMP_FILE" && mv "$TMP_FILE" "$CONFIG_PATH"

echo "✅ MCP observer added to config."
echo "🔄 Restart OpenCode to activate autonomous mode."