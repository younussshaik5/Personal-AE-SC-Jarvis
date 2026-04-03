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
    "intelligence_brief":     "intelligence_brief.md",
    "company_research":       "company_research.md",
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
    # intelligence_brief runs FIRST on any source change.
    # Nemotron reads all files, writes intelligence_brief.md, then
    # SKILL_CASCADES["intelligence_brief"] fires all reasoning skills.
    # company_research runs in parallel (independent of brief).
    "discovery.md": [
        "intelligence_brief",       # Nemotron full-context synthesis (runs first)
        "company_research",         # parallel — doesn't depend on brief
    ],
    "company_research.md": [
        "intelligence_brief",       # re-synthesise when company profile updates
        "battlecard",
        "competitive_intelligence",
        "demo_strategy",
        "account_summary",
    ],
    "deal_stage.json": [
        "intelligence_brief",       # re-synthesise on deal data change
        "quick_insights",           # fast — runs in parallel
        "account_summary",          # fast — runs in parallel
    ],
}

# ── Skill completion → downstream skills ─────────────────────────────────────
# After a skill writes its output, queue these dependents.
# priority 3 = first wave, 4 = second wave, 5 = third wave.

SKILL_CASCADES: Dict[str, Dict] = {

    # ── Wave 0 — Intelligence Brief cascade (priority 2 = HIGH) ──────────────
    # After Nemotron writes intelligence_brief.md, all reasoning skills fire
    # with the full synthesised context as their primary input.

    "intelligence_brief": {
        "skills": [
            "meddpicc",                 # score all 8 dimensions from complete brief
            "battlecard",               # competitive positioning from complete intel
            "competitive_intelligence", # deep competitive analysis
            "technical_risk",           # technical blockers and integration risk
            "discovery",                # gap-based discovery questions
            "risk_report",              # deal risk from complete picture
            "value_architecture",       # ROI model with all value signals
            "account_summary",          # full deal dossier
        ],
        "priority": 2,   # HIGH — same as file trigger priority
    },

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
            "discovery",
            "knowledge_builder",
        ],
        "priority": 3,
    },

    # Fresh battlecard → demo strategy and pricing analysis
    "battlecard": {
        "skills": ["demo_strategy", "competitor_pricing"],
        "priority": 4,
    },

    # Fresh technical risk → meeting prep + architecture diagram
    "technical_risk": {
        "skills": ["meeting_prep", "architecture_diagram"],
        "priority": 4,
    },

    # ── Wave 3 (priority 4) ───────────────────────────────────────────────────

    # Fresh risk report → meeting prep and demo strategy
    "risk_report": {
        "skills": ["meeting_prep", "demo_strategy"],
        "priority": 4,
    },

    # Fresh value architecture → proposal
    "value_architecture": {
        "skills": ["proposal"],
        "priority": 4,
    },

    # Fresh account summary → knowledge graph + HTML dashboard
    "account_summary": {
        "skills": ["knowledge_builder", "html_generator"],
        "priority": 4,
    },

    # ── Wave 4 (priority 5) ───────────────────────────────────────────────────

    # Fresh proposal → SOW + documentation
    "proposal": {
        "skills": ["sow", "documentation"],
        "priority": 5,
    },

    # Fresh demo strategy → final meeting prep
    "demo_strategy": {
        "skills": ["meeting_prep"],
        "priority": 5,
    },

    # Fresh competitor pricing → battlecard refresh
    "competitor_pricing": {
        "skills": ["battlecard"],
        "priority": 5,
    },

    # Fresh meeting prep → follow-up email (everything in context for next touch)
    "meeting_prep": {
        "skills": ["followup_email"],
        "priority": 5,
    },
}

# ── Skills never auto-queued ──────────────────────────────────────────────────
# User must trigger these explicitly (require transcript input, are one-off,
# or are infrastructure/meta skills).

SKIP_AUTO_QUEUE = {
    "scaffold_account",         # user-only: creates account folder
    "onboarding",               # user-only: setup wizard
    "deal_stage_tracker",       # user-only: manual stage update
    "system_health",            # user-only: diagnostics
    "custom_template",          # user-only: needs custom prompt
    "conversation_summarizer",  # user-only: needs conversation transcript as input
    "meeting_summary",          # user-only: needs meeting transcript as input
    "conversation_extractor",   # user-only: needs raw conversation text as input
    # followup_email, architecture_diagram, documentation, html_generator
    # are auto-triggered via cascade — they work from account context alone
}
