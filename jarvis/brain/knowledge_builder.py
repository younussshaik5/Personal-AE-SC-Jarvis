#!/usr/bin/env python3
"""
KnowledgeBuilder — JARVIS autonomous gap-filling engine.

What this does:
  - Scans every account folder every 6 hours
  - Identifies what's MISSING (no company research, no competitive analysis, etc.)
  - Uses NVIDIA to autonomously research and fill those gaps
  - Watches the entire claude space workspace for ANY new/changed files
  - Extracts intelligence from everything it finds
  - Builds a cross-deal knowledge base in MEMORY/ that improves all future outputs
  - Self-feeds: the richer the context, the better NVIDIA's outputs, the richer the context

This is the "self-populating" engine. It doesn't wait for you.
It finds gaps, fills them, and makes itself smarter in the process.
"""

import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager


# Files JARVIS considers "complete" for an account
REQUIRED_INTEL_FILES = {
    "company_research.md",
    "competitive_analysis.md",
    "value_proposition.md",
}

# How old intel can be before it's refreshed (days)
INTEL_REFRESH_DAYS = 14


class KnowledgeBuilder:
    """
    Autonomously researches, fills gaps, and builds cross-deal intelligence.
    Runs continuously in the background using NVIDIA.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("brain.knowledge_builder")
        self._running = False
        self._gap_fill_task: Optional[asyncio.Task] = None
        self._workspace_scan_task: Optional[asyncio.Task] = None
        self._llm_client = None
        self._processed_files: Set[str] = set()

    async def start(self):
        self._running = True
        self._jarvis_home = Path(self.config.workspace_root)
        self._accounts_dir = self._jarvis_home / "ACCOUNTS"
        self._memory_dir = self._jarvis_home / "MEMORY"
        self._memory_dir.mkdir(parents=True, exist_ok=True)

        # Also watch the claude space working directory for intelligence
        self._claude_space = Path(os.environ.get(
            "CLAUDE_SPACE",
            str(Path.home() / "Documents" / "claude space")
        ))

        # Subscribe to events
        self.event_bus.subscribe("account.initialized", self._on_account_initialized)
        self.event_bus.subscribe("meeting.summary.ready", self._on_new_intelligence)
        self.event_bus.subscribe("document.processed", self._on_new_intelligence)
        self.event_bus.subscribe("brain.entry.routed", self._on_new_intelligence)

        # Start background loops
        self._gap_fill_task = asyncio.create_task(self._gap_fill_loop())
        self._workspace_scan_task = asyncio.create_task(self._workspace_scan_loop())

        self.logger.info("KnowledgeBuilder started",
                         jarvis_home=str(self._jarvis_home),
                         claude_space=str(self._claude_space))

    async def stop(self):
        self._running = False
        for task in (self._gap_fill_task, self._workspace_scan_task):
            if task and not task.done():
                task.cancel()

    # ------------------------------------------------------------------
    # Gap fill loop — runs every 6 hours
    # ------------------------------------------------------------------

    async def _gap_fill_loop(self):
        """Every 6 hours: scan all accounts, fill missing intelligence."""
        while self._running:
            await asyncio.sleep(6 * 3600)
            try:
                await self._fill_all_gaps()
            except Exception as e:
                self.logger.error("Gap fill loop error", error=str(e))

    async def _fill_all_gaps(self):
        """Scan every account, identify gaps, fill them with NVIDIA."""
        if not self._accounts_dir.exists():
            return

        accounts = [d for d in self._accounts_dir.iterdir()
                    if d.is_dir() and not d.name.startswith(('_', '.'))]

        self.logger.info("Scanning for intelligence gaps", accounts=len(accounts))
        filled = 0

        for account_dir in accounts:
            gaps = self._identify_gaps(account_dir)
            for gap in gaps:
                success = await self._fill_gap(account_dir, gap)
                if success:
                    filled += 1
                await asyncio.sleep(2)  # rate limiting between API calls

        if filled:
            self.logger.info("Intelligence gaps filled", count=filled)
            self.event_bus.publish(Event(
                type="knowledge.gaps.filled",
                source="brain.knowledge_builder",
                data={"count": filled}
            ))

    def _identify_gaps(self, account_dir: Path) -> List[str]:
        """Return list of gap types for an account."""
        gaps = []
        intel_dir = account_dir / "INTEL"
        intel_dir.mkdir(exist_ok=True)

        for required_file in REQUIRED_INTEL_FILES:
            file_path = intel_dir / required_file
            if not file_path.exists():
                gaps.append(required_file.replace(".md", ""))
            else:
                # Check if stale
                age_days = (datetime.now() - datetime.fromtimestamp(
                    file_path.stat().st_mtime
                )).days
                if age_days > INTEL_REFRESH_DAYS:
                    gaps.append(f"refresh_{required_file.replace('.md', '')}")

        # Check for missing MEDDPICC notes
        meddpicc = self._read_json(account_dir / "meddpicc.json")
        if meddpicc and meddpicc.get("score", 0) > 0:
            if not (intel_dir / "meddpicc_strategy.md").exists():
                gaps.append("meddpicc_strategy")

        return gaps

    async def _fill_gap(self, account_dir: Path, gap: str) -> bool:
        """Fill a specific intelligence gap using NVIDIA."""
        llm = self._get_llm_client()
        if not llm:
            return False

        account_name = account_dir.name
        context = self._build_account_context(account_dir)

        gap_prompts = {
            "company_research": f"""Research {account_name} as a potential enterprise software customer.

Based on any available context:
{context}

Generate a company intelligence brief covering:
1. Company overview (industry, size, revenue if known)
2. Digital transformation maturity
3. Likely pain points for customer experience / support automation
4. Key decision-making dynamics (enterprise vs startup culture)
5. Budget signals and fiscal year timing
6. Technology stack indicators
7. Competitive landscape they operate in
8. Why they would buy conversational AI NOW

Be specific and practical. Focus on what an AE needs to know before a discovery call.
Write as markdown.""",

            "competitive_analysis": f"""Generate competitive positioning for selling to {account_name}.

Account context:
{context}

Based on the account profile, generate:
1. Most likely competitors in this evaluation (rank top 3)
2. For each competitor: their likely pitch vs our differentiation
3. Objections we'll face and how to handle them
4. Our strongest angles for this specific account type
5. Deal-killers to watch for

Focus on Yellow.ai vs alternatives. Be specific, not generic.
Write as markdown.""",

            "value_proposition": f"""Build a value proposition for {account_name}.

Account context:
{context}

Generate:
1. Primary business value (what problem does this solve for THEM specifically)
2. Quantified ROI framework (use industry benchmarks if no account-specific data)
3. 3 headline statements tailored to this account's industry/size
4. Executive-level business case (CFO language)
5. Technical value for IT/procurement stakeholders

Write as markdown.""",

            "meddpicc_strategy": f"""Generate a MEDDPICC pursuit strategy for {account_name}.

Current MEDDPICC status:
{context}

For each MEDDPICC element that's incomplete (score < 2):
1. What question reveals this information?
2. Which meeting/touchpoint is the right moment to ask?
3. What red flags indicate a problem here?
4. What action unblocks this element?

Be specific to this deal, not generic advice.
Write as markdown.""",
        }

        # Handle refresh variants
        base_gap = gap.replace("refresh_", "")
        prompt = gap_prompts.get(base_gap) or gap_prompts.get(gap)
        if not prompt:
            return False

        try:
            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text",
                source="background",
            )

            # Write to INTEL/
            output_filename = f"{base_gap}.md"
            intel_dir = account_dir / "INTEL"
            intel_dir.mkdir(exist_ok=True)
            output_file = intel_dir / output_filename

            header = (
                f"# {base_gap.replace('_', ' ').title()} — {account_name}\n"
                f"*Auto-generated by JARVIS KnowledgeBuilder — {datetime.now().strftime('%Y-%m-%d')}*\n"
                f"*Refresh every {INTEL_REFRESH_DAYS} days*\n\n---\n\n"
            )
            output_file.write_text(header + response, encoding="utf-8")

            self.logger.info("Gap filled", account=account_name, gap=base_gap)
            return True

        except Exception as e:
            self.logger.warning("Gap fill failed", account=account_name,
                                gap=gap, error=str(e))
            return False

    # ------------------------------------------------------------------
    # Workspace scan loop — watches claude space for any new intelligence
    # ------------------------------------------------------------------

    async def _workspace_scan_loop(self):
        """
        Periodically scan the claude space workspace for new or changed files.
        Extracts intelligence from ANYTHING found — playbooks, guides, notes,
        conversation artifacts — and routes it into the knowledge base.
        """
        while self._running:
            await asyncio.sleep(300)  # every 5 minutes
            try:
                await self._scan_workspace()
            except Exception as e:
                self.logger.error("Workspace scan error", error=str(e))

    async def _scan_workspace(self):
        """Scan claude space for new files with extractable intelligence."""
        if not self._claude_space.exists():
            return

        scan_patterns = ["**/*.md", "**/*.txt", "**/*.pdf", "**/*.docx"]
        skip_dirs = {".git", "__pycache__", "node_modules", "dist",
                     "ACCOUNTS", "MEETINGS", "INTEL", ".processed"}

        for pattern in scan_patterns:
            for file_path in self._claude_space.glob(pattern):
                # Skip if inside jarvis data dirs or already processed
                if any(skip in file_path.parts for skip in skip_dirs):
                    continue
                if str(file_path) in self._processed_files:
                    continue

                # Only process files modified in the last 24 hours
                try:
                    age_hours = (datetime.now() - datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    )).total_seconds() / 3600
                    if age_hours > 24:
                        continue
                except Exception:
                    continue

                await self._extract_from_workspace_file(file_path)
                self._processed_files.add(str(file_path))

                # Keep set bounded
                if len(self._processed_files) > 1000:
                    self._processed_files = set(list(self._processed_files)[-500:])

    async def _extract_from_workspace_file(self, file_path: Path):
        """Extract intelligence from a workspace file using NVIDIA."""
        llm = self._get_llm_client()
        if not llm:
            return

        try:
            text = self._read_file_text(file_path)
            if not text or len(text.strip()) < 100:
                return

            prompt = f"""You are analyzing a file from a sales professional's workspace.
File: {file_path.name}

Extract ONLY what's useful for an enterprise sales AE:
1. Account names mentioned (if any)
2. Sales strategies, playbook patterns, or methodologies
3. Product knowledge (Yellow.ai features, use cases, pricing signals)
4. Competitive insights
5. Any customer pain points or buying signals

If this file contains no sales-relevant information, return: {{"relevant": false}}

Otherwise return JSON:
{{
  "relevant": true,
  "accounts": [],
  "insights": [],
  "product_knowledge": [],
  "competitive": [],
  "save_to": "playbook|product|competitive|account"
}}

File content (first 3000 chars):
{text[:3000]}"""

            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text",
                source="background",
            )

            parsed = self._extract_json(response)
            if not parsed or not parsed.get("relevant"):
                return

            # Route to knowledge base
            await self._route_workspace_intelligence(file_path, parsed, text)

        except Exception as e:
            self.logger.debug("Workspace file extraction failed",
                              file=file_path.name, error=str(e))

    async def _route_workspace_intelligence(
        self, file_path: Path, extracted: Dict, raw_text: str
    ):
        """Save extracted workspace intelligence to the right memory location."""
        save_to = extracted.get("save_to", "general")
        memory_subdir = self._memory_dir / save_to
        memory_subdir.mkdir(parents=True, exist_ok=True)

        # Save to appropriate memory category
        output_name = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d')}.json"
        output_file = memory_subdir / output_name
        output_file.write_text(json.dumps({
            "source_file": str(file_path),
            "extracted": datetime.now().isoformat(),
            **extracted
        }, indent=2))

        # If specific accounts mentioned → also route to account folders
        for account_name in extracted.get("accounts", []):
            account_dir = self._accounts_dir / account_name
            if account_dir.exists():
                intel_dir = account_dir / "INTEL"
                intel_dir.mkdir(exist_ok=True)
                note_file = intel_dir / f"workspace_note_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
                note_file.write_text(
                    f"# Intelligence from workspace: {file_path.name}\n"
                    f"*Extracted by JARVIS — {datetime.now().strftime('%Y-%m-%d')}*\n\n"
                    + "\n".join(f"- {i}" for i in extracted.get("insights", []))
                )

        # Build cumulative knowledge base
        await self._update_knowledge_base(save_to, extracted)

        self.logger.info("Workspace intelligence extracted",
                         file=file_path.name, category=save_to)

    async def _update_knowledge_base(self, category: str, extracted: Dict):
        """
        Maintain a rolling knowledge base in MEMORY/.
        This is what gets injected into NVIDIA prompts to make them smarter over time.
        The more context accumulates, the better every output gets.
        """
        kb_file = self._memory_dir / f"knowledge_base_{category}.md"

        insights = extracted.get("insights", [])
        product_knowledge = extracted.get("product_knowledge", [])
        competitive = extracted.get("competitive", [])

        if not any([insights, product_knowledge, competitive]):
            return

        with open(kb_file, "a", encoding="utf-8") as f:
            f.write(f"\n<!-- {datetime.now().strftime('%Y-%m-%d')} -->\n")
            for item in insights:
                f.write(f"- {item}\n")
            for item in product_knowledge:
                f.write(f"- [PRODUCT] {item}\n")
            for item in competitive:
                f.write(f"- [COMPETITIVE] {item}\n")

    # ------------------------------------------------------------------
    # Cross-deal pattern building
    # ------------------------------------------------------------------

    async def build_cross_deal_patterns(self):
        """
        Synthesize patterns across ALL deals in ACCOUNTS/.
        What separates wins from losses? What actions move deals fastest?
        Stored in MEMORY/patterns.md — injected into future prompts.
        """
        llm = self._get_llm_client()
        if not llm:
            return

        # Collect deal summaries
        deal_summaries = []
        if self._accounts_dir.exists():
            for account_dir in self._accounts_dir.iterdir():
                if not account_dir.is_dir():
                    continue
                stage_data = self._read_json(account_dir / "deal_stage.json")
                meddpicc = self._read_json(account_dir / "meddpicc.json")
                if stage_data:
                    deal_summaries.append({
                        "account": account_dir.name,
                        "stage": stage_data.get("stage"),
                        "stage_history": stage_data.get("history", []),
                        "meddpicc_score": meddpicc.get("score", 0) if meddpicc else 0,
                    })

        if len(deal_summaries) < 2:
            return  # Not enough data yet

        prompt = f"""Analyze these sales deals and identify patterns:

{json.dumps(deal_summaries, indent=2)[:4000]}

Identify:
1. Which MEDDPICC scores correlate with deals advancing fastest?
2. Which stages are deals stalling in most?
3. What's the average time in each stage?
4. What patterns appear in deals that progress vs stall?
5. Recommended actions for each stage based on this data.

Write practical, specific insights an AE can act on.
Format as markdown."""

        try:
            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text",
                source="background",
            )
            patterns_file = self._memory_dir / "patterns.md"
            patterns_file.write_text(
                f"# Cross-Deal Patterns\n"
                f"*Generated {datetime.now().strftime('%Y-%m-%d')} from {len(deal_summaries)} deals*\n\n"
                + response,
                encoding="utf-8"
            )
            self.logger.info("Cross-deal patterns updated", deals=len(deal_summaries))
        except Exception as e:
            self.logger.warning("Pattern building failed", error=str(e))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_account_initialized(self, event: Event):
        """New account created — immediately start filling intelligence gaps."""
        account_name = event.data.get("account_name", "")
        if account_name:
            await asyncio.sleep(5)  # let initializer finish first
            account_dir = self._accounts_dir / account_name
            if account_dir.exists():
                gaps = self._identify_gaps(account_dir)
                for gap in gaps:
                    await self._fill_gap(account_dir, gap)
                    await asyncio.sleep(2)

    async def _on_new_intelligence(self, event: Event):
        """New intelligence arrived — rebuild cross-deal patterns if enough data."""
        # Throttle: only rebuild patterns every 10 new intelligence events
        if not hasattr(self, '_intel_count'):
            self._intel_count = 0
        self._intel_count += 1
        if self._intel_count >= 10:
            self._intel_count = 0
            asyncio.create_task(self.build_cross_deal_patterns())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_account_context(self, account_dir: Path) -> str:
        """Build a context string from all available account data."""
        parts = []

        # MEDDPICC
        m = self._read_json(account_dir / "meddpicc.json")
        if m:
            parts.append(f"MEDDPICC score: {m.get('score', 0)}/8")

        # Deal stage
        s = self._read_json(account_dir / "deal_stage.json")
        if s:
            parts.append(f"Stage: {s.get('stage', 'unknown')}")

        # Contacts
        c = self._read_json(account_dir / "contacts.json")
        if c and c.get("contacts"):
            names = [f"{x.get('name')} ({x.get('role', '')})"
                     for x in c["contacts"][:5]]
            parts.append(f"Known contacts: {', '.join(names)}")

        # Existing INTEL snippets
        intel_dir = account_dir / "INTEL"
        if intel_dir.exists():
            for f in list(intel_dir.glob("*.md"))[:3]:
                snippet = f.read_text(encoding="utf-8")[:300]
                parts.append(f"Existing intel ({f.stem}): {snippet}")

        return "\n".join(parts) if parts else f"Account: {account_dir.name} — no data yet"

    def _get_llm_client(self):
        if not self._llm_client:
            try:
                from jarvis.llm.llm_client import LLMClient
                self._llm_client = LLMClient(self.config)
            except Exception:
                pass
        return self._llm_client

    def _read_json(self, path: Path) -> Optional[Dict]:
        try:
            return json.loads(path.read_text()) if path.exists() else None
        except Exception:
            return None

    def _extract_json(self, text: str) -> Optional[Dict]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _read_file_text(self, path: Path) -> str:
        try:
            if path.suffix.lower() in (".txt", ".md"):
                return path.read_text(encoding="utf-8", errors="ignore")
            if path.suffix.lower() == ".docx":
                import zipfile, xml.etree.ElementTree as ET
                with zipfile.ZipFile(path) as z:
                    with z.open("word/document.xml") as f:
                        tree = ET.parse(f)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                return " ".join(n.text for n in tree.findall(".//w:t", ns) if n.text)
        except Exception:
            pass
        return ""
