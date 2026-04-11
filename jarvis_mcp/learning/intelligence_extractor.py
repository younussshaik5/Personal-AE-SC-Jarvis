"""
IntelligenceExtractor — LLM-powered extraction of sales intel from ANY text.

Accepts: skill outputs, dropped files, chat messages, emails, transcripts,
         SOW content, proposals, PPT notes, anything with text.

Returns a structured intel delta — only NEW facts, nothing generic.
The KnowledgeMerger then appends this to discovery.md.

This closes the feedback loop:
  - Skill outputs contain new intel → extracted → merged back into discovery.md
  - Dropped files contain new intel → extracted → merged → cascade fires
  - Chat messages contain new intel → extracted → merged → cascade fires
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """You are a sales intelligence extractor for a B2B deal.

Analyze the text below and extract ONLY concrete, new, actionable facts about the deal.

Return a markdown summary with ONLY sections that contain actual new information.
Omit any section where you found nothing. Be concise — no filler, no generic advice.

Sections to look for:

### New Stakeholders
Name, title, role in decision (champion / economic buyer / technical evaluator / blocker)

### Pain Points & Problems
Specific business problems, frustrations, bottlenecks mentioned with any quantification

### Requirements & Success Criteria
Explicit requirements, must-haves, evaluation criteria

### Metrics & ROI Signals
Any numbers: cost savings, productivity gains, headcount, revenue, timelines, percentages

### Competitors Mentioned
Competitor names, their status (evaluating / eliminated / incumbent / preferred)

### Timeline & Deadlines
Contract dates, go-live targets, decision dates, budget cycles

### Budget & ARR Signals
Budget confirmed/range, approval authority, fiscal year constraints

### Champion & Sponsor Signals
Who is advocating internally, who has access to power, who is engaged vs passive

### Decision Process
Procurement steps, approval chain, security/legal review status, who signs

### Technical Requirements
Integrations needed, security requirements, compliance, data requirements, architecture

### Risks & Blockers
Objections raised, concerns expressed, political blockers, competitive threats

---

TEXT TO ANALYZE:
{text}

---

Return ONLY the sections with actual findings. If nothing useful was found, return exactly:
NO_NEW_INTEL
"""


class IntelligenceExtractor:
    """
    Extracts structured sales intel from any text using an LLM.
    Used by: file watcher (new files), queue worker (skill outputs), mcp_server (chat).
    """

    def __init__(self, llm_manager):
        self.llm = llm_manager

    async def extract(
        self,
        text: str,
        source: str = "unknown",
        max_chars: int = 8000,
    ) -> Optional[str]:
        """
        Extract intel from text. Returns markdown string of findings,
        or None if nothing useful was found.

        source: human-readable label for logging (e.g. "file:notes.txt", "skill:sow")
        """
        if not text or not text.strip():
            return None

        # Truncate very long inputs — keep the most recent content (tail)
        if len(text) > max_chars:
            text = text[-max_chars:]

        prompt = _EXTRACTION_PROMPT.format(text=text.strip())

        try:
            result = await self.llm.generate(
                prompt=prompt,
                model_type="fast",   # extraction is a fast task
                max_tokens=1200,
                system_prompt=(
                    "You are a precise sales intelligence extractor. "
                    "Extract only concrete, specific facts. Never invent or generalize. "
                    "If the text contains no useful deal intelligence, say NO_NEW_INTEL."
                ),
            )
        except Exception as e:
            log.warning(f"[extractor] LLM call failed for {source}: {e}")
            return None

        if not result or result.strip() == "NO_NEW_INTEL" or result.strip().startswith("❌"):
            log.debug(f"[extractor] No new intel found in {source}")
            return None

        log.info(f"[extractor] Intel extracted from {source} ({len(result)} chars)")
        return result.strip()
