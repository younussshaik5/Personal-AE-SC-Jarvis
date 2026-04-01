#!/usr/bin/env python3
"""
JARVIS MCP Server — Official MCP SDK implementation
Runs automatically with Claude Desktop via stdio.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root so jarvis_mcp imports work
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Log to stderr only — stdout is reserved for MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="[JARVIS] %(message)s",
    stream=sys.stderr
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Boot JARVIS
# ---------------------------------------------------------------------------
log.info("Starting JARVIS MCP server…")
try:
    from jarvis_mcp.mcp_server import JarvisServer
    _jarvis = JarvisServer()
    log.info(f"✅ {len(_jarvis.skills)} skills loaded")
except Exception as exc:
    log.error(f"Failed to load JARVIS: {exc}")
    _jarvis = None

# ---------------------------------------------------------------------------
# Tool definitions — maps MCP tool name → (handler, description, schema)
# ---------------------------------------------------------------------------

TOOLS: list[types.Tool] = []

def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required or []
        }
    )


# ── Onboarding ──────────────────────────────────────────────────────────────
TOOLS.append(_tool(
    "onboarding_start",
    "Begin JARVIS onboarding — learns who you are, your company, and your role.",
    {"message": {"type": "string", "description": "Anything about yourself or your company"}}
))

TOOLS.append(_tool(
    "onboarding_next",
    "Continue the onboarding conversation.",
    {"message": {"type": "string", "description": "Your reply"}}
))

# ── Account Management ───────────────────────────────────────────────────────
TOOLS.append(_tool(
    "scaffold_account",
    "Create a new account folder with all JARVIS sections pre-scaffolded.",
    {
        "account_name": {"type": "string", "description": "Company / account name"},
        "company_info": {"type": "string", "description": "Any info about the company (freeform)"}
    },
    required=["account_name"]
))

# ── Core Sales Skills ────────────────────────────────────────────────────────
_account_arg = {"account_name": {"type": "string", "description": "Account name"}}

TOOLS.append(_tool("get_proposal",            "Generate or retrieve the account proposal.",              _account_arg, ["account_name"]))
TOOLS.append(_tool("get_battlecard",          "Get competitive battlecard for this account.",             _account_arg, ["account_name"]))
TOOLS.append(_tool("get_demo_strategy",       "Build a demo strategy and script.",                       _account_arg, ["account_name"]))
TOOLS.append(_tool("get_risk_report",         "Generate a risk assessment report.",                      _account_arg, ["account_name"]))
TOOLS.append(_tool("get_value_architecture",  "Build ROI model / value architecture.",                   _account_arg, ["account_name"]))
TOOLS.append(_tool("get_discovery",           "Get discovery prep questions and saved notes.",            _account_arg, ["account_name"]))
TOOLS.append(_tool("get_competitive_intelligence", "Deep competitive intelligence for the account.",      _account_arg, ["account_name"]))
TOOLS.append(_tool("get_meeting_prep",        "Generate a meeting prep brief.",                          _account_arg, ["account_name"]))
TOOLS.append(_tool("get_account_summary",     "Full account dossier / 360 summary.",                     _account_arg, ["account_name"]))
TOOLS.append(_tool("generate_sow",           "Generate a Statement of Work.",                            _account_arg, ["account_name"]))
TOOLS.append(_tool("generate_architecture",  "Generate a Mermaid.js solution architecture diagram.",     _account_arg, ["account_name"]))
TOOLS.append(_tool("track_meddpicc",         "Score and update MEDDPICC for the deal.",                  _account_arg, ["account_name"]))

TOOLS.append(_tool(
    "update_deal_stage",
    "Move a deal to a new stage.",
    {
        "account_name": {"type": "string"},
        "stage": {"type": "string", "description": "discovery | qualify | demo | negotiate | close | won | lost"},
        "notes": {"type": "string", "description": "Optional context"}
    },
    required=["account_name", "stage"]
))

# ── Communication & Intelligence ─────────────────────────────────────────────
TOOLS.append(_tool(
    "process_meeting",
    "Process a meeting transcript or notes and save to account.",
    {
        "account_name": {"type": "string"},
        "transcript": {"type": "string", "description": "Meeting notes or transcript text"}
    },
    required=["account_name", "transcript"]
))

TOOLS.append(_tool(
    "summarize_conversation",
    "Summarize a conversation or email thread.",
    {
        "account_name": {"type": "string"},
        "text": {"type": "string", "description": "The conversation or email text"}
    },
    required=["account_name", "text"]
))

TOOLS.append(_tool(
    "extract_intelligence",
    "Extract structured sales intelligence from any text.",
    {
        "account_name": {"type": "string"},
        "text": {"type": "string", "description": "Email, notes, or transcript"}
    },
    required=["account_name", "text"]
))

TOOLS.append(_tool(
    "generate_followup",
    "Draft a follow-up email for this account.",
    {
        "account_name": {"type": "string"},
        "context": {"type": "string", "description": "What happened / what to follow up on"}
    },
    required=["account_name"]
))

TOOLS.append(_tool(
    "analyze_competitor_pricing",
    "Analyze competitor pricing and positioning.",
    {
        "account_name": {"type": "string"},
        "competitor": {"type": "string", "description": "Competitor name"}
    },
    required=["account_name"]
))

TOOLS.append(_tool(
    "assess_technical_risk",
    "Assess technical risks for the deal.",
    _account_arg,
    required=["account_name"]
))

TOOLS.append(_tool(
    "quick_insights",
    "Get quick insights and next best action for an account.",
    _account_arg,
    required=["account_name"]
))

TOOLS.append(_tool(
    "build_knowledge_graph",
    "Build or update the knowledge graph for an account.",
    _account_arg,
    required=["account_name"]
))

TOOLS.append(_tool(
    "generate_documentation",
    "Generate technical or sales documentation.",
    {
        "account_name": {"type": "string"},
        "doc_type": {"type": "string", "description": "Type of document to generate"}
    },
    required=["account_name"]
))

TOOLS.append(_tool(
    "generate_custom_template",
    "Generate a custom document from a template.",
    {
        "account_name": {"type": "string"},
        "template_name": {"type": "string"},
        "context": {"type": "string"}
    },
    required=["account_name", "template_name"]
))

TOOLS.append(_tool(
    "generate_html_report",
    "Generate an HTML report for the account.",
    _account_arg,
    required=["account_name"]
))

log.info(f"Registered {len(TOOLS)} MCP tools")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
server = Server("jarvis")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Route tool calls to JARVIS skills."""
    log.info(f"Tool called: {name} — args: {list(arguments.keys())}")

    if _jarvis is None:
        return [types.TextContent(type="text", text="❌ JARVIS server failed to initialize. Check logs.")]

    account = arguments.get("account_name", "")

    try:
        # ── Route to the right skill ──────────────────────────────────────────
        skill = _jarvis.skills.get(name)
        if skill:
            result = await skill.execute(arguments)
            return [types.TextContent(type="text", text=str(result))]

        # ── Fallbacks for tools with different internal names ────────────────
        alias_map = {
            "get_proposal":             "proposal",
            "get_battlecard":           "battlecard",
            "get_demo_strategy":        "demo_strategy",
            "get_risk_report":          "risk_report",
            "get_value_architecture":   "value_architecture",
            "get_discovery":            "discovery",
            "get_competitive_intelligence": "competitive_intelligence",
            "get_meeting_prep":         "meeting_prep",
            "get_account_summary":      "account_summary",
            "generate_sow":             "sow",
            "generate_architecture":    "architecture_diagram",
            "track_meddpicc":           "meddpicc",
            "update_deal_stage":        "deal_stage_tracker",
            "process_meeting":          "meeting_summary",
            "summarize_conversation":   "conversation_summarizer",
            "extract_intelligence":     "conversation_extractor",
            "generate_followup":        "followup_email",
            "analyze_competitor_pricing": "competitor_pricing",
            "assess_technical_risk":    "technical_risk",
            "quick_insights":           "quick_insights",
            "build_knowledge_graph":    "knowledge_builder",
            "generate_documentation":   "documentation",
            "generate_custom_template": "custom_template",
            "generate_html_report":     "html_generator",
        }

        internal_name = alias_map.get(name)
        if internal_name:
            skill = _jarvis.skills.get(internal_name)
            if skill:
                result = await skill.execute(arguments)
                return [types.TextContent(type="text", text=str(result))]

        # ── Special: onboarding ──────────────────────────────────────────────
        if name in ("onboarding_start", "onboarding_next"):
            msg = arguments.get("message", "")
            result = f"JARVIS Onboarding: received '{msg}'. Onboarding skill initializing…"
            return [types.TextContent(type="text", text=result)]

        return [types.TextContent(type="text", text=f"⚠️ Tool '{name}' is registered but has no handler yet.")]

    except Exception as exc:
        log.error(f"Error in {name}: {exc}")
        return [types.TextContent(type="text", text=f"❌ Error running {name}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main():
    log.info("JARVIS MCP server ready — waiting for Claude Desktop…")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
