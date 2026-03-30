#!/usr/bin/env python3
"""Proposal Skill - Generates structured proposal JSON and HTML per account."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.queue.task_queue import TaskQueue, TaskPriority


class ProposalSkill:
    """Generates proposal_data.json and proposal.html per account."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.proposal")
        self.workspace_root = Path(config_manager.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._running = False
        self._queue: Optional[TaskQueue] = None

    async def start(self):
        self.logger.info("Starting proposal skill")
        self._running = True
        self._queue = TaskQueue(self.workspace_root)

        self.event_bus.subscribe("value_architecture.updated", self._on_value_architecture_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)
        self.event_bus.subscribe("deal.stage.changed", self._on_deal_stage_changed)

        self.logger.info("Proposal skill started")

    async def stop(self):
        self._running = False
        self.logger.info("Proposal skill stopped")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_value_architecture_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account and self._queue:
            await self._queue.enqueue(
                "generate_proposal", payload={"account": account},
                account=account, priority=TaskPriority.MEDIUM,
                dedup_key=f"generate_proposal:{account}",
            )

    async def _on_discovery_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account and self._queue:
            await self._queue.enqueue(
                "generate_proposal", payload={"account": account},
                account=account, priority=TaskPriority.MEDIUM,
                dedup_key=f"generate_proposal:{account}",
            )

    async def _on_deal_stage_changed(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account and self._queue:
            await self._queue.enqueue(
                "generate_proposal", payload={"account": account},
                account=account, priority=TaskPriority.HIGH,
                dedup_key=f"generate_proposal:{account}",
            )

    # ------------------------------------------------------------------
    # Static WorkerPool handler
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_generate_proposal(task, services: Dict[str, Any]):
        """WorkerPool handler — builds proposal_data.json and proposal.html."""
        kb = services["knowledge_builder"]
        logger = JARVISLogger("skill.proposal.handler")

        account_name = task.payload.get("account", "")
        if not account_name:
            return

        accounts_dir = kb._accounts_dir
        account_dir = accounts_dir / account_name
        if not account_dir.exists():
            logger.warning("Account directory not found", account=account_name)
            return

        # Gather account context
        context = _read_proposal_context(account_dir)

        # Get LLM via knowledge_builder
        llm = kb._get_llm_client()
        if not llm:
            logger.warning("LLM unavailable for proposal generation", account=account_name)
            proposal_data = _fallback_proposal_data(account_name)
        else:
            proposal_data = await _generate_proposal_data(account_name, context, llm, logger)

        # Write proposal_data.json
        proposal_dir = account_dir / "PROPOSAL"
        proposal_dir.mkdir(exist_ok=True)

        proposal_json_path = proposal_dir / "proposal_data.json"
        proposal_json_path.write_text(
            json.dumps(proposal_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Load HTML template and inject data
        template_path = Path(__file__).parent.parent / "templates" / "proposal_builder.html"
        html_content = _render_proposal_html(proposal_data, template_path)
        (proposal_dir / "proposal.html").write_text(html_content, encoding="utf-8")

        logger.info("Proposal generated", account=account_name)

        # Publish event
        kb.event_bus.publish(Event(
            type="proposal.updated",
            source="skill.proposal",
            data={"account": account_name},
        ))


# ------------------------------------------------------------------
# Helper functions (module-level)
# ------------------------------------------------------------------

def _read_proposal_context(account_dir: Path) -> Dict[str, Any]:
    """Read all relevant files for proposal generation."""
    ctx: Dict[str, Any] = {}

    # contacts.json
    contacts_file = account_dir / "contacts.json"
    if contacts_file.exists():
        try:
            ctx["contacts"] = json.loads(contacts_file.read_text(encoding="utf-8"))
        except Exception:
            ctx["contacts"] = []

    # meddpicc.json
    meddpicc_file = account_dir / "meddpicc.json"
    if meddpicc_file.exists():
        try:
            ctx["meddpicc"] = json.loads(meddpicc_file.read_text(encoding="utf-8"))
        except Exception:
            ctx["meddpicc"] = {}

    # INTEL/company_research.md
    intel_file = account_dir / "INTEL" / "company_research.md"
    if intel_file.exists():
        ctx["company_research"] = intel_file.read_text(encoding="utf-8")[:3000]

    # DISCOVERY/final_discovery.md
    discovery_file = account_dir / "DISCOVERY" / "final_discovery.md"
    if discovery_file.exists():
        ctx["discovery"] = discovery_file.read_text(encoding="utf-8")[:3000]

    # VALUE_ARCHITECTURE/roi_model.md
    roi_file = account_dir / "VALUE_ARCHITECTURE" / "roi_model.md"
    if roi_file.exists():
        ctx["roi_model"] = roi_file.read_text(encoding="utf-8")[:2000]

    # BATTLECARD/battlecard.md
    battlecard_file = account_dir / "BATTLECARD" / "battlecard.md"
    if battlecard_file.exists():
        ctx["battlecard"] = battlecard_file.read_text(encoding="utf-8")[:1500]

    return ctx


async def _generate_proposal_data(
    account_name: str,
    ctx: Dict[str, Any],
    llm,
    logger,
) -> Dict[str, Any]:
    """Use LLM (task_type='quick') to generate structured proposal fields."""
    from jarvis.llm.llm_client import Message

    prompt = f"""Generate structured proposal data for account: {account_name}

DISCOVERY NOTES:
{ctx.get('discovery', 'No discovery data available')}

COMPANY RESEARCH:
{ctx.get('company_research', 'No company research available')}

ROI MODEL:
{ctx.get('roi_model', 'No ROI model available')}

COMPETITIVE CONTEXT:
{ctx.get('battlecard', 'No battlecard available')}

Return a single JSON object with this exact structure:
{{
  "account": "{account_name}",
  "generated_at": "{datetime.now().strftime('%Y-%m-%d')}",
  "executive_summary": "2-3 sentence summary of the problem, proposed solution, and financial case",
  "pain_points": ["specific pain point 1", "pain point 2", "pain point 3"],
  "proposed_solution": "Description of the proposed AI platform solution and key capabilities",
  "key_benefits": ["Benefit 1 with metric", "Benefit 2 with metric", "Benefit 3 with metric"],
  "implementation_timeline": "Phase 1 (weeks 1-6): Core deployment. Phase 2 (weeks 7-12): Expansion. Phase 3 (ongoing): Optimization.",
  "line_items": [
    {{"name": "Platform License", "description": "Annual subscription", "quantity": 1, "unit_price": 0, "discount_pct": 0}},
    {{"name": "Implementation Services", "description": "Onboarding and configuration", "quantity": 1, "unit_price": 0, "discount_pct": 0}},
    {{"name": "AI Training & Optimization", "description": "Model tuning for use cases", "quantity": 1, "unit_price": 0, "discount_pct": 0}}
  ],
  "terms": "Net 30",
  "validity_days": 30
}}

Use specific numbers and metrics from the discovery/ROI data where available. Do not invent pricing — leave unit_price as 0 if unknown.
"""

    messages = [
        Message(
            role="system",
            content=(
                "You are a senior sales engineer. Generate accurate, data-driven proposal content "
                "from account intelligence. Return only valid JSON — no markdown fences, no commentary."
            ),
        ),
        Message(role="user", content=prompt),
    ]

    try:
        response = await llm.generate_with_routing(
            messages, task_type="quick", source="background"
        )
        # Strip markdown fences if present
        clean = response.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        data = json.loads(clean)
        # Ensure required keys exist
        data.setdefault("account", account_name)
        data.setdefault("generated_at", datetime.now().strftime("%Y-%m-%d"))
        data.setdefault("terms", "Net 30")
        data.setdefault("validity_days", 30)
        return data
    except Exception as e:
        logger.warning("LLM proposal generation failed, using fallback", account=account_name, error=str(e))
        return _fallback_proposal_data(account_name)


def _fallback_proposal_data(account_name: str) -> Dict[str, Any]:
    """Return minimal proposal data when LLM is unavailable."""
    return {
        "account": account_name,
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "executive_summary": (
            f"{account_name} is evaluating AI automation to reduce operational costs and improve "
            "customer experience. The proposed solution delivers enterprise-grade AI automation "
            "with measurable ROI within 90 days."
        ),
        "pain_points": [
            "High volume of repetitive tasks handled manually",
            "Fragmented communication and workflow channels",
            "Slow response times impacting customer satisfaction",
        ],
        "proposed_solution": (
            "Intelligent automation platform covering AI workflows, omnichannel engagement, "
            "and process automation — deployed in phases starting with highest-impact use cases."
        ),
        "key_benefits": [
            "60-80% bot containment rate — reducing agent workload",
            "30-50% reduction in total cost of ownership vs. current stack",
            "Sub-4-week time-to-value for Phase 1 deployment",
        ],
        "implementation_timeline": (
            "Phase 1 (weeks 1-6): Primary use case deployment and agent training. "
            "Phase 2 (weeks 7-12): Secondary channels and integrations. "
            "Phase 3 (ongoing): AI optimization and expansion."
        ),
        "line_items": [
            {"name": "Platform License", "description": "Annual subscription", "quantity": 1, "unit_price": 0, "discount_pct": 0},
            {"name": "Implementation Services", "description": "Onboarding and configuration", "quantity": 1, "unit_price": 0, "discount_pct": 0},
            {"name": "AI Training & Optimization", "description": "Model tuning for primary use cases", "quantity": 1, "unit_price": 0, "discount_pct": 0},
        ],
        "terms": "Net 30",
        "validity_days": 30,
    }


def _render_proposal_html(proposal_data: Dict[str, Any], template_path: Path) -> str:
    """Inject proposal_data into the HTML template. Falls back to built-in template if file not found."""

    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = _built_in_proposal_template()

    # Build replacement values
    account = proposal_data.get("account", "")
    generated_at = proposal_data.get("generated_at", datetime.now().strftime("%Y-%m-%d"))
    exec_summary = proposal_data.get("executive_summary", "")
    proposed_solution = proposal_data.get("proposed_solution", "")
    implementation_timeline = proposal_data.get("implementation_timeline", "")
    terms = proposal_data.get("terms", "Net 30")
    validity_days = proposal_data.get("validity_days", 30)

    pain_points_html = "\n".join(
        f"          <li>{p}</li>" for p in proposal_data.get("pain_points", [])
    )
    key_benefits_html = "\n".join(
        f"          <li>{b}</li>" for b in proposal_data.get("key_benefits", [])
    )

    # Build line items table
    line_items = proposal_data.get("line_items", [])
    subtotal = 0.0
    rows_html = ""
    for item in line_items:
        qty = item.get("quantity", 1)
        price = item.get("unit_price", 0)
        disc = item.get("discount_pct", 0)
        line_total = qty * price * (1 - disc / 100)
        subtotal += line_total
        price_str = f"${price:,.2f}" if price else "TBD"
        total_str = f"${line_total:,.2f}" if price else "TBD"
        disc_str = f"{disc}%" if disc else "—"
        rows_html += f"""        <tr>
          <td>{item.get('name', '')}</td>
          <td>{item.get('description', '')}</td>
          <td>{qty}</td>
          <td>{price_str}</td>
          <td>{disc_str}</td>
          <td>{total_str}</td>
        </tr>\n"""

    subtotal_str = f"${subtotal:,.2f}" if subtotal else "To be quoted"

    # Simple token substitution
    replacements = {
        "{{ACCOUNT_NAME}}": account,
        "{{GENERATED_AT}}": generated_at,
        "{{EXECUTIVE_SUMMARY}}": exec_summary,
        "{{PAIN_POINTS_LIST}}": pain_points_html,
        "{{PROPOSED_SOLUTION}}": proposed_solution,
        "{{KEY_BENEFITS_LIST}}": key_benefits_html,
        "{{IMPLEMENTATION_TIMELINE}}": implementation_timeline,
        "{{LINE_ITEMS_ROWS}}": rows_html,
        "{{SUBTOTAL}}": subtotal_str,
        "{{TERMS}}": terms,
        "{{VALIDITY_DAYS}}": str(validity_days),
        "{{PROPOSAL_DATA_JSON}}": json.dumps(proposal_data, indent=2, ensure_ascii=False),
    }

    html = template
    for token, value in replacements.items():
        html = html.replace(token, value)

    return html


def _built_in_proposal_template() -> str:
    """Minimal self-contained HTML proposal template used when proposal_builder.html is absent."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Proposal — {{ACCOUNT_NAME}}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0f172a; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 2rem; }
    h1 { font-size: 1.75rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.25rem; }
    h2 { font-size: 1.1rem; font-weight: 600; color: #818cf8; text-transform: uppercase; letter-spacing: 0.06em; margin: 2rem 0 0.75rem; }
    p { color: #94a3b8; line-height: 1.7; margin-bottom: 0.75rem; }
    ul { list-style: none; padding: 0; }
    ul li { padding: 0.4rem 0 0.4rem 1.2rem; position: relative; color: #94a3b8; }
    ul li::before { content: "▸"; position: absolute; left: 0; color: #6366f1; }
    .meta { font-size: 0.8rem; color: #475569; margin-bottom: 2rem; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th { background: #1e293b; color: #64748b; text-align: left; padding: 0.6rem 0.75rem; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.06em; }
    td { padding: 0.65rem 0.75rem; border-bottom: 1px solid #1e293b; color: #94a3b8; }
    tr:hover td { background: #1e293b; }
    .subtotal { text-align: right; font-weight: 600; color: #f1f5f9; margin-top: 0.75rem; }
    .badge { display: inline-block; background: #6366f1; color: #fff; font-size: 0.7rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 9999px; letter-spacing: 0.05em; text-transform: uppercase; margin-right: 0.5rem; }
    footer { margin-top: 3rem; text-align: center; font-size: 0.75rem; color: #334155; }
  </style>
</head>
<body>
  <span class="badge">JARVIS</span>
  <h1>Proposal — {{ACCOUNT_NAME}}</h1>
  <p class="meta">Prepared: {{GENERATED_AT}} &nbsp;|&nbsp; Valid for {{VALIDITY_DAYS}} days &nbsp;|&nbsp; Terms: {{TERMS}}</p>

  <div class="card">
    <h2>Executive Summary</h2>
    <p>{{EXECUTIVE_SUMMARY}}</p>
  </div>

  <div class="card">
    <h2>Pain Points Addressed</h2>
    <ul>
{{PAIN_POINTS_LIST}}
    </ul>
  </div>

  <div class="card">
    <h2>Proposed Solution</h2>
    <p>{{PROPOSED_SOLUTION}}</p>
  </div>

  <div class="card">
    <h2>Key Benefits</h2>
    <ul>
{{KEY_BENEFITS_LIST}}
    </ul>
  </div>

  <div class="card">
    <h2>Implementation Timeline</h2>
    <p>{{IMPLEMENTATION_TIMELINE}}</p>
  </div>

  <div class="card">
    <h2>Commercial Summary</h2>
    <table>
      <thead>
        <tr><th>Item</th><th>Description</th><th>Qty</th><th>Unit Price</th><th>Discount</th><th>Total</th></tr>
      </thead>
      <tbody>
{{LINE_ITEMS_ROWS}}
      </tbody>
    </table>
    <p class="subtotal">Estimated Total: {{SUBTOTAL}}</p>
  </div>

  <footer>Auto-generated by JARVIS Proposal Skill &mdash; Review before sending to customer</footer>
</body>
</html>
"""
