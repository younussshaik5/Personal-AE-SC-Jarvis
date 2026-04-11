#!/usr/bin/env python3
"""
JARVIS MCP Server Launcher
Auto-starts with Claude Desktop, auto-stops when Claude Desktop closes.

Lifecycle:
  Claude Desktop opens  → JARVIS starts (all skills, file watchers, CRM, etc.)
  Claude Desktop closes → JARVIS stops (clean shutdown, all processes terminated)
"""

import sys
import os
import asyncio
import atexit
import logging
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from jarvis_mcp.platform_utils import PlatformUtils

# Setup logging before anything else
logging.basicConfig(
    level=logging.DEBUG,
    format="[JARVIS MCP] %(levelname)s | %(message)s",
    stream=sys.stderr
)
log = logging.getLogger(__name__)


class MCPLauncher:
    """Launches and manages JARVIS MCP server with lifecycle management"""

    def __init__(self):
        self.server = None
        self.running = False
        self.startup_complete = False
        log.debug("MCPLauncher initialized")

    def _check_environment(self):
        """Verify JARVIS environment is properly set up"""
        try:
            # Check JARVIS_HOME
            jarvis_home = os.getenv("JARVIS_HOME")
            if not jarvis_home:
                log.error("❌ JARVIS_HOME not set. Run install.py first.")
                return False

            jarvis_path = Path(jarvis_home)
            if not jarvis_path.exists():
                log.error(f"❌ JARVIS_HOME doesn't exist: {jarvis_home}")
                return False

            # Check ACCOUNTS folder
            accounts_dir = jarvis_path / "ACCOUNTS"
            if not accounts_dir.exists():
                log.warning(f"⚠️ ACCOUNTS folder not found, creating: {accounts_dir}")
                try:
                    accounts_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    log.error(f"❌ Failed to create ACCOUNTS folder: {e}")
                    return False

            log.debug(f"✓ Environment check passed (JARVIS_HOME={jarvis_home})")
            return True

        except Exception as e:
            log.error(f"❌ Environment check failed: {type(e).__name__}: {e}", exc_info=True)
            return False

    async def start(self):
        """Start the JARVIS MCP server"""
        try:
            log.info("━" * 60)
            log.info("🚀 JARVIS MCP Server Starting...")
            log.info("━" * 60)

            # Pre-flight checks
            if not self._check_environment():
                log.error("❌ Environment check failed. Setup incomplete?")
                log.error("Run: python install.py")
                sys.exit(1)

            # Import after environment check
            try:
                from jarvis_mcp.mcp_server import JarvisServer
            except ImportError as e:
                log.error(f"❌ Failed to import JarvisServer: {e}")
                log.error("Check that all dependencies are installed: pip install -r requirements.txt")
                sys.exit(1)

            # Initialize server
            log.info("📦 Initializing JARVIS server...")
            self.server = JarvisServer()
            self.running = True
            self.startup_complete = True

            log.info("━" * 60)
            log.info("✅ JARVIS Server Started Successfully")
            log.info("━" * 60)
            log.info("🤖 27 Sales Intelligence Skills loaded and ready")
            log.info("📂 Account Management System active")
            log.info("🔄 File Watchers active (auto-cascade on updates)")
            log.info("📊 CRM Dashboard available at http://localhost:8000")
            log.info("━" * 60)
            log.info("✨ Ready for Claude Desktop connection")
            log.info("━" * 60)

            # Keep server running until shutdown signal
            while self.running:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            log.info("Server startup cancelled")
            self.running = False
        except FileNotFoundError as e:
            log.error(f"❌ File not found (deleted?): {e}", exc_info=True)
            log.error("A JARVIS file was deleted. Run setup again: python install.py")
            self.running = False
            sys.exit(1)
        except Exception as e:
            log.error(f"❌ Fatal startup error: {type(e).__name__}: {e}", exc_info=True)
            self.running = False
            sys.exit(1)

    async def shutdown(self):
        """Gracefully shutdown server (called when Claude Desktop closes)"""
        if not self.startup_complete:
            log.debug("Shutdown called before startup completed")
            return

        try:
            log.info("━" * 60)
            log.info("🛑 JARVIS MCP Server Shutting Down...")
            log.info("━" * 60)

            self.running = False

            # Shutdown server if running
            if self.server:
                try:
                    log.info("📤 Closing file watchers...")
                    await self.server.shutdown()
                except asyncio.TimeoutError:
                    log.warning("⚠️ Server shutdown timeout")
                except Exception as e:
                    log.error(f"Error during shutdown: {type(e).__name__}: {e}", exc_info=True)

            log.info("━" * 60)
            log.info("✅ JARVIS MCP Server Stopped")
            log.info("━" * 60)

        except Exception as e:
            log.error(f"Error during shutdown: {type(e).__name__}: {e}", exc_info=True)

    def handle_signal(self, signum=None, frame=None):
        """Handle shutdown signals (platform-aware)"""
        log.debug(f"Received signal: {signum}")
        asyncio.create_task(self.shutdown())


async def main():
    """Main entry point with lifecycle management"""
    launcher = MCPLauncher()

    # Register signal handlers (Windows: atexit, Unix/Mac: SIGTERM/SIGINT)
    PlatformUtils.register_signal_handlers(launcher.handle_signal)

    # Also register atexit for guaranteed cleanup
    atexit.register(lambda: asyncio.run(launcher.shutdown()) if launcher.running else None)

    # Start server
    try:
        await launcher.start()
    except KeyboardInterrupt:
        log.info("⚠️ Interrupted by user")
        await launcher.shutdown()
    except Exception as e:
        log.error(f"Fatal error: {type(e).__name__}: {e}", exc_info=True)
        await launcher.shutdown()
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
        log.info("JARVIS MCP launcher exited cleanly")
        sys.exit(0)
    except KeyboardInterrupt:
        log.info("JARVIS MCP launcher interrupted by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"JARVIS MCP launcher fatal error: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)
