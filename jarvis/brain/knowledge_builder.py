#!/usr/bin/env python3
"""
KnowledgeBuilder — JARVIS autonomous intelligence engine.

How it works:
  - Subscribes to events: account.initialized, meeting.summary.ready,
    document.processed, brain.entry.routed, file.created/modified in claude_space
  - On each event → queues gap-fill and workspace-extract tasks immediately
  - Workers pick up tasks within 1-5 minutes (rate-limited to protect NVIDIA quota)
  - No fixed 6-hour loops. Everything is event-driven.

Task types registered:
  "gap_fill"          — fill missing INTEL/ files for one account (NVIDIA)
  "workspace_extract" — extract sales intel from a file in claude_space (NVIDIA)
  "cross_deal_sync"   — synthesize patterns across all accounts (NVIDIA, LOW priority)
  "html_refresh"      — regenerate account.html or opp.html (no LLM needed)

Context is never lost:
  Full account context is passed in the task payload (JSON).
  Handler reads current state from disk, calls NVIDIA, writes result to disk.
  If NVIDIA fails → task retries up to 3 times (WorkerPool handles this).
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.queue.task_queue import TaskQueue, TaskPriority

REQUIRED_INTEL_FILES = {
    "company_research.md",
    "competitive_analysis.md",
    "value_proposition.md",
}

INTEL_REFRESH_DAYS = 14

WORKSPACE_FILE_EXTS = {".md", ".txt", ".pdf", ".docx", ".json"}
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".processed",
               "dist", "logs", "MEMORY", "data"}


class KnowledgeBuilder:
    """
    Queues intelligence tasks whenever anything changes.
    Workers process them in parallel within 1-5 minutes.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config     = config_manager
        self.event_bus  = event_bus
        self.logger     = JARVISLogger("brain.knowledge_builder")
        self._running   = False
        self._queue: Optional[TaskQueue] = None

    async def start(self):
        self._running = True
        self._jarvis_home  = Path(self.config.workspace_root)
        self._accounts_dir = self._jarvis_home / "ACCOUNTS"
        self._memory_dir   = self._jarvis_home / "MEMORY"
        self._memory_dir.mkdir(parents=True, exist_ok=True)

        # claude_space resolved from config (set via .env CLAUDE_SPACE=)
        cs = getattr(self.config, "claude_space", None)
        self._claude_space = Path(cs) if cs else None

        # Task queue (shared singleton via jarvis_home path)
        self._queue = TaskQueue(self._jarvis_home)

        # Subscribe to semantic events — queue tasks immediately
        self.event_bus.subscribe("account.initialized",      self._on_account_event)
        self.event_bus.subscribe("meeting.summary.ready",    self._on_account_event)
        self.event_bus.subscribe("document.processed",       self._on_account_event)
        self.event_bus.subscribe("brain.entry.routed",       self._on_account_event)
        self.event_bus.subscribe("meddpicc.updated",         self._on_account_event)
        self.event_bus.subscribe("email.added",              self._on_account_event)
        self.event_bus.subscribe("knowledge.intel.updated",  self._on_account_event)
        self.event_bus.subscribe("file.created",             self._on_file_event)
        self.event_bus.subscribe("file.modified",            self._on_file_event)
        # Presales section events — cascade refreshes
        self.event_bus.subscribe("account.sections.created",   self._on_sections_created)
        self.event_bus.subscribe("discovery.updated",          self._on_discovery_updated)
        self.event_bus.subscribe("meddpicc.updated",           self._on_meddpicc_updated_presales)
        # RFP source file ready → queue fill_rfi task
        self.event_bus.subscribe("rfi.source.ready",           self._on_rfi_source_ready)
        # Presales file dropped → cascade specific section refreshes
        self.event_bus.subscribe("presales.cascade.requested", self._on_presales_cascade)

        # On startup: queue gap-fill for every existing account (LOW priority)
        await self._queue_all_account_gaps()

        # Queue cross-deal synthesis on startup (lowest priority)
        await self._queue.enqueue(
            "cross_deal_sync", payload={}, priority=TaskPriority.LOW,
            dedup_key="cross_deal_sync"
        )

        self.logger.info("KnowledgeBuilder started",
                         accounts_dir=str(self._accounts_dir),
                         claude_space=str(self._claude_space))

    async def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # Event handlers — translate events into queued tasks immediately
    # ------------------------------------------------------------------

    async def _on_account_event(self, event: Event):
        """Any account-level event → queue gap-fill + relevant presales refreshes."""
        account = (event.data.get("account") or
                   event.data.get("account_name") or "")
        if not account:
            return
        await self._queue.enqueue(
            "gap_fill",
            payload={"account": account},
            account=account,
            priority=TaskPriority.MEDIUM,
        )
        # Also refresh HTML after any data change
        await self._queue.enqueue(
            "html_refresh",
            payload={"account": account, "level": "account"},
            account=account,
            dedup_key=f"html_refresh:{account}",
            priority=TaskPriority.LOW,
        )
        # On meeting summary or document processed → cascade presales refreshes
        if event.type in ("meeting.summary.ready", "document.processed"):
            for task_type in ("fill_discovery", "fill_demo_strategy",
                              "fill_risk_report", "fill_next_steps"):
                await self._queue.enqueue(
                    task_type,
                    payload={"account": account},
                    account=account,
                    priority=TaskPriority.MEDIUM,
                    dedup_key=f"{task_type}:{account}:{event.type}",
                )

    async def _on_sections_created(self, event: Event):
        """When 7 presales folders are created → queue initial population of all sections."""
        account = event.data.get("account_name", "")
        if not account:
            return
        # Queue all presales sections at LOW priority (background population)
        for task_type in ("fill_discovery", "fill_battlecard", "fill_demo_strategy",
                          "fill_risk_report", "fill_next_steps", "fill_value_architecture"):
            await self._queue.enqueue(
                task_type,
                payload={"account": account},
                account=account,
                priority=TaskPriority.LOW,
                dedup_key=f"{task_type}:{account}:init",
            )

    async def _on_discovery_updated(self, event: Event):
        """Discovery updated → refresh demo strategy + value architecture."""
        account = event.data.get("account", "") or event.data.get("account_name", "")
        if not account:
            return
        for task_type in ("fill_demo_strategy", "fill_value_architecture"):
            await self._queue.enqueue(
                task_type,
                payload={"account": account},
                account=account,
                priority=TaskPriority.MEDIUM,
                dedup_key=f"{task_type}:{account}:discovery_cascade",
            )

    async def _on_meddpicc_updated_presales(self, event: Event):
        """MEDDPICC changed → refresh discovery prep + risk report + value architecture."""
        account = event.data.get("account", "") or event.data.get("account_name", "")
        if not account:
            return
        for task_type in ("fill_discovery", "fill_risk_report", "fill_value_architecture"):
            await self._queue.enqueue(
                task_type,
                payload={"account": account},
                account=account,
                priority=TaskPriority.MEDIUM,
                dedup_key=f"{task_type}:{account}:meddpicc_cascade",
            )

    async def _on_rfi_source_ready(self, event: Event):
        """RFP source file extracted by DocumentProcessor → queue fill_rfi task."""
        account = event.data.get("account", "")
        path = event.data.get("path", "")
        if not account:
            return
        await self._queue.enqueue(
            "fill_rfi",
            payload={"account": account, "path": path},
            account=account,
            priority=TaskPriority.HIGH,
            dedup_key=f"fill_rfi:{account}:{path}",
        )
        self.logger.info("RFP fill task queued", account=account)

    async def _on_presales_cascade(self, event: Event):
        """File dropped into a presales section → cascade-refresh relevant downstream sections."""
        account = event.data.get("account", "")
        task_name = event.data.get("task", "")
        if not account or not task_name:
            return
        await self._queue.enqueue(
            task_name,
            payload={"account": account},
            account=account,
            priority=TaskPriority.MEDIUM,
            dedup_key=f"{task_name}:{account}:presales_cascade",
        )

    async def _on_file_event(self, event: Event):
        """File changed in claude_space → queue workspace extraction."""
        path_str = event.data.get("path", "")
        if not path_str:
            return
        path = Path(path_str)

        # Only care about files in claude_space
        if self._claude_space and not path_str.startswith(str(self._claude_space)):
            return

        # Skip JARVIS_HOME itself (avoid feedback loops)
        if path_str.startswith(str(self._jarvis_home)):
            return

        if path.suffix.lower() not in WORKSPACE_FILE_EXTS:
            return

        # Skip ignored dirs
        if any(part in IGNORE_DIRS for part in path.parts):
            return

        await self._queue.enqueue(
            "workspace_extract",
            payload={"path": path_str},
            dedup_key=f"workspace_extract:{path_str}",
            priority=TaskPriority.MEDIUM,
        )

    # ------------------------------------------------------------------
    # Startup: queue gaps for all existing accounts
    # ------------------------------------------------------------------

    async def _queue_all_account_gaps(self):
        if not self._accounts_dir.exists():
            return
        count = 0
        for account_dir in self._accounts_dir.iterdir():
            if account_dir.is_dir() and not account_dir.name.startswith(("_", ".")):
                await self._queue.enqueue(
                    "gap_fill",
                    payload={"account": account_dir.name},
                    account=account_dir.name,
                    priority=TaskPriority.LOW,
                )
                count += 1
        if count:
            self.logger.info("Queued gap-fill for existing accounts", count=count)

    # ------------------------------------------------------------------
    # Task handlers — called by WorkerPool
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_gap_fill(task, services: Dict[str, Any]):
        """Fill missing INTEL/ files for one account."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return

        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return

        intel_dir = account_dir / "INTEL"
        intel_dir.mkdir(exist_ok=True)

        gaps = kb._identify_gaps(account_dir)
        if not gaps:
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)

        # Use long_context model when there's a lot of account data to analyse
        context_json = json.dumps(context)
        gap_task_type = "long_context" if len(context_json) > 10000 else "text"

        for gap in gaps:
            try:
                content = await kb._generate_intel(account, gap, context, llm, gap_task_type)
                if content:
                    fname = gap.replace("refresh_", "") + ".md"
                    (intel_dir / fname).write_text(content, encoding="utf-8")
                    kb.logger.info("Intel filled", account=account, gap=gap)
                    kb.event_bus.publish(Event(
                        type="knowledge.intel.updated",
                        source="brain.knowledge_builder",
                        data={"account": account, "file": fname}
                    ))
            except Exception as e:
                kb.logger.error("Gap fill failed", account=account, gap=gap, error=str(e))

    @staticmethod
    async def handle_workspace_extract(task, services: Dict[str, Any]):
        """Extract sales intel from any file in claude_space."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        path_str = task.payload.get("path", "")
        if not path_str:
            return
        path = Path(path_str)
        if not path.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        try:
            text = kb._read_file_text(path)
            if len(text.strip()) < 100:
                return

            prompt = f"""Extract sales intelligence from this file.
File: {path.name}

Content:
{text[:4000]}

Return JSON with these fields (omit any that are not present):
{{
  "accounts": ["company names mentioned"],
  "insights": ["key business insights, pain points, needs"],
  "product_knowledge": ["yellow.ai product/feature knowledge"],
  "competitive": ["competitor mentions or comparisons"],
  "action_items": ["any action items or next steps"]
}}"""

            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text", source="background"
            )
            parsed = kb._extract_json(response)
            if not parsed:
                return

            # Write to MEMORY knowledge base
            for category, items in parsed.items():
                if items:
                    kb._update_knowledge_base(category, items, source=path.name)

            # Route to relevant accounts
            for acct_name in parsed.get("accounts", []):
                matched = kb._fuzzy_match_account(acct_name)
                if matched:
                    intel_path = kb._accounts_dir / matched / "INTEL" / "workspace_intel.md"
                    kb._append_intel(intel_path, text[:2000], source=path.name)
                    kb.event_bus.publish(Event(
                        type="knowledge.intel.updated",
                        source="brain.knowledge_builder",
                        data={"account": matched, "file": "workspace_intel.md"}
                    ))

            kb.logger.debug("Workspace file extracted", path=path.name)

        except Exception as e:
            kb.logger.error("Workspace extract failed", path=path_str, error=str(e))

    @staticmethod
    async def handle_cross_deal_sync(task, services: Dict[str, Any]):
        """Synthesize patterns across all accounts → MEMORY/patterns/cross_deal_insights.md"""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        llm = kb._get_llm_client()
        if not llm:
            return
        if not kb._accounts_dir.exists():
            return

        accounts_context = []
        for account_dir in kb._accounts_dir.iterdir():
            if account_dir.is_dir() and not account_dir.name.startswith(("_", ".")):
                ctx = kb._build_account_context(account_dir)
                if ctx.get("meddpicc_score", 0) > 0:
                    accounts_context.append(ctx)

        if len(accounts_context) < 2:
            return

        prompt = f"""Analyze patterns across {len(accounts_context)} active sales deals.

Deal summaries:
{json.dumps(accounts_context[:10], indent=2)[:5000]}

Identify:
1. Common pain points appearing across multiple deals
2. Which MEDDPICC dimensions are consistently weak
3. Competitive patterns (who keeps showing up)
4. Stage progression bottlenecks
5. One specific playbook recommendation

Return JSON: {{"patterns": [], "weak_meddpicc": [], "competitive": [], "bottlenecks": [], "recommendation": ""}}"""

        try:
            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="reasoning", source="background"
            )
            parsed = kb._extract_json(response)
            if parsed:
                out = kb._memory_dir / "patterns" / "cross_deal_insights.md"
                out.parent.mkdir(exist_ok=True)
                lines = [f"# Cross-Deal Intelligence — {datetime.now().strftime('%Y-%m-%d')}\n"]
                for k, v in parsed.items():
                    if v:
                        lines.append(f"## {k.replace('_', ' ').title()}")
                        if isinstance(v, list):
                            lines.extend(f"- {item}" for item in v)
                        else:
                            lines.append(str(v))
                        lines.append("")
                out.write_text("\n".join(lines), encoding="utf-8")
                kb.logger.info("Cross-deal patterns updated")
        except Exception as e:
            kb.logger.error("Cross-deal sync failed", error=str(e))

        # Re-queue for next run (1 hour later at LOW priority)
        await kb._queue.enqueue(
            "cross_deal_sync", payload={}, priority=TaskPriority.LOW,
            dedup_key="cross_deal_sync"
        )

    # ------------------------------------------------------------------
    # Presales section handlers — called by WorkerPool
    # Each writes to account's presales folder + publishes cascade event
    # All paths via config.workspace_root — zero hardcoding
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_fill_discovery(task, services: Dict[str, Any]):
        """Generate/refresh DISCOVERY/discovery_prep.md from company intel + MEDDPICC gaps + web research."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        discovery_dir = account_dir / "DISCOVERY"
        if not discovery_dir.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        # Enrich context with live web research
        web_research = await kb._fetch_web_research(account)
        context["web_research"] = web_research

        meddpicc = context.get("meddpicc", {})
        weak_dims = [dim for dim in ("metrics", "economic_buyer", "decision_criteria",
                                     "decision_process", "paper_process", "implicate_pain",
                                     "champion", "competition")
                     if meddpicc.get(dim, 0) < 2]

        intel_context = kb._read_intel_files(account_dir)

        prompt = f"""You are a Sales + Presales expert preparing for a discovery call with {account}.

Company intel:
{json.dumps(web_research, indent=2)[:2000]}

MEDDPICC status:
{json.dumps(meddpicc, indent=2)}

Weak MEDDPICC dimensions (score < 2): {weak_dims}

Known intel from files:
{intel_context[:1500]}

Generate a comprehensive discovery prep document in markdown:

## Company Background
(2-3 sentences: industry, size, what they do, why they'd need AI/automation)

## Top 10 Discovery Questions
(industry-specific, open-ended, pain-focused)

## MEDDPICC Gap Questions
(for each weak dimension: 2 questions that fill the gap)

## Stakeholders to Target
(roles to engage based on deal stage)

## Competitive Trap Questions
(questions that expose competitor weaknesses without naming them directly)

## Key Pain Points from Intel
(summarized from what JARVIS already knows)"""

        try:
            content = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text", source="background"
            )
            if content:
                (discovery_dir / "discovery_prep.md").write_text(
                    f"# Discovery Prep — {account}\n\n"
                    f"*Auto-generated by JARVIS — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
                    f"---\n\n{content}",
                    encoding="utf-8"
                )
                kb.logger.info("Discovery prep generated", account=account)
                kb.event_bus.publish(Event(
                    type="discovery.updated",
                    source="brain.knowledge_builder",
                    data={"account": account, "file": "discovery_prep.md"}
                ))
        except Exception as e:
            kb.logger.error("fill_discovery failed", account=account, error=str(e))

    @staticmethod
    async def handle_fill_battlecard(task, services: Dict[str, Any]):
        """Generate/refresh BATTLECARD/battlecard.md + battlecard_data.json via web research + Step 3.5 Flash reasoning."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        bc_dir = account_dir / "BATTLECARD"
        if not bc_dir.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        web_research = await kb._fetch_web_research(account)
        competitive_intel = kb._read_text(account_dir / "INTEL" / "competitive_analysis.md")
        contacts = context.get("contacts", {}).get("contacts", [])

        prompt = f"""You are a competitive intelligence expert. Create a battlecard for the deal with {account}.

Company context from web research:
{json.dumps(web_research, indent=2)[:1500]}

Competitive analysis intel:
{competitive_intel[:1500]}

Contacts/roles at {account}:
{json.dumps(contacts[:5], indent=2)}

Return a JSON object with this exact structure:
{{
  "differentiators": ["top 5 unique selling points"],
  "competitors": [
    {{
      "name": "Competitor name",
      "weaknesses": ["weakness 1", "weakness 2"],
      "trap_questions": ["question that exposes this competitor without naming them"],
      "g2_positioning": "1-line G2 sentiment summary"
    }}
  ],
  "objections": [
    {{"objection": "common objection", "response": "counter response"}}
  ],
  "stakeholder_messaging": [
    {{"role": "CTO/CFO/etc", "key_message": "what resonates with them"}}
  ],
  "win_probability": "Low/Medium/High",
  "win_themes": ["theme 1", "theme 2"]
}}"""

        try:
            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="reasoning", source="background"
            )
            import re
            match = re.search(r"\{.*\}", response, re.DOTALL)
            bc_data = json.loads(match.group(0)) if match else {}
            bc_data["account"] = account
            bc_data["generated_at"] = datetime.now().isoformat()

            # Write JSON
            (bc_dir / "battlecard_data.json").write_text(
                json.dumps(bc_data, indent=2), encoding="utf-8"
            )

            # Write readable markdown
            md_lines = [f"# Battlecard — {account}\n",
                        f"*Auto-generated by JARVIS — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n"]
            md_lines.append("## Our Top Differentiators\n")
            for d in bc_data.get("differentiators", []):
                md_lines.append(f"- {d}")
            md_lines.append("\n## Competitors\n")
            for c in bc_data.get("competitors", []):
                md_lines.append(f"### {c.get('name', 'Unknown')}")
                md_lines.append(f"**Weaknesses:** {', '.join(c.get('weaknesses', []))}")
                md_lines.append(f"**G2:** {c.get('g2_positioning', '')}")
                md_lines.append("**Trap Questions:**")
                for q in c.get("trap_questions", []):
                    md_lines.append(f"- {q}")
                md_lines.append("")
            md_lines.append("## Objection Handling\n")
            for o in bc_data.get("objections", []):
                md_lines.append(f"**{o.get('objection')}**")
                md_lines.append(f"→ {o.get('response')}\n")
            md_lines.append(f"\n## Win Probability: {bc_data.get('win_probability', 'TBD')}\n")

            (bc_dir / "battlecard.md").write_text("\n".join(md_lines), encoding="utf-8")
            kb.logger.info("Battlecard generated", account=account)
            kb.event_bus.publish(Event(
                type="battlecard.updated",
                source="brain.knowledge_builder",
                data={"account": account}
            ))
        except Exception as e:
            kb.logger.error("fill_battlecard failed", account=account, error=str(e))

    @staticmethod
    async def handle_fill_demo_strategy(task, services: Dict[str, Any]):
        """Generate DEMO_STRATEGY/demo_strategy.md + demo_script.md from discovery + intel."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        demo_dir = account_dir / "DEMO_STRATEGY"
        if not demo_dir.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        final_discovery = kb._read_text(account_dir / "DISCOVERY" / "final_discovery.md")
        value_prop = kb._read_text(account_dir / "INTEL" / "value_proposition.md")
        bc_data_text = kb._read_text(account_dir / "BATTLECARD" / "battlecard_data.json")
        contacts = context.get("contacts", {}).get("contacts", [])

        prompt = f"""You are a presales expert building a demo strategy for {account}.

Final discovery notes:
{final_discovery[:2000] if final_discovery and 'Generating' not in final_discovery else 'Not yet available — use company intel'}

Value proposition intel:
{value_prop[:1000]}

Battlecard context:
{bc_data_text[:500]}

Key contacts:
{json.dumps(contacts[:5], indent=2)}

Generate:

# Demo Strategy — {account}

## Narrative Hook
(1-2 sentences: the pain story that opens the demo)

## 40-Minute Demo Flow
1. Discovery Recap (5 min) — confirm pain, set agenda
2. Platform Overview (10 min) — the "aha" moment
3. AI Capabilities (10 min) — show what they asked about
4. Competitive Differentiation (5 min) — landmine-free
5. ROI & Business Value (5 min) — their numbers
6. Next Steps (5 min) — clear ask

## Use Cases to Demo
(specific to {account}'s stated requirements)

## Competitive Landmines to Avoid
(what NOT to say that competitors could use against us)

## Personalization Checklist
- [ ] Use {account} logo in slides
- [ ] Reference their industry metrics
- [ ] Use their terminology from discovery calls
- [ ] Show use case they mentioned explicitly"""

        try:
            strategy = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="reasoning", source="background"
            )
            if strategy:
                (demo_dir / "demo_strategy.md").write_text(
                    f"*Auto-generated by JARVIS — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{strategy}",
                    encoding="utf-8"
                )

            # Generate script only if discovery exists
            if final_discovery and "Generating" not in final_discovery:
                script_prompt = f"""Based on this demo strategy for {account}, write a line-by-line demo script.

Strategy:
{strategy[:2000] if strategy else 'See demo_strategy.md'}

Format each section as:
**[SLIDE/SCREEN]:** what to show
**[SAY]:** exact words
**[IF OBJECTION]:** how to handle

Keep it natural, not robotic. Include 3 transition phrases between sections."""

                script = await llm.generate_with_routing(
                    messages=[{"role": "user", "content": script_prompt}],
                    task_type="reasoning", source="background"
                )
                if script:
                    (demo_dir / "demo_script.md").write_text(
                        f"# Demo Script — {account}\n\n"
                        f"*Auto-generated by JARVIS — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
                        f"---\n\n{script}",
                        encoding="utf-8"
                    )

            kb.logger.info("Demo strategy generated", account=account)
            kb.event_bus.publish(Event(
                type="demo.strategy.updated",
                source="brain.knowledge_builder",
                data={"account": account}
            ))
        except Exception as e:
            kb.logger.error("fill_demo_strategy failed", account=account, error=str(e))

    @staticmethod
    async def handle_fill_risk_report(task, services: Dict[str, Any]):
        """Auto-fill RISK_REPORT/risk_report.md using activities + MEDDPICC + web risk signals."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        risk_dir = account_dir / "RISK_REPORT"
        if not risk_dir.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        meddpicc = context.get("meddpicc", {})
        contacts = context.get("contacts", {}).get("contacts", [])
        activities = context.get("recent_activities", [])
        actions = kb._read_text(account_dir / "actions.md")

        # Count activities by type
        activity_counts = {}
        for act in activities:
            atype = act.get("type", "other")
            activity_counts[atype] = activity_counts.get(atype, 0) + 1

        # Identify weak MEDDPICC dimensions
        weak_dims = [(dim, meddpicc.get(dim, 0)) for dim in
                     ("metrics", "economic_buyer", "decision_criteria", "decision_process",
                      "paper_process", "implicate_pain", "champion", "competition")
                     if meddpicc.get(dim, 0) < 2]

        discovery_md = kb._read_text(account_dir / "DISCOVERY" / "final_discovery.md")
        intel_text = kb._read_text(account_dir / "INTEL" / "company_research.md")

        # Get web risk signals
        web_research = await kb._fetch_web_research(account, query_type="risks")

        prompt = f"""Fill this risk report template for {account}. Use only facts from the data provided.

Account data:
- Contacts met: {[c.get('name', '') + ' (' + c.get('title', '') + ')' for c in contacts[:5]]}
- Activity counts: {activity_counts}
- MEDDPICC weak dimensions: {weak_dims}
- Discovery notes excerpt: {discovery_md[:500] if discovery_md else 'None'}
- Company intel excerpt: {intel_text[:500] if intel_text else 'None'}
- Outstanding actions: {actions[:500] if actions else 'None'}
- Web risk signals: {json.dumps(web_research, indent=2)[:500] if web_research else 'None'}

Fill in the template below. Where data is missing, write "Unknown — needs discovery".

## Top 3 Technical Use Cases
1.
2.
3.

## 3 Challenges We Are Solving
1. [Challenge] → [How we solve it]
2.
3.

## What Have We Done So Far
SE activities: ({activity_counts.get('discovery', 0)}) Discovery, ({activity_counts.get('demo', 0)}) Demo, ({activity_counts.get('poc', 0)}) POC, ({activity_counts.get('rfp', 0)}) RFP, ({activity_counts.get('competitive', 0)}) Competitive

## Stakeholders
Met: (from contacts)
Upcoming: (from calendar / next steps)

## Outstanding / Next Steps
(from actions.md)

## Technical Gaps/Risks
MEDDPICC dimensions below 2: (list them)
Web risk signals: (layoffs, budget freeze, M&A etc)
Product gaps: (any requirements we can't meet)"""

        try:
            # Stage 1: Minitron 8B generates the report (fast, structured template fill)
            draft = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="quick", source="background"
            )
            if not draft or draft.startswith("[LLM Error:"):
                kb.logger.warning("Risk report quick draft failed, skipping", account=account)
                return

            # Stage 2: Step 3.5 Flash validates and improves (only if quality differs)
            validation_prompt = f"""You are reviewing a risk report draft for account: {account}.

DRAFT:
{draft}

Review the draft and:
1. Fix any factual inconsistencies or missing information based on the data provided
2. Improve clarity and completeness where needed
3. If the draft is already accurate and complete, respond with exactly: APPROVED

If you make improvements, return only the improved report — no preamble.
If approved, return exactly: APPROVED"""

            validated = await llm.generate_with_routing(
                messages=[{"role": "user", "content": validation_prompt}],
                task_type="reasoning", source="background"
            )

            # Use validated version if Step 3.5 Flash improved it; else keep draft
            if validated and not validated.startswith("[LLM Error:") and validated.strip() != "APPROVED":
                final_report = validated.strip()
                kb.logger.info("Risk report improved by validation stage", account=account)
            else:
                final_report = draft
                kb.logger.info("Risk report draft approved unchanged", account=account)

            now = datetime.now()
            # Append entry to existing risk_report.md (never overwrite)
            existing = kb._read_text(risk_dir / "risk_report.md") or ""
            entry = (f"\n\n---\n\n## {now.strftime('%Y-%m-%d')} — Weekly Update\n\n"
                     f"**Owner:** SE\n\n{final_report}")
            (risk_dir / "risk_report.md").write_text(
                existing.rstrip() + entry, encoding="utf-8"
            )
            kb.logger.info("Risk report updated", account=account)
            kb.event_bus.publish(Event(
                type="risk.report.updated",
                source="brain.knowledge_builder",
                data={"account": account}
            ))
        except Exception as e:
            kb.logger.error("fill_risk_report failed", account=account, error=str(e))

    @staticmethod
    async def handle_fill_next_steps(task, services: Dict[str, Any]):
        """Generate NEXT_STEPS/next_steps.md with stage-appropriate email drafts."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        ns_dir = account_dir / "NEXT_STEPS"
        if not ns_dir.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        stage = context.get("deal_stage", {}).get("stage", "new_account")
        contacts = context.get("contacts", {}).get("contacts", [])
        primary_contact = contacts[0] if contacts else {}
        actions = kb._read_text(account_dir / "actions.md")

        stage_intents = {
            "new_account": "initial outreach / setting up discovery call",
            "discovery": "following up on discovery call with summary and next steps",
            "demo": "thank you for the demo + next steps to advance",
            "proposal": "following up on proposal / handling objections",
            "negotiation": "working toward agreement / removing blockers",
            "closed_won": "congratulations + onboarding next steps",
            "closed_lost": "post-loss check-in to keep relationship warm",
        }
        intent = stage_intents.get(stage, "following up to advance the deal")

        prompt = f"""Write 2 email draft options for {account} at {stage} stage.

Intent: {intent}
Primary contact: {primary_contact.get('name', '[Contact Name]')} — {primary_contact.get('title', '')}
Outstanding actions: {actions[:300] if actions else 'None'}

For each email draft:
Subject: [Subject line]
Body: [Email body — personalized, concise, clear next action]

Make them sound human, not templated. Reference actual deal context where possible.
Draft A: More direct/assertive
Draft B: More consultative/soft touch"""

        try:
            drafts_text = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text", source="background"
            )
            if drafts_text:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                (ns_dir / "next_steps.md").write_text(
                    f"# Next Steps & Email Drafts — {account}\n\n"
                    f"*Auto-generated by JARVIS — {now}*\n"
                    f"*Current stage: {stage.replace('_', ' ').title()}*\n\n"
                    f"---\n\n{drafts_text}",
                    encoding="utf-8"
                )
                # Update JSON index
                drafts_json = {"account": account, "generated_at": now,
                               "current_stage": stage, "drafts": [drafts_text]}
                (ns_dir / "email_drafts.json").write_text(
                    json.dumps(drafts_json, indent=2), encoding="utf-8"
                )
                kb.logger.info("Next steps generated", account=account)
                kb.event_bus.publish(Event(
                    type="next_steps.updated",
                    source="brain.knowledge_builder",
                    data={"account": account, "stage": stage}
                ))
        except Exception as e:
            kb.logger.error("fill_next_steps failed", account=account, error=str(e))

    @staticmethod
    async def handle_fill_value_architecture(task, services: Dict[str, Any]):
        """Generate VALUE_ARCHITECTURE/ files: ROI model, TCO, value_data.json via long-context + web research."""
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        va_dir = account_dir / "VALUE_ARCHITECTURE"
        if not va_dir.exists():
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        meddpicc = context.get("meddpicc", {})
        discovery_notes = kb._read_text(account_dir / "DISCOVERY" / "final_discovery.md")
        value_prop = kb._read_text(account_dir / "INTEL" / "value_proposition.md")
        web_research = await kb._fetch_web_research(account)

        metrics_from_discovery = meddpicc.get("notes", {}).get("metrics", "")
        company_size = web_research.get("company_size", "Unknown")

        prompt = f"""Build a value architecture for {account}.

Company size: {company_size}
Discovery metrics mentioned: {metrics_from_discovery or 'Not captured yet'}
Value proposition intel: {value_prop[:800] if value_prop else 'None'}
Discovery notes: {discovery_notes[:800] if discovery_notes and 'Generating' not in discovery_notes else 'None yet'}

Generate two sections:

## ROI Model — {account}

### Scenario: Conservative (Year 1)
- Efficiency gain: X%
- Cost reduction: $X
- Revenue impact: $X
- Total ROI: X%
- Payback period: X months

### Scenario: Realistic (Year 1)
[same structure]

### Scenario: Optimistic (Year 1)
[same structure]

### Key Assumptions
[list assumptions used]

---

## TCO Analysis — {account}

### Current Stack (estimated)
[tools they likely use, estimated annual cost]

### With Our Solution
[our pricing + implementation + maintenance]

### 3-Year Total Savings
[calculation]

### ROI Summary
[1-paragraph executive summary]"""

        try:
            va_content = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="long_context", source="background"
            )
            if va_content:
                # Split into ROI and TCO sections
                if "## TCO Analysis" in va_content:
                    parts = va_content.split("## TCO Analysis")
                    roi_part = parts[0]
                    tco_part = "## TCO Analysis" + parts[1]
                else:
                    roi_part = va_content
                    tco_part = ""

                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                (va_dir / "roi_model.md").write_text(
                    f"# ROI Model — {account}\n*Auto-generated by JARVIS — {now}*\n\n---\n\n{roi_part}",
                    encoding="utf-8"
                )
                if tco_part:
                    (va_dir / "tco_analysis.md").write_text(
                        f"# TCO Analysis — {account}\n*Auto-generated by JARVIS — {now}*\n\n---\n\n{tco_part}",
                        encoding="utf-8"
                    )
                # Update value_data.json
                value_data = {"account": account, "generated_at": now,
                              "status": "generated",
                              "metrics": {"company_size": company_size},
                              "web_research_used": bool(web_research)}
                (va_dir / "value_data.json").write_text(
                    json.dumps(value_data, indent=2), encoding="utf-8"
                )
                kb.logger.info("Value architecture generated", account=account)
                kb.event_bus.publish(Event(
                    type="value_architecture.updated",
                    source="brain.knowledge_builder",
                    data={"account": account}
                ))
        except Exception as e:
            kb.logger.error("fill_value_architecture failed", account=account, error=str(e))

    @staticmethod
    async def handle_fill_rfi(task, services: Dict[str, Any]):
        """Fill an RFI: reads original source file, generates a new filled copy using Nemotron 120B.

        Input:  Original RFI document (PDF/DOCX/TXT) in ACCOUNTS/{account}/RFI/
        Output: {original_name}_filled.md  — new copy with responses filled in
                rfi_analysis.md            — requirements map + evaluation breakdown
                rfi_responses.md           — structured Q&A responses
        """
        kb: "KnowledgeBuilder" = services["knowledge_builder"]
        account = task.payload.get("account", "")
        if not account:
            return
        account_dir = kb._accounts_dir / account
        if not account_dir.exists():
            return
        rfi_dir = account_dir / "RFI"
        if not rfi_dir.exists():
            return

        # Find the source RFI file from the task payload, or find the latest one in the folder
        source_path_str = task.payload.get("path", "")
        if source_path_str:
            source_file = Path(source_path_str)
        else:
            # Find the most recent non-generated RFI file
            candidates = [
                f for f in rfi_dir.iterdir()
                if f.is_file()
                and f.suffix.lower() in {".pdf", ".docx", ".doc", ".txt", ".md"}
                and "_filled" not in f.stem
                and f.name not in {"rfi_analysis.md", "rfi_responses.md", "README.md"}
            ]
            if not candidates:
                kb.logger.warning("No source RFP file found", account=account)
                return
            source_file = max(candidates, key=lambda f: f.stat().st_mtime)

        if not source_file.exists():
            kb.logger.warning("RFP source file missing", path=str(source_file))
            return

        # Read the source RFP text (already extracted by DocumentProcessor)
        rfp_text = kb._read_text(source_file) or ""
        if not rfp_text and source_file.suffix.lower() == ".md":
            rfp_text = source_file.read_text(encoding="utf-8", errors="ignore")

        if not rfp_text or len(rfp_text.strip()) < 100:
            kb.logger.warning("RFP source text too short to process", account=account)
            return

        llm = kb._get_llm_client()
        if not llm:
            return

        context = kb._build_account_context(account_dir)
        intel = kb._read_intel_files(account_dir)
        discovery_notes = kb._read_text(account_dir / "DISCOVERY" / "final_discovery.md")
        battlecard_data = kb._read_text(account_dir / "BATTLECARD" / "battlecard.md")
        web_research = await kb._fetch_web_research(account)

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # --- Step 1: Analyze RFP — extract structure and requirements ---
        analysis_prompt = f"""You are a Solution Consultant analyzing an RFP for {account}.

RFP Content:
{rfp_text}

Extract and structure the following:
1. All requirements (mandatory and optional), numbered
2. Evaluation criteria and scoring weights (if stated)
3. Submission deadline and key dates
4. Budget range (if stated)
5. Likely competitors being evaluated
6. Key decision makers mentioned
7. Top 5 win themes we must address
8. MEDDPICC signals: decision process, paper process, metrics mentioned

Return as structured markdown with clear section headers."""

        # RFPs can be large — use Nemotron 120B (1M token window)
        analysis = await llm.generate_with_routing(
            messages=[{"role": "user", "content": analysis_prompt}],
            task_type="long_context", source="background"
        )

        if not analysis or analysis.startswith("[LLM Error:"):
            kb.logger.error("RFP analysis generation failed", account=account)
            return

        (rfi_dir / "rfi_analysis.md").write_text(
            f"# RFP Analysis — {account}\n*Auto-generated by JARVIS — {now}*\n"
            f"**Source file:** {source_file.name}\n\n---\n\n{analysis}",
            encoding="utf-8"
        )
        kb.logger.info("RFP analysis written", account=account)

        # --- Step 2: Generate responses for each requirement ---
        responses_prompt = f"""You are an Account Executive + Solution Consultant responding to an RFP for {account}.

RFP ANALYSIS (requirements and evaluation criteria):
{analysis[:4000]}

OUR CONTEXT:
- Company intel: {intel[:1000] if intel else 'See discovery notes'}
- Discovery notes: {discovery_notes[:800] if discovery_notes and 'Generating' not in discovery_notes else 'None yet'}
- Competitive positioning: {battlecard_data[:800] if battlecard_data and 'Generating' not in battlecard_data else 'None yet'}
- Web research: {str(web_research)[:400]}

Generate a complete response document for this RFP. For each requirement:
1. Confirm compliance (Fully Compliant / Partially Compliant / Requires Customization)
2. Provide a specific response (2-4 sentences)
3. Reference relevant capabilities or proof points

Format as a professional RFP response document. Be specific, confident, and concrete."""

        filled_content = await llm.generate_with_routing(
            messages=[{"role": "user", "content": responses_prompt}],
            task_type="long_context", source="background"
        )

        if not filled_content or filled_content.startswith("[LLM Error:"):
            kb.logger.error("RFP response generation failed", account=account)
            return

        # Write rfi_responses.md (structured Q&A)
        (rfi_dir / "rfi_responses.md").write_text(
            f"# RFP Responses — {account}\n*Auto-generated by JARVIS — {now}*\n"
            f"**Source file:** {source_file.name}\n\n---\n\n{filled_content}",
            encoding="utf-8"
        )

        # Write the filled copy — same logical structure as original, with responses inline
        filled_copy_name = f"{source_file.stem}_filled.md"
        filled_copy_path = rfi_dir / filled_copy_name
        filled_copy_path.write_text(
            f"# {source_file.stem} — Filled Copy\n"
            f"**Account:** {account}  \n"
            f"**Generated:** {now}  \n"
            f"**Source:** {source_file.name}  \n\n"
            f"---\n\n"
            f"## Original RFP\n\n{rfp_text[:8000]}\n\n"
            f"---\n\n"
            f"## Our Responses\n\n{filled_content}",
            encoding="utf-8"
        )

        kb.logger.info("RFP filled copy written", account=account, file=filled_copy_name)
        kb.event_bus.publish(Event(
            type="rfi.processed",
            source="brain.knowledge_builder",
            data={"account": account, "filled_copy": str(filled_copy_path)}
        ))
        # Also trigger battlecard refresh — RFP reveals competitors and decision criteria
        await kb._queue.enqueue(
            "fill_battlecard",
            payload={"account": account},
            account=account,
            priority=TaskPriority.MEDIUM,
            dedup_key=f"fill_battlecard:{account}:rfp_cascade",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_web_research(account: str, query_type: str = "company") -> dict:
        """Fetch live web research for an account using DuckDuckGo.
        Returns dict with company intel — used by all presales skill handlers."""
        try:
            import aiohttp
            from urllib.parse import quote_plus
            import re as _re

            results = {}
            queries = {
                "company": [
                    f"{account} company industry size overview 2025",
                    f"{account} technology stack CRM tools customer service",
                    f"{account} revenue growth employees 2024 2025",
                ],
                "risks": [
                    f"{account} layoff budget freeze 2024 2025",
                    f"{account} merger acquisition leadership change",
                ],
            }
            search_queries = queries.get(query_type, queries["company"])
            snippets = []

            async with aiohttp.ClientSession() as session:
                for query in search_queries:
                    try:
                        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                        headers = {
                            "User-Agent": "Mozilla/5.0 (JARVIS/2.0; Sales Intelligence Bot)"
                        }
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                            if resp.status == 200:
                                html = await resp.text()
                                found = _re.findall(
                                    r'<a class="result__snippet">(.*?)</a>', html, _re.DOTALL
                                )
                                for s in found[:3]:
                                    clean = _re.sub(r"<[^>]+>", "", s).strip()
                                    if clean:
                                        snippets.append(clean)
                    except Exception:
                        pass

            results["raw_snippets"] = snippets[:8]
            results["account"] = account
            results["fetched_at"] = datetime.now().isoformat()

            # Basic extractions from snippets
            text = " ".join(snippets).lower()
            results["company_size"] = (
                "Enterprise (10000+)" if any(x in text for x in ["billion", "10,000", "100,000"]) else
                "Mid-Market (1000-10000)" if any(x in text for x in ["thousand", "1,000"]) else
                "SMB (<1000)"
            )
            return results
        except Exception:
            return {"account": account, "raw_snippets": [], "company_size": "Unknown"}

    def _read_intel_files(self, account_dir: Path) -> str:
        """Read all INTEL/ markdown files and return concatenated text (truncated)."""
        intel_dir = account_dir / "INTEL"
        if not intel_dir.exists():
            return ""
        parts = []
        for f in intel_dir.glob("*.md"):
            try:
                parts.append(f"### {f.stem}\n{f.read_text(encoding='utf-8', errors='ignore')[:500]}")
            except Exception:
                pass
        return "\n\n".join(parts)[:3000]

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8") if path.exists() else ""
        except Exception:
            return ""

    def _identify_gaps(self, account_dir: Path) -> List[str]:
        gaps = []
        intel_dir = account_dir / "INTEL"
        intel_dir.mkdir(exist_ok=True)
        for required_file in REQUIRED_INTEL_FILES:
            fp = intel_dir / required_file
            if not fp.exists():
                gaps.append(required_file.replace(".md", ""))
            else:
                age = (datetime.now() - datetime.fromtimestamp(fp.stat().st_mtime)).days
                if age > INTEL_REFRESH_DAYS:
                    gaps.append(f"refresh_{required_file.replace('.md', '')}")
        meddpicc = self._read_json(account_dir / "meddpicc.json")
        if meddpicc and meddpicc.get("score", 0) > 0:
            if not (account_dir / "INTEL" / "meddpicc_strategy.md").exists():
                gaps.append("meddpicc_strategy")
        return gaps

    async def _generate_intel(self, account: str, gap: str, context: dict, llm, task_type: str = "text") -> Optional[str]:
        gap_prompts = {
            "company_research": f"""Research {account} as a potential enterprise software buyer.
Context we already have: {json.dumps(context, indent=2)[:1000]}
Write a concise company profile covering industry, size, tech stack, digital maturity, recent news, and why {account} might need conversational AI.
Format as markdown.""",
            "competitive_analysis": f"""Generate competitive positioning for selling to {account}.
Context: {json.dumps(context, indent=2)[:1000]}
Cover likely competitors, our differentiation, objections and counters, win themes.
Format as markdown.""",
            "value_proposition": f"""Build a tailored value proposition for {account}.
Context: {json.dumps(context, indent=2)[:1000]}
Include business value in their language, 3 ROI scenarios, champion talking points, executive summary.
Format as markdown.""",
            "meddpicc_strategy": f"""Given MEDDPICC data for {account}, recommend specific actions.
MEDDPICC: {json.dumps(context.get('meddpicc', {}), indent=2)}
For each dimension below 2: what's missing, question to ask, who does it.
Format as markdown.""",
        }
        base_gap = gap.replace("refresh_", "")
        prompt = gap_prompts.get(gap) or gap_prompts.get(base_gap)
        if not prompt:
            return None
        try:
            return await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type=task_type, source="background"
            )
        except Exception as e:
            self.logger.error("Intel generation failed", gap=gap, error=str(e))
            return None

    def _build_account_context(self, account_dir: Path) -> dict:
        ctx: Dict[str, Any] = {"account": account_dir.name}
        for fname in ("meddpicc.json", "deal_stage.json", "contacts.json"):
            data = self._read_json(account_dir / fname)
            if data:
                ctx[fname.replace(".json", "")] = data
        if "meddpicc" in ctx:
            ctx["meddpicc_score"] = ctx["meddpicc"].get("score", 0)
        activities_file = account_dir / "activities.jsonl"
        if activities_file.exists():
            lines = activities_file.read_text().splitlines()[-10:]
            ctx["recent_activities"] = [json.loads(l) for l in lines if l.strip()]
        return ctx

    def _fuzzy_match_account(self, name: str) -> Optional[str]:
        import difflib
        if not self._accounts_dir.exists():
            return None
        accounts = [d.name for d in self._accounts_dir.iterdir()
                    if d.is_dir() and not d.name.startswith(("_", "."))]
        matches = difflib.get_close_matches(name, accounts, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def _update_knowledge_base(self, category: str, items: list, source: str):
        kb_file = self._memory_dir / f"knowledge_{category}.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"\n### From `{source}` — {timestamp}"]
        lines.extend(f"- {item}" for item in items)
        with open(kb_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _append_intel(self, path: Path, content: str, source: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n\n### {source} — {timestamp}\n{content}\n")

    def _read_file_text(self, path: Path) -> str:
        try:
            if path.suffix == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(path))
                    return "\n".join(p.extract_text() or "" for p in reader.pages)
                except ImportError:
                    pass
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _read_json(self, path: Path) -> Optional[dict]:
        try:
            return json.loads(path.read_text()) if path.exists() else None
        except Exception:
            return None

    def _extract_json(self, text: str) -> Optional[dict]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _get_llm_client(self):
        try:
            from jarvis.llm.llm_client import LLMClient
            return LLMClient(self.config)
        except Exception:
            return None
