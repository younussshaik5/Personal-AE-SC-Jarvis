"""
Fast programmatic quality checker for JARVIS skill output.
No LLM calls — pure text heuristics, runs in microseconds.
"""

from typing import Dict, Any

# Lines that start with these prefixes are NOT real content
_HEADING_PREFIX = "#"
_SEPARATOR_PREFIX = "---"
_NO_DATA_PREFIX = "_No data generated"

# Reasoning leak indicators — if a line starts with (case-insensitive), it's thinking, not output
_REASONING_STARTERS = (
    "we need to",
    "i need to",
    "let me ",
    "okay, i",
    "okay i",
    "first, ",
    "to write the",
    "to generate the",
    "to produce",
    "from the intelligence",
    "from the deal data",
    "from the account",
    "let me search",
    "let me analyze",
    "looking at the",
)

# Skeleton placeholders — content that looks like an unfilled template
_PLACEHOLDER_MARKERS = (
    "[insert",
    "[your ",
    "[tbd]",
    "[placeholder",
    "{{",
    "< fill",
    "<fill",
    "to be determined",
    "n/a — no data",
)


def _is_reasoning_line(line: str) -> bool:
    lower = line.lower().lstrip()
    return any(lower.startswith(s) for s in _REASONING_STARTERS)


def _is_placeholder_line(line: str) -> bool:
    lower = line.lower()
    return any(marker in lower for marker in _PLACEHOLDER_MARKERS)


def _has_account_reference(content: str, account_name: str) -> bool:
    """Return True if any word from account_name (len>3) appears in content."""
    content_lower = content.lower()
    words = [w for w in account_name.lower().split() if len(w) > 3]
    if not words:
        # Short account names — just check the whole name
        return account_name.lower() in content_lower
    return any(w in content_lower for w in words)


def validate_output(content: str, account_name: str, skill_name: str) -> Dict[str, Any]:
    """
    Programmatic quality check. Returns:
      {
        "quality": 0-100,
        "verdict": "good" | "partial" | "weak" | "skeleton" | "reasoning_dump" | "error",
        "reason": str
      }
    """
    # ── Error / empty ────────────────────────────────────────────────────────
    if not content or not content.strip():
        return {"quality": 0, "verdict": "error", "reason": "empty output"}

    stripped = content.strip()
    if stripped.startswith("❌"):
        return {"quality": 0, "verdict": "error", "reason": "skill returned error marker"}

    # ── Line classification ───────────────────────────────────────────────────
    lines = stripped.splitlines()
    real_lines = 0
    reasoning_count = 0
    placeholder_count = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(_HEADING_PREFIX):
            continue
        if line.startswith(_SEPARATOR_PREFIX):
            continue
        if line.startswith(_NO_DATA_PREFIX):
            continue
        if _is_reasoning_line(line):
            reasoning_count += 1
            continue
        if _is_placeholder_line(line):
            placeholder_count += 1
            continue
        real_lines += 1

    # ── Verdict logic ─────────────────────────────────────────────────────────
    if placeholder_count >= 3 and real_lines < 4:
        return {
            "quality": 5,
            "verdict": "skeleton",
            "reason": f"placeholder-only output ({placeholder_count} placeholders, {real_lines} real lines)",
        }

    if reasoning_count >= real_lines and reasoning_count > 0:
        return {
            "quality": 10,
            "verdict": "reasoning_dump",
            "reason": f"LLM thinking leaked into output ({reasoning_count} reasoning lines vs {real_lines} real lines)",
        }

    # ── Quality score ─────────────────────────────────────────────────────────
    quality = min(95, real_lines * 5)

    has_account_ref = _has_account_reference(stripped, account_name)
    if not has_account_ref:
        quality = max(0, quality - 25)

    # ── Final verdict ─────────────────────────────────────────────────────────
    if quality >= 60:
        verdict = "good"
        reason = f"{real_lines} real content lines, account referenced: {has_account_ref}"
    elif quality >= 30:
        verdict = "partial"
        reason = f"{real_lines} real content lines, quality borderline (score={quality})"
    else:
        verdict = "weak"
        reason = f"only {real_lines} real content lines, score={quality}"

    return {"quality": quality, "verdict": verdict, "reason": reason}
