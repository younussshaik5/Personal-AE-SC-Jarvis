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
CRM_PORT = int(os.getenv("CRM_PORT", "8000"))

# Global subprocess handle
_crm_proc: subprocess.Popen | None = None


def start_crm_server():
    """Start serve_crm.py as a background subprocess."""
    global _crm_proc

    if not SERVE_CRM:
        log.error("serve_crm.py not found. CRM dashboard unavailable.")
        return False

    # Kill any existing process on port (cross-platform)
    if PlatformUtils:
        try:
            if not PlatformUtils.check_port_available(CRM_PORT):
                PlatformUtils.kill_process_on_port(CRM_PORT)
        except Exception:
            pass

    try:
        _crm_proc = subprocess.Popen(
            [sys.executable, str(SERVE_CRM)],
            cwd=str(SERVE_CRM.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env={**os.environ, "CRM_PORT": str(CRM_PORT)},
        )
        log.info(f"CRM dashboard started — http://localhost:{CRM_PORT} (PID {_crm_proc.pid})")
        return True
    except Exception as e:
        log.error(f"Failed to start CRM server: {e}")
        return False


def stop_crm_server():
    """Stop the CRM subprocess."""
    global _crm_proc
    if _crm_proc and _crm_proc.poll() is None:
        log.info("Stopping CRM server…")
        _crm_proc.terminate()
        try:
            _crm_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _crm_proc.kill()
        _crm_proc = None


def handle_exit(signum=None, frame=None):
    stop_crm_server()
    sys.exit(0)


# Register platform-aware signal handlers (Windows-safe)
if PlatformUtils:
    PlatformUtils.register_signal_handlers(handle_exit)
else:
    # Fallback for when PlatformUtils is not available
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)


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
