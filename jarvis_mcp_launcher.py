#!/usr/bin/env python3
"""
JARVIS MCP Server Launcher
Auto-starts with Claude Desktop, auto-stops when Claude Desktop closes
"""

import sys
import os
import asyncio
import signal
import logging
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from jarvis_mcp.mcp_server import JarvisServer
from jarvis_mcp.platform_utils import PlatformUtils

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[JARVIS MCP] %(message)s",
    stream=sys.stderr
)
log = logging.getLogger(__name__)


class MCPLauncher:
    """Launches and manages JARVIS MCP server"""

    def __init__(self):
        self.server = None
        self.running = False

    async def start(self):
        """Start the JARVIS MCP server"""
        try:
            log.info("Starting server…")

            # Initialize server
            self.server = JarvisServer()
            self.running = True

            log.info(f"✅ Server initialized successfully")
            log.info(f"🤖 Skills loaded and ready")
            log.info(f"🚀 Ready for Claude Desktop connection")

            # Keep server running
            while self.running:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            log.info("Server startup cancelled")
            self.running = False
        except Exception as e:
            log.error(f"❌ Error: {type(e).__name__}: {e}", exc_info=True)
            self.running = False
            sys.exit(1)

    async def shutdown(self):
        """Gracefully shutdown server"""
        log.info("Shutting down…")
        self.running = False
        if self.server:
            try:
                await self.server.shutdown()
            except Exception as e:
                log.error(f"Error during shutdown: {type(e).__name__}: {e}", exc_info=True)
        log.info("✅ Shutdown complete")

    def handle_signal(self, signum=None, frame=None):
        """Handle shutdown signals (platform-aware signature)"""
        asyncio.create_task(self.shutdown())


async def main():
    """Main entry point"""
    launcher = MCPLauncher()

    # Handle signals (platform-aware: atexit on Windows, signals on Unix/Mac)
    PlatformUtils.register_signal_handlers(launcher.handle_signal)

    # Start server
    try:
        await launcher.start()
    except KeyboardInterrupt:
        log.info("Interrupted by user")
    except Exception as e:
        log.error(f"Fatal error: {type(e).__name__}: {e}", exc_info=True)
        raise
    finally:
        await launcher.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("JARVIS MCP launcher interrupted")
        sys.exit(0)
    except Exception as e:
        log.error(f"JARVIS MCP launcher fatal error: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)
