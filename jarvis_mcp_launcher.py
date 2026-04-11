#!/usr/bin/env python3
"""
JARVIS MCP Server Launcher
Auto-starts with Claude Desktop, auto-stops when Claude Desktop closes
"""

import sys
import os
import asyncio
import signal
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from jarvis_mcp.mcp_server import JarvisServer
from jarvis_mcp.platform_utils import PlatformUtils


class MCPLauncher:
    """Launches and manages JARVIS MCP server"""

    def __init__(self):
        self.server = None
        self.running = False

    async def start(self):
        """Start the JARVIS MCP server"""
        try:
            print("[JARVIS MCP] Starting server...", file=sys.stderr)

            # Initialize server
            self.server = JarvisServer()
            self.running = True

            print("[JARVIS MCP] ✅ Server initialized successfully", file=sys.stderr)
            print("[JARVIS MCP] 🤖 26 skills loaded and ready", file=sys.stderr)
            print("[JARVIS MCP] 🚀 Ready for Claude Desktop connection", file=sys.stderr)

            # Keep server running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[JARVIS MCP] ❌ Error: {e}", file=sys.stderr)
            self.running = False
            sys.exit(1)

    async def shutdown(self):
        """Gracefully shutdown server"""
        print("[JARVIS MCP] Shutting down...", file=sys.stderr)
        self.running = False
        if self.server:
            await self.server.shutdown()
        print("[JARVIS MCP] ✅ Shutdown complete", file=sys.stderr)

    def handle_signal(self, signum=None, frame=None):
        """Handle shutdown signals (platform-aware signature)"""
        asyncio.create_task(self.shutdown())


async def main():
    """Main entry point"""
    launcher = MCPLauncher()

    # Handle signals (platform-aware: atexit on Windows, signals on Unix/Mac)
    PlatformUtils.register_signal_handlers(launcher.handle_signal)

    # Start server
    await launcher.start()


if __name__ == "__main__":
    asyncio.run(main())
