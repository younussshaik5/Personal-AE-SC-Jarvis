#!/usr/bin/env python3
"""
Sales playbook stage definitions.
Defines deal stages, auto-triggers, actions, and exit criteria for the
full sales cycle from new account through close.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class DealStage(Enum):
    NEW_ACCOUNT = "new_account"
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    DEMO = "demo"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


@dataclass
class StageDefinition:
    """Defines a single deal stage in the playbook."""

    stage: DealStage
    name: str
    description: str
    auto_triggers: List[str]  # Events that trigger entry into this stage
    auto_actions: List[str]   # Skills/actions to run when entering this stage
    exit_criteria: List[str]  # Conditions that must be met to advance
    next_stages: List[DealStage] = field(default_factory=list)


PLAYBOOK_STAGES: Dict[DealStage, StageDefinition] = {
    DealStage.NEW_ACCOUNT: StageDefinition(
        stage=DealStage.NEW_ACCOUNT,
        name="New Account",
        description=(
            "Initial account setup. JARVIS runs company research, scores the account "
            "against the yellow.ai ICP (enterprise, high contact-center volume, "
            "CX transformation mandate), and maps the competitive landscape "
            "(Sprinklr, Genesys, NICE, Intercom, Kore.ai)."
        ),
        auto_triggers=[
            "account.created",          # New account folder created in workspace
            "account.folder.created",   # File system observer detects new account dir
        ],
        auto_actions=[
            "skill.company_research",       # Deep company research: financials, tech stack, org chart
            "skill.icp_scoring",            # Score against yellow.ai ICP criteria
            "skill.competitive_landscape",  # Map which competitors are in the account
        ],
        exit_criteria=[
            "Company research brief completed",
            "ICP score calculated (must be >= 40 to proceed)",
            "Competitive landscape mapped",
            "Initial contact identified (champion or economic buyer)",
        ],
        next_stages=[DealStage.DISCOVERY, DealStage.CLOSED_LOST],
    ),

    DealStage.DISCOVERY: StageDefinition(
        stage=DealStage.DISCOVERY,
        name="Discovery",
        description=(
            "First engagement with the prospect. Focus on understanding their "
            "current CX stack, pain points (agent attrition, CSAT decline, cost "
            "per interaction), automation appetite, and decision-making process. "
            "JARVIS generates a discovery framework and pre-meeting brief."
        ),
        auto_triggers=[
            "meeting.ended",                # First meeting with this account
            "meeting.scheduled.discovery",  # Calendar event tagged as discovery
        ],
        auto_actions=[
            "skill.discovery_framework",    # Generate discovery question framework
            "skill.pre_meeting_brief",      # Compile account context + talking points
        ],
        exit_criteria=[
            "Discovery call completed",
            "Pain points documented (at least 2 critical pains)",
            "Current CX stack identified",
            "Decision maker and champion identified",
            "Timeline and budget signals captured",
        ],
        next_stages=[DealStage.QUALIFICATION, DealStage.CLOSED_LOST],
    ),

    DealStage.QUALIFICATION: StageDefinition(
        stage=DealStage.QUALIFICATION,
        name="Qualification",
        description=(
            "Post-discovery deep qualification using MEDDPICC framework. "
            "JARVIS scores the deal, identifies gaps in qualification, and "
            "drafts personalized follow-up to fill those gaps."
        ),
        auto_triggers=[
            "meeting.summary.ready",        # Post-discovery meeting summary generated
            "skill.discovery.completed",    # Discovery notes processed
        ],
        auto_actions=[
            "skill.meddpicc_scoring",   # Full MEDDPICC analysis and scoring
            "skill.gap_analysis",       # Identify qualification gaps and risks
            "skill.followup_draft",     # Draft follow-up email addressing gaps
        ],
        exit_criteria=[
            "MEDDPICC score >= 60",
            "Economic buyer identified and engaged",
            "Decision criteria documented",
            "Paper process (procurement, legal, security) mapped",
            "Compelling event or timeline confirmed",
        ],
        next_stages=[DealStage.DEMO, DealStage.CLOSED_LOST],
    ),

    DealStage.DEMO: StageDefinition(
        stage=DealStage.DEMO,
        name="Demo / Technical Validation",
        description=(
            "Technical proof-of-value stage. JARVIS generates a tailored demo "
            "strategy based on discovered pains, builds an ROI framework using "
            "the prospect's metrics, and assesses technical integration risks."
        ),
        auto_triggers=[
            "playbook.meddpicc.above_threshold",   # MEDDPICC score crossed 60
            "meeting.scheduled.demo",               # Demo meeting scheduled
        ],
        auto_actions=[
            "skill.demo_strategy",          # Tailored demo flow based on pains/use cases
            "skill.roi_framework",          # Quantified ROI model with prospect's numbers
            "skill.technical_risk_assessment",  # Integration risks, security, compliance gaps
        ],
        exit_criteria=[
            "Demo delivered with positive prospect feedback",
            "Technical validation passed (no blocking integration issues)",
            "ROI narrative accepted by economic buyer",
            "Champion confirms internal alignment for proposal",
        ],
        next_stages=[DealStage.PROPOSAL, DealStage.QUALIFICATION, DealStage.CLOSED_LOST],
    ),

    DealStage.PROPOSAL: StageDefinition(
        stage=DealStage.PROPOSAL,
        name="Proposal",
        description=(
            "Formal proposal assembly. JARVIS compiles the proposal from "
            "discovery, qualification, and demo artifacts. Generates competitive "
            "battlecards for likely objections and prepares pricing strategy."
        ),
        auto_triggers=[
            "meeting.summary.demo_positive",    # Demo meeting had positive outcome
            "skill.demo.completed",             # Demo stage actions complete
        ],
        auto_actions=[
            "skill.proposal_assembly",  # Assemble full proposal document
            "skill.battlecards",        # Competitive battlecards for negotiation
            "skill.pricing_strategy",   # Pricing and packaging recommendations
        ],
        exit_criteria=[
            "Proposal document finalized and sent",
            "Pricing approved by deal desk / management",
            "Prospect acknowledges receipt and confirms review timeline",
            "Legal/procurement contacts engaged",
        ],
        next_stages=[DealStage.NEGOTIATION, DealStage.DEMO, DealStage.CLOSED_LOST],
    ),

    DealStage.NEGOTIATION: StageDefinition(
        stage=DealStage.NEGOTIATION,
        name="Negotiation",
        description=(
            "Active negotiation phase. JARVIS monitors for prospect responses, "
            "flags stale deals, and provides leverage analysis based on "
            "competitive positioning and prospect urgency signals."
        ),
        auto_triggers=[
            "proposal.sent",               # Proposal delivered to prospect
            "email.proposal.delivered",     # Email tracking confirms delivery
        ],
        auto_actions=[
            "skill.response_monitor",   # Track prospect engagement with proposal
            "skill.stale_deal_alert",   # Alert if no response within SLA
            "skill.leverage_analysis",  # Negotiation leverage and concession strategy
        ],
        exit_criteria=[
            "Terms agreed by both parties",
            "Contract redlines resolved",
            "Security/compliance review passed",
            "Verbal commit or signed contract received",
        ],
        next_stages=[DealStage.CLOSED_WON, DealStage.CLOSED_LOST],
    ),

    DealStage.CLOSED_WON: StageDefinition(
        stage=DealStage.CLOSED_WON,
        name="Closed Won",
        description=(
            "Deal closed successfully. JARVIS generates a win report analyzing "
            "what worked, creates a customer handoff document for the CS team, "
            "and archives the deal for future playbook refinement."
        ),
        auto_triggers=[
            "deal.closed_won",          # Manual trigger when deal closes
            "contract.signed",          # Contract signing detected
        ],
        auto_actions=[
            "skill.win_report",         # Analyze what worked, key moments, timeline
            "skill.handoff_document",   # CS handoff with context, contacts, commitments
            "skill.deal_archive",       # Archive all deal artifacts for learning
        ],
        exit_criteria=[
            "Win report completed",
            "Handoff document delivered to CS",
            "Deal archived",
        ],
        next_stages=[],  # Terminal stage
    ),

    DealStage.CLOSED_LOST: StageDefinition(
        stage=DealStage.CLOSED_LOST,
        name="Closed Lost",
        description=(
            "Deal lost. JARVIS runs a loss analysis to identify failure points, "
            "generates lessons learned for playbook improvement, and archives "
            "for competitive intelligence refinement."
        ),
        auto_triggers=[
            "deal.closed_lost",     # Manual trigger when deal is lost
            "deal.abandoned",       # Deal marked as abandoned/dead
        ],
        auto_actions=[
            "skill.loss_analysis",      # Root cause analysis: why we lost
            "skill.lessons_learned",    # Extract patterns to improve future deals
            "skill.deal_archive",       # Archive all deal artifacts
        ],
        exit_criteria=[
            "Loss analysis completed with root cause",
            "Lessons learned documented",
            "Deal archived",
        ],
        next_stages=[],  # Terminal stage
    ),
}


def get_stage_definition(stage: DealStage) -> StageDefinition:
    """Get the stage definition for a given deal stage."""
    return PLAYBOOK_STAGES[stage]


def get_stage_by_name(name: str) -> Optional[DealStage]:
    """Look up a DealStage by its string value."""
    try:
        return DealStage(name)
    except ValueError:
        return None


def get_all_trigger_events() -> Dict[str, DealStage]:
    """
    Build a reverse map from event type to the stage it triggers.
    Returns dict mapping event_type -> DealStage.
    """
    trigger_map = {}
    for stage, definition in PLAYBOOK_STAGES.items():
        for trigger in definition.auto_triggers:
            trigger_map[trigger] = stage
    return trigger_map
