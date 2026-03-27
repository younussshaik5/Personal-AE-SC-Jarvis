.PHONY: build install clean test

build:
	@echo "Building TypeScript..."
	npm run build

install:
	@echo "Installing MCP observer as OpenCode plugin..."
	@mkdir -p ~/.local/share/opencode/storage/plugin/opencode-observer
	@cp -r . ~/.local/share/opencode/storage/plugin/opencode-observer
	@echo "Built files copied to plugin storage"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit config/mcp-observer.json with correct paths if needed"
	@echo "2. Add to OpenCode config:"
	@echo "   'plugin': ['file://${HOME}/.local/share/opencode/storage/plugin/opencode-observer']"
	@echo ""
	@echo "OR run as standalone MCP server:"
	@echo "  node dist/index.js"

clean:
	@rm -rf dist
	@echo "Cleaned"

test: build
	@echo "Testing database connection..."
	@node -e "const db = require('./dist/db').default; console.log('DB test OK')"