#!/usr/bin/env python3
"""SOW Skill - Generates detailed Scope of Work documents per account using Step 3.5 Flash (reasoning)."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.queue.task_queue import TaskQueue, TaskPriority


class SOWSkill:
    """Generates comprehensive Scope of Work documents from account intelligence."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.sow")
        self.workspace_root = Path(config_manager.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._running = False
        self._queue: Optional[TaskQueue] = None

    async def start(self):
        self.logger.info("Starting SOW skill")
        self._running = True
        self._queue = TaskQueue(self.workspace_root)

        self.event_bus.subscribe("proposal.updated", self._on_proposal_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)
        self.event_bus.subscribe("value_architecture.updated", self._on_value_architecture_updated)

        self.logger.info("SOW skill started")

    async def stop(self):
        self._running = False
        self.logger.info("SOW skill stopped")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_proposal_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account and self._queue:
            await self._queue.enqueue(
                "generate_sow", payload={"account": account},
                account=account, priority=TaskPriority.MEDIUM,
                dedup_key=f"generate_sow:{account}",
            )

    async def _on_discovery_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account and self._queue:
            await self._queue.enqueue(
                "generate_sow", payload={"account": account},
                account=account, priority=TaskPriority.MEDIUM,
                dedup_key=f"generate_sow:{account}",
            )

    async def _on_value_architecture_updated(self, event: Event):
        account = event.data.get("account") or event.data.get("account_name")
        if account and self._queue:
            await self._queue.enqueue(
                "generate_sow", payload={"account": account},
                account=account, priority=TaskPriority.MEDIUM,
                dedup_key=f"generate_sow:{account}",
            )

    # ------------------------------------------------------------------
    # Static WorkerPool handler
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_generate_sow(task, services: Dict[str, Any]):
        """WorkerPool handler — reads account data, uses Step 3.5 Flash to generate SOW markdown."""
        kb = services["knowledge_builder"]
        logger = JARVISLogger("skill.sow.handler")

        account_name = task.payload.get("account", "")
        if not account_name:
            return

        accounts_dir = kb._accounts_dir
        account_dir = accounts_dir / account_name
        if not account_dir.exists():
            logger.warning("Account directory not found", account=account_name)
            return

        # Gather source data
        context = _read_sow_context(account_dir)
        if not context.get("has_data"):
            logger.info("Insufficient data for SOW generation", account=account_name)
            return

        # Get LLM via knowledge_builder
        llm = kb._get_llm_client()
        if not llm:
            logger.warning("LLM unavailable for SOW generation", account=account_name)
            sow_content = _fallback_sow(account_name, context)
        else:
            sow_content = await _generate_sow_content(account_name, context, llm, logger)

        # Write output
        sow_dir = account_dir / "SOW"
        sow_dir.mkdir(exist_ok=True)
        (sow_dir / "sow.md").write_text(sow_content, encoding="utf-8")

        logger.info("SOW generated", account=account_name)

        # Publish event
        kb.event_bus.publish(Event(
            type="sow.updated",
            source="skill.sow",
            data={"account": account_name},
        ))


# ------------------------------------------------------------------
# Helper functions (module-level)
# ------------------------------------------------------------------

def _read_sow_context(account_dir: Path) -> Dict[str, Any]:
    """Read all relevant files for SOW generation."""
    ctx: Dict[str, Any] = {"has_data": False}

    # DISCOVERY/final_discovery.md
    discovery_file = account_dir / "DISCOVERY" / "final_discovery.md"
    if discovery_file.exists():
        ctx["discovery"] = discovery_file.read_text(encoding="utf-8")[:4000]
        ctx["has_data"] = True

    # VALUE_ARCHITECTURE/roi_model.md
    roi_file = account_dir / "VALUE_ARCHITECTURE" / "roi_model.md"
    if roi_file.exists():
        ctx["roi_model"] = roi_file.read_text(encoding="utf-8")[:3000]
        ctx["has_data"] = True

    # PROPOSAL/proposal_data.json
    proposal_json = account_dir / "PROPOSAL" / "proposal_data.json"
    if proposal_json.exists():
        try:
            ctx["proposal"] = json.loads(proposal_json.read_text(encoding="utf-8"))
            ctx["has_data"] = True
        except Exception:
            ctx["proposal"] = {}

    # INTEL/company_research.md
    intel_file = account_dir / "INTEL" / "company_research.md"
    if intel_file.exists():
        ctx["company_research"] = intel_file.read_text(encoding="utf-8")[:3000]

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

    return ctx


async def _generate_sow_content(
    account_name: str,
    ctx: Dict[str, Any],
    llm,
    logger,
) -> str:
    """Use Step 3.5 Flash (task_type='reasoning') to generate a detailed SOW."""
    from jarvis.llm.llm_client import Message

    # Extract proposal fields for richer context
    proposal = ctx.get("proposal", {})
    exec_summary = proposal.get("executive_summary", "")
    pain_points = proposal.get("pain_points", [])
    proposed_solution = proposal.get("proposed_solution", "")
    key_benefits = proposal.get("key_benefits", [])
    line_items = proposal.get("line_items", [])
    terms = proposal.get("terms", "Net 30")
    validity_days = proposal.get("validity_days", 30)

    pain_points_str = "\n".join(f"- {p}" for p in pain_points) if pain_points else "See discovery notes"
    benefits_str = "\n".join(f"- {b}" for b in key_benefits) if key_benefits else "See ROI model"
    line_items_str = "\n".join(
        f"- {li.get('name', '')}: {li.get('description', '')}"
        for li in line_items
    ) if line_items else "Commercial details TBD"

    # Contacts
    contacts = ctx.get("contacts", [])
    contacts_str = ""
    if isinstance(contacts, list):
        for c in contacts[:10]:
            name = c.get("name") or c.get("full_name", "TBD")
            role = c.get("title") or c.get("role", "")
            contacts_str += f"  - {name} ({role})\n"
    elif isinstance(contacts, dict):
        for name, info in list(contacts.items())[:10]:
            role = info.get("title") or info.get("role", "") if isinstance(info, dict) else ""
            contacts_str += f"  - {name} ({role})\n"

    # MEDDPICC metrics & success criteria
    meddpicc = ctx.get("meddpicc", {})
    metrics_raw = ""
    if isinstance(meddpicc, dict):
        metrics_raw = meddpicc.get("metrics", meddpicc.get("M", ""))
        paper_process = meddpicc.get("paper_process", meddpicc.get("P", ""))
    else:
        paper_process = ""

    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""Generate a detailed, professional Scope of Work (SOW) document for account: {account_name}
Generated: {today}

SOURCE DATA:

DISCOVERY NOTES:
{ctx.get('discovery', 'No discovery data available')}

COMPANY RESEARCH:
{ctx.get('company_research', 'No company research available')}

ROI MODEL:
{ctx.get('roi_model', 'No ROI model available')}

EXECUTIVE SUMMARY (from proposal):
{exec_summary or 'Not yet generated'}

PAIN POINTS:
{pain_points_str}

PROPOSED SOLUTION:
{proposed_solution or 'Not yet defined'}

KEY BENEFITS / SUCCESS METRICS:
{benefits_str}

COMMERCIAL LINE ITEMS:
{line_items_str}

KEY STAKEHOLDERS / CONTACTS:
{contacts_str or '  - Stakeholders not yet identified'}

MEDDPICC METRICS:
{metrics_raw or 'Metrics not yet captured'}

PAPER PROCESS / CONTRACT NOTES:
{paper_process or 'Paper process not yet mapped'}

TERMS: {terms} | VALIDITY: {validity_days} days

---

Generate a complete SOW with ALL of the following sections. Be specific and use data from the source material above.
Where data is missing, use professional placeholders that are clearly marked [TBD].

# Scope of Work — {account_name}

**Document Version:** 1.0
**Prepared:** {today}
**Valid Until:** [date = today + {validity_days} days]
**Status:** Draft

---

## 1. Executive Summary
[2-3 paragraphs: customer context, engagement purpose, expected outcomes]

## 2. Project Scope and Objectives
[Bullet list of in-scope objectives, tied to discovered pain points]

## 3. Key Deliverables
[For each deliverable: name, description, acceptance criteria]
Use this format:
### Deliverable N: [Name]
- **Description:** ...
- **Acceptance Criteria:** ...
- **Owner:** [Vendor/Customer]

## 4. Implementation Timeline
[Phased plan with milestones and weeks]
| Phase | Activities | Duration | Milestone |
|-------|-----------|----------|-----------|
[at least 3 phases]

## 5. Technical Requirements
[Infrastructure, integrations, security, data requirements from discovery]

## 6. Roles and Responsibilities
[Two-column: Customer responsibilities vs Vendor responsibilities]
| Customer | Vendor |
|---------|--------|
[at least 4 rows each]

## 7. Success Metrics
[KPIs and targets derived from discovery/ROI model]
| Metric | Baseline | Target | Measurement Method |
|--------|---------|--------|-------------------|

## 8. Assumptions and Dependencies
[Numbered list of assumptions this SOW is contingent on]

## 9. Out of Scope
[Bullet list of explicitly excluded items to prevent scope creep]

## 10. Commercial Terms
[Payment terms, validity, change order process, IP ownership]

---
*This SOW was auto-generated by JARVIS from account intelligence. Review and customize before sending to customer.*
"""

    messages = [
        Message(
            role="system",
            content=(
                "You are a senior professional services consultant and solutions architect. "
                "Generate precise, comprehensive Scope of Work documents. "
                "Be specific, use numbers and metrics where available, "
                "and clearly mark any assumptions or TBD items. "
                "Return the full SOW as markdown — no preamble, no commentary outside the document."
            ),
        ),
        Message(role="user", content=prompt),
    ]

    try:
        response = await llm.generate_with_routing(
            messages, task_type="reasoning", source="background"
        )
        if response.startswith("[LLM Error:"):
            logger.warning("LLM returned error for SOW, using fallback", account=account_name, error=response)
            return _fallback_sow(account_name, ctx)
        return response
    except Exception as e:
        logger.error("LLM call failed for SOW generation", account=account_name, error=str(e))
        return _fallback_sow(account_name, ctx)


def _fallback_sow(account_name: str, ctx: Dict[str, Any]) -> str:
    """Minimal SOW template when LLM is unavailable."""
    today = datetime.now().strftime("%Y-%m-%d")
    proposal = ctx.get("proposal", {})
    exec_summary = proposal.get("executive_summary", f"This SOW defines the engagement between the Vendor and {account_name}.")
    pain_points = proposal.get("pain_points", ["High manual workload", "Fragmented tooling", "Slow response times"])
    benefits = proposal.get("key_benefits", ["Automation of tier-1 queries", "Unified customer experience", "Measurable ROI within 90 days"])
    terms = proposal.get("terms", "Net 30")

    pain_list = "\n".join(f"- {p}" for p in pain_points)
    benefit_list = "\n".join(f"- {b}" for b in benefits)

    return f"""# Scope of Work — {account_name}

**Document Version:** 1.0
**Prepared:** {today}
**Status:** Draft — Pending LLM Enrichment

---

## 1. Executive Summary

{exec_summary}

This document defines the scope, deliverables, timeline, and responsibilities for the AI platform deployment at {account_name}.

---

## 2. Project Scope and Objectives

{pain_list}

The engagement is scoped to address the above with a phased AI automation deployment.

---

## 3. Key Deliverables

### Deliverable 1: AI-Powered Virtual Assistant (Phase 1 Use Cases)
- **Description:** Deployment of conversational AI for tier-1 query resolution
- **Acceptance Criteria:** Bot containment rate ≥ 60% on target use cases in UAT
- **Owner:** Vendor (with Customer UAT sign-off)

### Deliverable 2: Agent Handoff & Escalation Workflow
- **Description:** Configured escalation flows from bot to live agent with context transfer
- **Acceptance Criteria:** Zero context loss on escalation; agent receives full conversation history
- **Owner:** Vendor

### Deliverable 3: Analytics Dashboard & Reporting
- **Description:** Live reporting on containment rate, CSAT, and volume trends
- **Acceptance Criteria:** Dashboard available post-go-live; data refreshed ≤ 1 hour
- **Owner:** Vendor

### Deliverable 4: Training and Enablement
- **Description:** Admin training, agent training, and runbook documentation
- **Acceptance Criteria:** Customer team can independently manage bot content post-training
- **Owner:** Vendor

---

## 4. Implementation Timeline

| Phase | Activities | Duration | Milestone |
|-------|-----------|----------|-----------|
| Phase 1: Setup & Configuration | Environment provisioning, integration configuration, bot design | Weeks 1–3 | Sandbox deployment ready |
| Phase 2: Build & UAT | Use case development, testing, customer UAT | Weeks 4–6 | UAT sign-off |
| Phase 3: Go-Live | Production deployment, hypercare support | Week 7 | Go-live |
| Phase 4: Optimisation | Performance tuning, additional use cases | Weeks 8–12 | Optimisation report |

---

## 5. Technical Requirements

- Cloud environment access (Customer to provide API credentials for integrations)
- CRM / helpdesk integration endpoint (REST API or webhook)
- SSO / authentication configuration for agent console
- Data residency requirements: [TBD — confirm with Customer IT/Security]
- Security review timeline: [TBD — confirm with Customer procurement]

---

## 6. Roles and Responsibilities

| Customer | Vendor |
|---------|--------|
| Provide integration credentials and API access | Deliver configured platform per agreed use cases |
| Assign project sponsor and technical lead | Assign dedicated implementation engineer |
| Complete UAT testing within agreed window | Provide UAT scripts and support during testing |
| Approve go-live decision | Conduct hypercare for 2 weeks post go-live |
| Provide access to historical conversation data (anonymised) | Train AI models on customer-specific intent patterns |
| Manage internal change management and agent training logistics | Deliver training sessions and documentation |

---

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Bot Containment Rate | 0% (new deployment) | ≥ 60% | Platform analytics |
| Average Handle Time | [TBD — from discovery] | -30% | Helpdesk reporting |
| CSAT Score | [TBD — from discovery] | +10 points | Post-interaction survey |
| First Contact Resolution | [TBD] | +15% | Helpdesk reporting |
| Time-to-Respond | [TBD] | < 10 seconds (bot) | Platform logs |

{benefit_list}

---

## 8. Assumptions and Dependencies

1. Customer provides integration API access within 5 business days of contract execution
2. Customer assigns a dedicated project coordinator available ≥ 4 hours/week
3. UAT environment mirrors production configuration
4. Historical conversation data (minimum 3 months) is available for AI training
5. Customer security review is completed before production deployment
6. No major changes to integration endpoints during implementation period
7. Go-live decision authority rests with the Customer's named project sponsor

---

## 9. Out of Scope

- Custom hardware or on-premises infrastructure provisioning
- Third-party software licensing (CRM, telephony platform — Customer-owned)
- Ongoing content management post-hypercare period (covered under support SLA)
- Languages not agreed in the initial deployment plan
- Integration with systems not listed in Section 5 Technical Requirements
- Legal review of conversation logs or data compliance certification

---

## 10. Commercial Terms

- **Payment Terms:** {terms}
- **Document Validity:** 30 days from preparation date
- **Change Orders:** Any scope changes must be agreed in writing; additional effort quoted separately
- **IP Ownership:** Platform IP remains with Vendor; Customer retains ownership of conversation data
- **Confidentiality:** Both parties agree to mutual NDA terms as per the Master Agreement

---

*Auto-generated by JARVIS SOW Skill from account intelligence. Review all [TBD] items and customise before presenting to customer. Regenerates automatically when proposal, discovery, or value architecture is updated.*
"""
