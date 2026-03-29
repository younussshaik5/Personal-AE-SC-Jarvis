#!/usr/bin/env python3
"""Architecture Diagram Skill - Generates Mermaid.js solution architecture diagrams per account."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.queue.task_queue import TaskQueue, TaskPriority


class ArchitectureDiagramSkill:
    """Generates Mermaid.js architecture diagrams from account intelligence."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.architecture_diagram")
        self.workspace_root = Path(config_manager.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._running = False
        self._queue: Optional[TaskQueue] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self):
        self.logger.info("Starting architecture diagram skill")
        self._running = True
        self._main_loop = asyncio.get_running_loop()
        self._queue = TaskQueue(self.workspace_root)

        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)
        self.event_bus.subscribe("meddpicc.updated", self._on_meddpicc_updated)
        self.event_bus.subscribe("knowledge.intel.updated", self._on_intel_updated)
        self.event_bus.subscribe("account.sections.created", self._on_sections_created)
        self.event_bus.subscribe("meeting.summary.ready", self._on_meeting_summary_ready)

        self.logger.info("Architecture diagram skill started")

    async def stop(self):
        self._running = False
        self.logger.info("Architecture diagram skill stopped")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_discovery_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account:
            self._schedule_task(account, TaskPriority.MEDIUM)

    def _on_meddpicc_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account:
            self._schedule_task(account, TaskPriority.MEDIUM)

    def _on_intel_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account:
            self._schedule_task(account, TaskPriority.MEDIUM)

    def _on_sections_created(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account:
            self._schedule_task(account, TaskPriority.LOW)

    def _on_meeting_summary_ready(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account:
            self._schedule_task(account, TaskPriority.MEDIUM)

    def _schedule_task(self, account: str, priority: TaskPriority):
        if self._queue and self._main_loop:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self._queue.enqueue(
                        "generate_architecture_diagram",
                        payload={"account": account},
                        account=account,
                        priority=priority,
                        dedup_key=f"generate_architecture_diagram:{account}",
                    )
                )
            )

    # ------------------------------------------------------------------
    # Static WorkerPool handler
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_generate_diagram(task, services: Dict[str, Any]):
        """WorkerPool handler — reads account data, generates Mermaid diagram files."""
        kb = services["knowledge_builder"]
        skill: "ArchitectureDiagramSkill" = services.get("architecture_diagram_skill")
        logger = JARVISLogger("skill.architecture_diagram.handler")

        account_name = task.payload.get("account", "")
        if not account_name:
            return

        # Resolve account directory
        accounts_dir = kb._accounts_dir
        account_dir = accounts_dir / account_name
        if not account_dir.exists():
            logger.warning("Account directory not found", account=account_name)
            return

        # Gather source data
        context = _read_account_context(account_dir)
        if not context.get("has_data"):
            logger.info("Insufficient data for diagram generation", account=account_name)
            return

        # Get LLM via knowledge_builder
        llm = kb._get_llm_client()
        if not llm:
            logger.warning("LLM unavailable for architecture diagram", account=account_name)
            return

        # Build prompt
        prompt = _build_diagram_prompt(account_name, context)

        from jarvis.llm.llm_client import Message
        messages = [
            Message(
                role="system",
                content=(
                    "You are a senior solutions architect. Generate precise, accurate Mermaid.js "
                    "diagrams based on account intelligence. Return only valid Mermaid syntax inside "
                    "a ```mermaid code block, followed by a JSON metadata block."
                ),
            ),
            Message(role="user", content=prompt),
        ]

        try:
            response = await llm.generate_with_routing(
                messages, task_type="reasoning", source="background"
            )
        except Exception as e:
            logger.error("LLM call failed for architecture diagram", account=account_name, error=str(e))
            return

        # Parse response
        mermaid_code, metadata = _parse_diagram_response(response, account_name, context)

        # Write output files
        arch_dir = account_dir / "ARCHITECTURE"
        arch_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        data_sources = _list_data_sources(context)

        # Write markdown file
        md_content = _build_markdown_file(account_name, mermaid_code, metadata, today, context)
        (arch_dir / "architecture_diagram.md").write_text(md_content, encoding="utf-8")

        # Write HTML file
        html_content = _build_html_file(account_name, mermaid_code, today, data_sources)
        (arch_dir / "architecture_diagram.html").write_text(html_content, encoding="utf-8")

        logger.info("Architecture diagram generated", account=account_name)

        # Publish event
        kb.event_bus.publish(Event(
            type="architecture.diagram.updated",
            source="skill.architecture_diagram",
            data={"account": account_name},
        ))


# ------------------------------------------------------------------
# Helper functions (module-level, used by static handler)
# ------------------------------------------------------------------

def _read_account_context(account_dir: Path) -> Dict[str, Any]:
    """Read all relevant account data files and return a unified context dict."""
    ctx: Dict[str, Any] = {"has_data": False}

    # contacts.json
    contacts_file = account_dir / "contacts.json"
    if contacts_file.exists():
        try:
            ctx["contacts"] = json.loads(contacts_file.read_text(encoding="utf-8"))
            ctx["has_data"] = True
        except Exception:
            ctx["contacts"] = []

    # meddpicc.json
    meddpicc_file = account_dir / "meddpicc.json"
    if meddpicc_file.exists():
        try:
            ctx["meddpicc"] = json.loads(meddpicc_file.read_text(encoding="utf-8"))
            ctx["has_data"] = True
        except Exception:
            ctx["meddpicc"] = {}

    # INTEL/company_research.md
    intel_file = account_dir / "INTEL" / "company_research.md"
    if intel_file.exists():
        ctx["company_research"] = intel_file.read_text(encoding="utf-8")[:4000]
        ctx["has_data"] = True

    # DISCOVERY/final_discovery.md
    discovery_file = account_dir / "DISCOVERY" / "final_discovery.md"
    if discovery_file.exists():
        ctx["discovery"] = discovery_file.read_text(encoding="utf-8")[:4000]
        ctx["has_data"] = True

    # BATTLECARD/battlecard.md
    battlecard_file = account_dir / "BATTLECARD" / "battlecard.md"
    if battlecard_file.exists():
        ctx["battlecard"] = battlecard_file.read_text(encoding="utf-8")[:2000]

    # VALUE_ARCHITECTURE/roi_model.md
    roi_file = account_dir / "VALUE_ARCHITECTURE" / "roi_model.md"
    if roi_file.exists():
        ctx["roi_model"] = roi_file.read_text(encoding="utf-8")[:2000]

    return ctx


def _build_diagram_prompt(account_name: str, ctx: Dict[str, Any]) -> str:
    contacts_str = ""
    contacts = ctx.get("contacts", [])
    if isinstance(contacts, list):
        for c in contacts[:8]:
            name = c.get("name") or c.get("full_name", "Unknown")
            role = c.get("title") or c.get("role", "")
            contacts_str += f"  - {name} ({role})\n"
    elif isinstance(contacts, dict):
        for name, info in list(contacts.items())[:8]:
            role = info.get("title") or info.get("role", "") if isinstance(info, dict) else ""
            contacts_str += f"  - {name} ({role})\n"

    meddpicc = ctx.get("meddpicc", {})
    decision_process = ""
    if isinstance(meddpicc, dict):
        decision_process = meddpicc.get("decision_process", meddpicc.get("D", ""))

    solution_name = "AI Platform"
    intel = ctx.get("company_research", "")
    if "yellow.ai" in intel.lower():
        solution_name = "yellow.ai AI Platform"

    return f"""Generate a Mermaid.js solution architecture diagram for account: {account_name}

KEY STAKEHOLDERS (from contacts):
{contacts_str or '  - Stakeholders not yet identified'}

CURRENT ENVIRONMENT / PAIN POINTS (from discovery & intel):
{ctx.get('discovery', ctx.get('company_research', 'No discovery data available'))[:2000]}

OUR SOLUTION: {solution_name}

VALUE DELIVERED (from value architecture / discovery metrics):
{ctx.get('roi_model', 'ROI model not yet generated')[:1000]}

DECISION FLOW (from MEDDPICC decision process):
{decision_process or 'Decision process not yet mapped'}

COMPETITIVE CONTEXT:
{ctx.get('battlecard', 'No battlecard data available')[:1000]}

Generate a diagram that shows:
1. Customer org box — key stakeholders with their roles
2. Current state — pain points and existing tech stack
3. {solution_name} integration layer — key capabilities mapped to pain points
4. Value delivered — metrics and outcomes from value architecture
5. Decision flow — from MEDDPICC decision process

Return your response in this exact format:

```mermaid
[your Mermaid.js diagram here — use flowchart LR or graph TD]
```

```json
{{
  "solution_name": "{solution_name}",
  "key_stakeholders": ["Name (Role)", "..."],
  "pain_points": ["...", "..."],
  "integration_points": ["...", "..."],
  "value_metrics": ["...", "..."],
  "decision_steps": ["...", "..."]
}}
```
"""


def _parse_diagram_response(response: str, account_name: str, ctx: Dict[str, Any]):
    """Extract mermaid code and metadata JSON from LLM response."""
    mermaid_code = ""
    metadata = {}

    # Extract mermaid block
    if "```mermaid" in response:
        parts = response.split("```mermaid")
        if len(parts) > 1:
            inner = parts[1].split("```")[0].strip()
            mermaid_code = inner

    # Extract JSON metadata block
    if "```json" in response:
        parts = response.split("```json")
        if len(parts) > 1:
            json_str = parts[1].split("```")[0].strip()
            try:
                metadata = json.loads(json_str)
            except Exception:
                metadata = {}

    # Fallback diagram if LLM failed to produce valid mermaid
    if not mermaid_code:
        contacts = ctx.get("contacts", [])
        stakeholders = []
        if isinstance(contacts, list):
            stakeholders = [
                f"{c.get('name', 'Contact')} ({c.get('title', '')})"
                for c in contacts[:4]
            ]
        stakeholder_nodes = "\n    ".join(
            [f'S{i}["{s}"]' for i, s in enumerate(stakeholders)]
        ) or 'S0["Key Stakeholder"]'
        mermaid_code = f"""graph LR
    subgraph Customer["{account_name} — Customer Org"]
    {stakeholder_nodes}
    end
    subgraph CurrentState["Current State"]
    CS1["Manual Processes"]
    CS2["Fragmented Tools"]
    CS3["High Operational Cost"]
    end
    subgraph AIPlatform["AI Platform — Integration Layer"]
    AI1["Conversational AI"]
    AI2["Workflow Automation"]
    AI3["Unified Analytics"]
    end
    subgraph Value["Value Delivered"]
    V1["Cost Reduction"]
    V2["CSAT Improvement"]
    V3["Agent Efficiency"]
    end
    Customer --> CurrentState
    CurrentState --> AIPlatform
    AIPlatform --> Value"""

    return mermaid_code, metadata


def _list_data_sources(ctx: Dict[str, Any]) -> List[str]:
    sources = []
    if ctx.get("contacts"):
        sources.append("contacts.json — key stakeholders")
    if ctx.get("meddpicc"):
        sources.append("meddpicc.json — qualification data")
    if ctx.get("company_research"):
        sources.append("INTEL/company_research.md — company intelligence")
    if ctx.get("discovery"):
        sources.append("DISCOVERY/final_discovery.md — discovery notes")
    if ctx.get("battlecard"):
        sources.append("BATTLECARD/battlecard.md — competitive context")
    if ctx.get("roi_model"):
        sources.append("VALUE_ARCHITECTURE/roi_model.md — ROI model")
    return sources or ["No data sources found — regenerate after account data is populated"]


def _build_markdown_file(
    account_name: str,
    mermaid_code: str,
    metadata: Dict[str, Any],
    generated_at: str,
    ctx: Dict[str, Any],
) -> str:
    meta_section = ""
    if metadata:
        if metadata.get("key_stakeholders"):
            meta_section += "\n### Key Stakeholders\n" + "\n".join(
                f"- {s}" for s in metadata["key_stakeholders"]
            )
        if metadata.get("pain_points"):
            meta_section += "\n\n### Pain Points\n" + "\n".join(
                f"- {p}" for p in metadata["pain_points"]
            )
        if metadata.get("integration_points"):
            meta_section += "\n\n### Integration Points\n" + "\n".join(
                f"- {i}" for i in metadata["integration_points"]
            )
        if metadata.get("value_metrics"):
            meta_section += "\n\n### Value Metrics\n" + "\n".join(
                f"- {v}" for v in metadata["value_metrics"]
            )

    sources = _list_data_sources(ctx)
    sources_md = "\n".join(f"- {s}" for s in sources)

    return f"""# Architecture Diagram — {account_name}

**Generated:** {generated_at}

---

## Mermaid.js Diagram

```mermaid
{mermaid_code}
```

---
{meta_section}

---

## Data Sources

{sources_md}

---

*Auto-generated by JARVIS Architecture Diagram Skill. Regenerates on discovery, MEDDPICC, or intel updates.*
"""


def _build_html_file(
    account_name: str,
    mermaid_code: str,
    generated_at: str,
    data_sources: List[str],
) -> str:
    sources_html = "\n".join(
        f"        <li>{s}</li>" for s in data_sources
    )
    # Escape backticks and backslashes for embedding in JS template literal
    safe_mermaid = mermaid_code.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Architecture Diagram — {account_name}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: #0f172a;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      padding: 2rem;
    }}

    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #1e293b;
    }}

    header h1 {{
      font-size: 1.5rem;
      font-weight: 700;
      color: #f1f5f9;
      letter-spacing: -0.02em;
    }}

    header .meta {{
      font-size: 0.8rem;
      color: #64748b;
    }}

    .badge {{
      display: inline-block;
      background: #6366f1;
      color: #fff;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-right: 0.5rem;
    }}

    .diagram-container {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 0.75rem;
      padding: 2rem;
      margin-bottom: 2rem;
      overflow-x: auto;
    }}

    .diagram-container .mermaid {{
      display: flex;
      justify-content: center;
    }}

    .toolbar {{
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }}

    button {{
      background: #6366f1;
      color: #fff;
      border: none;
      border-radius: 0.5rem;
      padding: 0.5rem 1.25rem;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }}

    button:hover {{
      background: #4f46e5;
    }}

    button.secondary {{
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
    }}

    button.secondary:hover {{
      background: #334155;
      color: #e2e8f0;
    }}

    .sources-section {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 0.75rem;
      padding: 1.5rem;
    }}

    .sources-section h2 {{
      font-size: 1rem;
      font-weight: 600;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 1rem;
    }}

    .sources-section ul {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}

    .sources-section li {{
      font-size: 0.875rem;
      color: #64748b;
      padding-left: 1.2rem;
      position: relative;
    }}

    .sources-section li::before {{
      content: "▸";
      position: absolute;
      left: 0;
      color: #6366f1;
    }}

    footer {{
      margin-top: 2rem;
      text-align: center;
      font-size: 0.75rem;
      color: #334155;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <span class="badge">JARVIS</span>
      <h1>Solution Architecture — {account_name}</h1>
    </div>
    <div class="meta">Generated: {generated_at}</div>
  </header>

  <div class="toolbar">
    <button id="downloadSvg">Download SVG</button>
    <button class="secondary" id="copyMermaid">Copy Mermaid Source</button>
  </div>

  <div class="diagram-container">
    <div class="mermaid" id="diagram">
{mermaid_code}
    </div>
  </div>

  <div class="sources-section">
    <h2>Data Sources</h2>
    <ul>
{sources_html}
    </ul>
  </div>

  <footer>Auto-generated by JARVIS &mdash; Architecture Diagram Skill &mdash; Regenerates on data updates</footer>

  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        primaryColor: '#6366f1',
        primaryTextColor: '#f1f5f9',
        primaryBorderColor: '#818cf8',
        lineColor: '#475569',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a',
        background: '#0f172a',
        mainBkg: '#1e293b',
        nodeBorder: '#6366f1',
        clusterBkg: '#1e293b',
        titleColor: '#f1f5f9',
        edgeLabelBackground: '#1e293b',
        fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
      }},
      flowchart: {{
        htmlLabels: true,
        curve: 'basis',
      }},
    }});

    document.getElementById('downloadSvg').addEventListener('click', async () => {{
      const svg = document.querySelector('#diagram svg');
      if (!svg) {{ alert('Diagram not yet rendered.'); return; }}
      const serializer = new XMLSerializer();
      const svgStr = serializer.serializeToString(svg);
      const blob = new Blob([svgStr], {{ type: 'image/svg+xml' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'architecture_{account_name.replace(" ", "_")}.svg';
      a.click();
      URL.revokeObjectURL(url);
    }});

    document.getElementById('copyMermaid').addEventListener('click', () => {{
      const src = `{safe_mermaid}`;
      navigator.clipboard.writeText(src).then(() => {{
        const btn = document.getElementById('copyMermaid');
        btn.textContent = 'Copied!';
        setTimeout(() => {{ btn.textContent = 'Copy Mermaid Source'; }}, 2000);
      }});
    }});
  </script>
</body>
</html>
"""
