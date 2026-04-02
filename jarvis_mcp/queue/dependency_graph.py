"""
Dependency graph — complete routing for all 27 JARVIS skills.

FILE_TRIGGERS  : source file changed → queue these skills (priority HIGH)
SKILL_CASCADES : skill completed → queue these downstream skills
SKIP_AUTO_QUEUE: never auto-queue (user must trigger manually)

All skill names match SKILL_REGISTRY keys exactly.
"""

from typing import Dict, List

# ── Skill name → output file written to the account folder ───────────────────
# Used by both QueueWorker and handle_tool_call to persist every skill output.
# Skills not listed here (deal_stage_tracker, scaffold_account) manage their
# own file writes internally.

SKILL_OUTPUT_FILES: Dict[str, str] = {
    "proposal":               "proposal.md",
    "battlecard":             "battlecard.md",
    "demo_strategy":          "demo_strategy.md",
    "risk_report":            "risk_report.md",
    "value_architecture":     "value_architecture.md",
    "discovery":              "discovery_questions.md",
    "competitive_intelligence": "competitive_intelligence.md",
    "meeting_prep":           "meeting_prep.md",
    "meeting_summary":        "meeting_summary.md",
    "conversation_summarizer": "conversation_summary.md",
    "meddpicc":               "meddpicc.md",
    "sow":                    "sow.md",
    "followup_email":         "followup_email.md",
    "account_summary":        "account_summary.md",
    "technical_risk":         "technical_risk.md",
    "competitor_pricing":     "competitor_pricing.md",
    "architecture_diagram":   "architecture_diagram.md",
    "documentation":          "documentation.md",
    "html_generator":         "report.html",
    "knowledge_builder":      "knowledge_builder.md",
    "quick_insights":         "quick_insights.md",
    "custom_template":        "custom_template.md",
    "conversation_extractor": "conversation_extractor.md",
}

# ── File change → skills to queue ────────────────────────────────────────────
# Priority 2 (HIGH) — direct source changed, run immediately.

FILE_TRIGGERS: Dict[str, List[str]] = {
    # Safe to include feedback skills here because:
    # - Feedback loop (skill output → discovery.md) is fire-and-forget async
    # - KnowledgeMerger.was_self_written() has a 300s cooldown per account
    # - FileWatcher cycle guard checks was_self_written() and suppresses re-triggers
    # Result: one full batch of skills runs, enriches discovery.md once, stops.
    "discovery.md": [
        "meddpicc",                 # re-score all 8 MEDDPICC dimensions
        "battlecard",               # competitive refresh
        "competitive_intelligence", # deep competitive analysis
        "technical_risk",           # technical blockers and integration risk
        "discovery",                # refresh gap-based discovery questions
    ],
    "company_research.md": [
        "battlecard",
        "competitive_intelligence",
        "demo_strategy",
        "account_summary",
    ],
    "deal_stage.json": [
        "quick_insights",           # stage/ARR changed
        "account_summary",          # dossier needs refresh
        "meddpicc",                 # deal data affects scores
        "risk_report",              # stage change = risk shift
    ],
}

# ── Skill completion → downstream skills ─────────────────────────────────────
# After a skill writes its output, queue these dependents.
# priority 3 = first wave, 4 = second wave, 5 = third wave.

SKILL_CASCADES: Dict[str, Dict] = {

    # ── Wave 1 (priority 3) ───────────────────────────────────────────────────

    # Fresh signals extracted → re-score MEDDPICC
    "conversation_extractor": {
        "skills": ["meddpicc"],
        "priority": 3,
    },

    # Fresh deep competitive intel → refresh battlecard
    "competitive_intelligence": {
        "skills": ["battlecard"],
        "priority": 3,
    },

    # ── Wave 2 (priority 3-4) ─────────────────────────────────────────────────

    # Fresh MEDDPICC → risk, value arch, summary, discovery gaps, knowledge graph
    "meddpicc": {
        "skills": [
            "risk_report",
            "value_architecture",
            "account_summary",
            "discovery",           # discovery gaps updated by fresh MEDDPICC scores
            "knowledge_builder",   # stakeholder map from fresh MEDDPICC
        ],
        "priority": 3,
    },

    # Fresh battlecard → demo strategy and pricing analysis
    "battlecard": {
        "skills": ["demo_strategy", "competitor_pricing"],
        "priority": 4,
    },

    # Fresh technical risk → meeting prep (SC needs to know blockers)
    "technical_risk": {
        "skills": ["meeting_prep"],
        "priority": 4,
    },

    # ── Wave 3 (priority 4) ───────────────────────────────────────────────────

    # Fresh risk report → meeting prep and demo strategy
    "risk_report": {
        "skills": ["meeting_prep", "demo_strategy"],
        "priority": 4,
    },

    # Fresh value architecture → proposal (ROI now in context)
    "value_architecture": {
        "skills": ["proposal"],
        "priority": 4,
    },

    # Fresh account summary → knowledge graph
    "account_summary": {
        "skills": ["knowledge_builder"],
        "priority": 4,
    },

    # ── Wave 4 (priority 5) ───────────────────────────────────────────────────

    # Fresh proposal → SOW derived from it
    "proposal": {
        "skills": ["sow"],
        "priority": 5,
    },

    # Fresh demo strategy → final meeting prep (everything now in context)
    "demo_strategy": {
        "skills": ["meeting_prep"],
        "priority": 5,
    },

    # Fresh competitor pricing → battlecard refresh
    "competitor_pricing": {
        "skills": ["battlecard"],
        "priority": 5,
    },
}

# ── Skills never auto-queued ──────────────────────────────────────────────────
# User must trigger these explicitly (require transcript input, are one-off,
# or are infrastructure/meta skills).

SKIP_AUTO_QUEUE = {
    "scaffold_account",         # user-only: creates new account
    "onboarding",               # user-only: setup wizard
    "deal_stage_tracker",       # user-only: manual stage update
    "system_health",            # user-only: diagnostics
    "custom_template",          # user-only: needs custom prompt
    "html_generator",           # user-only: needs explicit request
    "documentation",            # user-only: needs explicit request
    "conversation_summarizer",  # user-only: needs transcript input
    "meeting_summary",          # user-only: needs transcript input
    "architecture_diagram",     # user-only: needs explicit request
    "followup_email",           # user-only: needs meeting context
}
