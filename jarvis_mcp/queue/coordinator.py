"""
BriefCoordinator — progressive context enrichment engine.

After each skill completes, the coordinator:
  1. Extracts key findings from the skill output (pure text — no LLM)
  2. Appends them to intelligence_brief.md as a LIVE DELTA block
  3. Every downstream skill now reads a richer brief than the skill before it

On the next Nemotron synthesis run, Nemotron reads the brief including all
accumulated deltas → absorbs them into a clean new base → deltas cleared.

No LLM calls. No extra API usage. Pure file I/O with an asyncio lock
so parallel skills never corrupt the brief file.

Execution order effect:
  Wave 1 skills (meddpicc, battlecard) → read Nemotron BASE brief
    → meddpicc completes → delta appended → brief now has meddpicc findings
  Wave 2 skills (risk_report, demo_strategy) → read BASE + meddpicc delta
    → battlecard completes → delta appended → brief has meddpicc + battlecard
  Wave 3 skills (proposal, meeting_prep) → read BASE + wave 1 + wave 2 deltas
"""

import re
import asyncio
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

# Skills whose outputs contain meaningful key findings worth appending
DELTA_SKILLS = {
    "meddpicc", "battlecard", "competitive_intelligence", "risk_report",
    "value_architecture", "technical_risk", "discovery", "account_summary",
    "company_research", "meeting_prep", "demo_strategy", "quick_insights",
    "competitor_pricing", "proposal",
}

# Skills whose output format is unsuitable for key findings extraction
SKIP_DELTA = {
    "intelligence_brief",     # IS the brief — never delta itself
    "html_generator",         # raw HTML
    "architecture_diagram",   # mermaid diagram code
    "knowledge_builder",      # graph data
    "conversation_extractor", # raw extraction output
    "conversation_summarizer","meeting_summary",
    "followup_email",         # email draft — no key findings
    "sow",                    # contract — no key findings
    "documentation",
    "custom_template",
}

# DELTAS section marker — everything below this line is auto-appended
_DELTA_MARKER = "## ── LIVE SKILL DELTAS"
_DELTA_HEADER = (
    "\n\n---\n"
    f"{_DELTA_MARKER}\n"
    "*Auto-appended by coordinator after each skill completes. "
    "Absorbed and cleared on next Nemotron synthesis run.*\n"
)


def extract_key_findings(skill_name: str, content: str, max_bullets: int = 10) -> str:
    """
    Extract key findings from skill output — pure text processing, no LLM.
    Returns up to max_bullets bullet points of the most important signals.
    """
    if not content or len(content.strip()) < 100:
        return ""

    lines = content.split("\n")
    findings = []
    seen = set()

    def add(line: str) -> None:
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line).strip()
        clean = re.sub(r"\*(.+?)\*", r"\1", clean)
        clean = re.sub(r"`(.+?)`", r"\1", clean)
        clean = re.sub(r"\s+", " ", clean)
        if not clean or clean in seen or len(clean) < 15:
            return
        seen.add(clean)
        bullet = clean if clean.startswith("- ") else f"- {clean}"
        findings.append(bullet[:220])

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Bullet points
        m = re.match(r"^[-*•]\s+(.{10,})", stripped)
        if m:
            add(m.group(1))
            continue

        # Numbered list
        m = re.match(r"^\d+\.\s+(.{10,})", stripped)
        if m:
            add(m.group(1))
            continue

        # Score/Status/Rating lines (MEDDPICC specific)
        if re.match(r"^\*{0,2}(Score|Status|Level|Rating|Verdict|Severity)\*{0,2}\s*[:—–]", stripped, re.I):
            add(stripped)
            continue

        # Section heading that contains RED/AMBER/GREEN verdict
        if re.match(r"^#{1,4}", stripped) and re.search(r"\b(RED|AMBER|GREEN|HIGH|MEDIUM|LOW)\b", stripped):
            clean_heading = re.sub(r"^#{1,4}\s*", "", stripped)
            add(clean_heading)
            continue

        if len(findings) >= max_bullets:
            break

    # Fallback: if we got too few, pull first substantive sentence from each section
    if len(findings) < 3:
        current_section = None
        for line in lines:
            stripped = line.strip()
            if re.match(r"^#{1,4}\s+.+", stripped):
                current_section = re.sub(r"^#{1,4}\s*", "", stripped)[:60]
                continue
            if current_section and stripped and len(stripped) > 25 and not stripped.startswith("#"):
                clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
                add(f"[{current_section}] {clean[:160]}")
                current_section = None  # one per section
            if len(findings) >= max_bullets:
                break

    return "\n".join(findings[:max_bullets])


class BriefCoordinator:
    """
    Appends skill deltas to intelligence_brief.md immediately after each
    skill completes. Called by QueueWorker — no blocking, fire-and-forget.
    """

    def __init__(self, config_manager):
        self.config = config_manager
        # Per-account locks — prevent concurrent writes to the same file
        self._locks: dict = {}

    def _get_lock(self, account_name: str) -> asyncio.Lock:
        if account_name not in self._locks:
            self._locks[account_name] = asyncio.Lock()
        return self._locks[account_name]

    async def append_delta(self, account_name: str, skill_name: str, output: str) -> None:
        """
        Extract key findings and append to intelligence_brief.md.
        Safe to call concurrently — per-account asyncio lock prevents corruption.
        """
        if skill_name in SKIP_DELTA:
            return
        if skill_name not in DELTA_SKILLS:
            return
        if not output or output.strip().startswith("❌"):
            return

        findings = extract_key_findings(skill_name, output)
        if not findings:
            log.debug(f"[coordinator] no extractable findings from {skill_name} ({account_name})")
            return

        brief_path = self.config.get_account_path(account_name) / "intelligence_brief.md"
        if not brief_path.exists():
            log.debug(f"[coordinator] no brief yet for {account_name} — skipping delta")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        label = skill_name.upper().replace("_", " ")
        delta_block = f"\n### [{timestamp}] {label}\n{findings}\n"

        async with self._get_lock(account_name):
            try:
                current = brief_path.read_text(encoding="utf-8")

                if _DELTA_MARKER not in current:
                    # First delta — add the section header
                    brief_path.write_text(
                        current + _DELTA_HEADER + delta_block,
                        encoding="utf-8",
                    )
                else:
                    # Append to existing DELTAS section
                    with open(brief_path, "a", encoding="utf-8") as f:
                        f.write(delta_block)

                log.info(
                    f"[coordinator] ✓ {skill_name} delta → "
                    f"{account_name}/intelligence_brief.md "
                    f"({len(findings.splitlines())} findings)"
                )
            except Exception as e:
                log.warning(f"[coordinator] delta append failed ({skill_name}/{account_name}): {e}")

    async def clear_deltas(self, account_name: str) -> None:
        """
        Remove the LIVE DELTAS section from intelligence_brief.md.
        Called by IntelligenceBriefSkill before writing a fresh Nemotron synthesis
        (deltas are absorbed into the new base — no longer needed separately).
        """
        brief_path = self.config.get_account_path(account_name) / "intelligence_brief.md"
        if not brief_path.exists():
            return

        async with self._get_lock(account_name):
            try:
                current = brief_path.read_text(encoding="utf-8")
                if _DELTA_MARKER not in current:
                    return
                # Keep only the BASE section (everything before the DELTAS marker)
                base = current.split(f"\n\n---\n{_DELTA_MARKER}")[0].rstrip()
                brief_path.write_text(base + "\n", encoding="utf-8")
                log.info(f"[coordinator] cleared deltas from {account_name}/intelligence_brief.md")
            except Exception as e:
                log.warning(f"[coordinator] clear_deltas failed ({account_name}): {e}")
