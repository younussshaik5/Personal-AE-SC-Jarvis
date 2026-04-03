"""JARVIS Skills package - all 24+ presales intelligence skills."""

from .account_summary import AccountSummarySkill
from .intelligence_brief import IntelligenceBriefSkill
from .architecture_diagram import ArchitectureDiagramSkill
from .battlecard import BattlecardSkill
from .company_research import CompanyResearchSkill
from .competitive_intelligence import CompetitiveIntelligenceSkill
from .competitor_pricing import CompetitorPricingSkill
from .conversation_extractor import ConversationExtractorSkill
from .conversation_summarizer import ConversationSummarizerSkill
from .custom_template import CustomTemplateSkill
from .deal_stage_tracker import DealStageTrackerSkill
from .demo_strategy import DemoStrategySkill
from .discovery import DiscoverySkill
from .documentation import DocumentationSkill
from .followup_email import FollowupEmailSkill
from .html_generator import HtmlGeneratorSkill
from .knowledge_builder import KnowledgeBuilderSkill
from .meddpicc import MeddpiccSkill
from .meeting_prep import MeetingPrepSkill
from .meeting_summary import MeetingSummarySkill
from .onboarding import OnboardingSkill
from .proposal import ProposalSkill
from .quick_insights import QuickInsightsSkill
from .risk_report import RiskReportSkill
from .scaffold_account import ScaffoldAccountSkill
from .sow import SowSkill
from .technical_risk import TechnicalRiskSkill
from .value_architecture import ValueArchitectureSkill
from .system_health import SystemHealthSkill

# Skill registry mapping skill names to classes
SKILL_REGISTRY = {
    "account_summary": AccountSummarySkill,
    "intelligence_brief": IntelligenceBriefSkill,
    "architecture_diagram": ArchitectureDiagramSkill,
    "battlecard": BattlecardSkill,
    "company_research": CompanyResearchSkill,
    "competitive_intelligence": CompetitiveIntelligenceSkill,
    "competitor_pricing": CompetitorPricingSkill,
    "conversation_extractor": ConversationExtractorSkill,
    "conversation_summarizer": ConversationSummarizerSkill,
    "custom_template": CustomTemplateSkill,
    "deal_stage_tracker": DealStageTrackerSkill,
    "demo_strategy": DemoStrategySkill,
    "discovery": DiscoverySkill,
    "documentation": DocumentationSkill,
    "followup_email": FollowupEmailSkill,
    "html_generator": HtmlGeneratorSkill,
    "knowledge_builder": KnowledgeBuilderSkill,
    "meddpicc": MeddpiccSkill,
    "meeting_prep": MeetingPrepSkill,
    "meeting_summary": MeetingSummarySkill,
    "onboarding": OnboardingSkill,
    "proposal": ProposalSkill,
    "quick_insights": QuickInsightsSkill,
    "risk_report": RiskReportSkill,
    "scaffold_account": ScaffoldAccountSkill,
    "sow": SowSkill,
    "technical_risk": TechnicalRiskSkill,
    "value_architecture": ValueArchitectureSkill,
    "system_health": SystemHealthSkill,
}

__all__ = [
    "SKILL_REGISTRY",
    "AccountSummarySkill",
    "IntelligenceBriefSkill",
    "ArchitectureDiagramSkill",
    "BattlecardSkill",
    "CompanyResearchSkill",
    "CompetitiveIntelligenceSkill",
    "CompetitorPricingSkill",
    "ConversationExtractorSkill",
    "ConversationSummarizerSkill",
    "CustomTemplateSkill",
    "DealStageTrackerSkill",
    "DemoStrategySkill",
    "DiscoverySkill",
    "DocumentationSkill",
    "FollowupEmailSkill",
    "HtmlGeneratorSkill",
    "KnowledgeBuilderSkill",
    "MeddpiccSkill",
    "MeetingPrepSkill",
    "MeetingSummarySkill",
    "OnboardingSkill",
    "ProposalSkill",
    "QuickInsightsSkill",
    "RiskReportSkill",
    "ScaffoldAccountSkill",
    "SowSkill",
    "TechnicalRiskSkill",
    "ValueArchitectureSkill",
    "SystemHealthSkill",
]
