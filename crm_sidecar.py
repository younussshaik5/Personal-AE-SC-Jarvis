#!/usr/bin/env python3
"""
JARVIS CRM Sidecar MCP Server
Registered in claude_desktop_config.json alongside JARVIS.
Claude Desktop starts this when it opens → it starts serve_crm.py on port 8000.
Claude Desktop closes → this process dies → serve_crm.py subprocess dies too.

Exposes one MCP tool: open_crm_dashboard
"""

import sys
import os
import subprocess
import asyncio
import logging
import signal
import atexit
import threading
from pathlib import Path

# Load .env so CRM server inherits API keys without shell env vars
def _load_dotenv_simple():
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    try:
        # Import at function level to avoid circular dependency
        sys.path.insert(0, str(Path(__file__).parent))
        from jarvis_mcp.platform_utils import PlatformUtils
        PlatformUtils.load_env_file(env_file)
    except Exception as e:
        log.debug(f"Failed to load .env with PlatformUtils: {e}")

# Import PlatformUtils at module level for port checking and signal handlers
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from jarvis_mcp.platform_utils import PlatformUtils
except ImportError:
    PlatformUtils = None

_load_dotenv_simple()

# All logging to stderr — stdout is reserved for MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="[CRM] %(message)s",
    stream=sys.stderr
)
log = logging.getLogger(__name__)

# Locate serve_crm.py — prefer project dir, fall back to parent
_here = Path(__file__).parent
_serve_crm_candidates = [
    _here / "serve_crm.py",          # inside project (correct for forks)
    _here.parent / "serve_crm.py",   # legacy: parent directory
]
SERVE_CRM = next((p for p in _serve_crm_candidates if p.exists()), None)

# Get CRM port from environment (with fallback and validation)
_crm_port_env = os.getenv("CRM_PORT", "8000")
try:
    CRM_PORT = int(_crm_port_env)
    if CRM_PORT < 1 or CRM_PORT > 65535:
        log.error(f"Invalid CRM_PORT {CRM_PORT}: must be 1-65535, using default 8000")
        CRM_PORT = 8000
except ValueError:
    log.error(f"Invalid CRM_PORT '{_crm_port_env}': not an integer, using default 8000")
    CRM_PORT = 8000

# Global subprocess handle
_crm_proc: subprocess.Popen | None = None
_stderr_reader_thread: threading.Thread | None = None


def _read_stderr_stream(process: subprocess.Popen, max_lines: int = 100):
    """
    Read stderr from subprocess in background thread to prevent buffer overflow.

    Args:
        process: The subprocess whose stderr to read
        max_lines: Maximum lines to keep in buffer before dropping old lines
    """
    lines = []
    try:
        while True:
            line = process.stderr.readline()
            if not line:
                break

            line_str = line.decode("utf-8", errors="replace").rstrip()
            if line_str:
                log.debug(f"CRM stderr: {line_str}")
                lines.append(line_str)

                # Keep buffer bounded
                if len(lines) > max_lines:
                    lines.pop(0)
    except Exception as e:
        log.warning(f"Error reading CRM stderr: {e}")


def start_crm_server():
    """
    Start serve_crm.py as a background subprocess with proper error handling.

    Handles:
    - Port conflicts (kills existing processes or finds available port)
    - Stderr buffering (background reader thread)
    - Graceful shutdown with timeout
    - Process cleanup
    """
    global _crm_proc, _stderr_reader_thread

    if not SERVE_CRM:
        log.error("serve_crm.py not found. CRM dashboard unavailable.")
        return False

    # Determine port to use (kill existing process or find available)
    actual_port = CRM_PORT
    if PlatformUtils:
        try:
            if not PlatformUtils.check_port_available(CRM_PORT):
                log.warning(f"Port {CRM_PORT} in use, attempting to kill existing process...")
                if PlatformUtils.kill_process_on_port(CRM_PORT):
                    # Give it a moment to free the port
                    import time
                    time.sleep(1)
                else:
                    # Could not kill existing process, try to find available port
                    log.warning(f"Could not kill process on port {CRM_PORT}, finding available port...")
                    available = PlatformUtils.find_available_port(CRM_PORT)
                    if available:
                        actual_port = available
                        log.info(f"Using alternate port {actual_port} instead of {CRM_PORT}")
                    else:
                        log.error(f"Could not find available port starting from {CRM_PORT}")
                        return False
        except Exception as e:
            log.warning(f"Error checking/using port {CRM_PORT}: {e}")
            # Try to find available port as fallback
            try:
                available = PlatformUtils.find_available_port(8000, 50)
                if available:
                    actual_port = available
                    log.info(f"Using fallback port {actual_port}")
                else:
                    log.error("Could not find any available port")
                    return False
            except Exception as e2:
                log.error(f"Failed to find available port: {e2}")
                return False

    try:
        _crm_proc = subprocess.Popen(
            [sys.executable, str(SERVE_CRM)],
            cwd=str(SERVE_CRM.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env={**os.environ, "CRM_PORT": str(actual_port)},
            preexec_fn=None,  # Windows-safe
        )

        # Start background thread to read stderr
        _stderr_reader_thread = threading.Thread(
            target=_read_stderr_stream,
            args=(_crm_proc,),
            daemon=True,
            name="CRM-stderr-reader"
        )
        _stderr_reader_thread.start()

        log.info(f"CRM dashboard started — http://localhost:{actual_port} (PID {_crm_proc.pid})")
        return True
    except Exception as e:
        log.error(f"Failed to start CRM server on port {actual_port}: {type(e).__name__}: {e}", exc_info=True)
        return False


def stop_crm_server():
    """
    Stop the CRM subprocess gracefully with timeout.

    Process:
    1. Send SIGTERM (graceful shutdown)
    2. Wait up to 5 seconds for process to exit
    3. If still running, send SIGKILL (force kill)
    4. Clean up stderr reader thread
    """
    global _crm_proc, _stderr_reader_thread

    if not _crm_proc or _crm_proc.poll() is not None:
        return  # Already dead

    log.info(f"Stopping CRM server (PID {_crm_proc.pid})…")

    try:
        # Graceful shutdown
        _crm_proc.terminate()

        try:
            # Wait with timeout
            _crm_proc.wait(timeout=5)
            log.info("CRM server stopped gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if still running
            log.warning("CRM server did not stop gracefully, killing…")
            _crm_proc.kill()
            _crm_proc.wait(timeout=2)
            log.info("CRM server killed")

    except Exception as e:
        log.error(f"Error stopping CRM server: {e}", exc_info=True)
    finally:
        _crm_proc = None
        _stderr_reader_thread = None


def handle_exit(signum=None, frame=None):
    stop_crm_server()
    sys.exit(0)


# Register cleanup handlers - both signal handlers AND atexit for comprehensive coverage
# Signal handlers for Unix/Mac (graceful shutdown via signals)
if PlatformUtils:
    PlatformUtils.register_signal_handlers(handle_exit)
else:
    # Fallback for when PlatformUtils is not available
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

# Register atexit handler - ensures cleanup even if process exits abnormally
atexit.register(stop_crm_server)


# ── MCP server ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(_here))

try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    log.error("mcp package not installed. Run: pip install mcp")


async def main():
    if not HAS_MCP:
        # Keep process alive even without MCP so CRM server stays up
        start_crm_server()
        while True:
            await asyncio.sleep(60)
        return

    start_crm_server()

    server = Server("jarvis-crm")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="open_crm_dashboard",
                description=(
                    "Open the JARVIS CRM Dashboard in the browser. "
                    f"Shows deal pipeline, MEDDPICC scores, risks, and AI intelligence for all accounts. "
                    f"Running at http://localhost:{CRM_PORT}"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "open_crm_dashboard":
            # Check if server is up
            alive = _crm_proc and _crm_proc.poll() is None
            if not alive:
                started = start_crm_server()
                if not started:
                    return [types.TextContent(type="text", text="❌ CRM server failed to start. Check that serve_crm.py exists.")]
                await asyncio.sleep(2)

            # Open browser
            try:
                import webbrowser
                webbrowser.open(f"http://localhost:{CRM_PORT}")
            except Exception:
                pass

            return [types.TextContent(
                type="text",
                text=(
                    f"✅ JARVIS CRM Dashboard is running at **http://localhost:{CRM_PORT}**\n\n"
                    "The dashboard shows:\n"
                    "- Full pipeline with Closed Won / Closed Lost\n"
                    "- MEDDPICC scores for every deal\n"
                    "- Risk analysis and competitive intelligence\n"
                    "- All JARVIS-generated skill outputs (battlecard, risk report, etc.)\n"
                    "- One-click PDF export for any account\n\n"
                    "Click any account row to see the full deal intelligence report."
                )
            )]

        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    log.info("CRM sidecar MCP server ready")
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        stop_crm_server()
