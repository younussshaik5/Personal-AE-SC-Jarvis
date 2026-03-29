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
        self.event_bus.subscribe("account.initialized",     self._on_account_event)
        self.event_bus.subscribe("meeting.summary.ready",   self._on_account_event)
        self.event_bus.subscribe("document.processed",      self._on_account_event)
        self.event_bus.subscribe("brain.entry.routed",      self._on_account_event)
        self.event_bus.subscribe("meddpicc.updated",        self._on_account_event)
        self.event_bus.subscribe("email.added",             self._on_account_event)
        self.event_bus.subscribe("knowledge.intel.updated", self._on_account_event)
        self.event_bus.subscribe("file.created",             self._on_file_event)
        self.event_bus.subscribe("file.modified",            self._on_file_event)

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
        """Any account-level event → queue gap-fill for that account."""
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

        for gap in gaps:
            try:
                content = await kb._generate_intel(account, gap, context, llm)
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
                task_type="text", source="background"
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
    # Helpers
    # ------------------------------------------------------------------

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

    async def _generate_intel(self, account: str, gap: str, context: dict, llm) -> Optional[str]:
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
For each dimension below 2: what's missing, question to ask, who does it (AE vs SC).
Format as markdown.""",
        }
        base_gap = gap.replace("refresh_", "")
        prompt = gap_prompts.get(gap) or gap_prompts.get(base_gap)
        if not prompt:
            return None
        try:
            return await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text", source="background"
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
