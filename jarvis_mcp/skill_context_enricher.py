"""Skill Context Enricher - Auto-loads full account context to skills"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .comprehensive_data_aggregator import ComprehensiveDataAggregator
from .account_hierarchy import AccountHierarchy


class SkillContextEnricher:
    """Enriches skill execution with complete account context"""

    def __init__(self, accounts_root: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.accounts_root = Path(accounts_root) if accounts_root else Path.home() / "Documents" / "claude space" / "ACCOUNTS"
        self.hierarchy = AccountHierarchy(str(self.accounts_root))
        self.aggregator_cache = {}

    def get_enriched_context(self, account_name: str) -> Dict[str, Any]:
        """Load complete account context"""
        if account_name in self.aggregator_cache:
            aggregator = self.aggregator_cache[account_name]
            return aggregator.aggregate_all_context()

        account_path = self.hierarchy.get_account_path(account_name)
        if not account_path:
            self.logger.warning(f"Account '{account_name}' not found")
            return self._empty_context(account_name)

        aggregator = ComprehensiveDataAggregator(str(account_path))
        self.aggregator_cache[account_name] = aggregator

        context = aggregator.aggregate_all_context()
        self.logger.debug(f"✓ Loaded context for {account_name}")
        return context

    def get_context_for_skill(self, account_name: str, skill_name: str, 
                             extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get skill-specific context"""
        context = self.get_enriched_context(account_name)

        context['_skill_execution'] = {
            'skill_name': skill_name,
            'extra_params': extra_params or {},
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }

        skill_focus_map = {
            'proposal': ['company_profile', 'competitive_intelligence', 'deal_pipeline', 'relationships'],
            'battlecard': ['competitive_intelligence', 'metrics', 'skill_history'],
            'discovery': ['company_profile', 'learning_history', 'relationships'],
            'demo_strategy': ['company_profile', 'deal_pipeline', 'relationships', 'competitive_intelligence'],
        }

        context['_skill_focus'] = {
            'type': skill_name,
            'relevant_data': skill_focus_map.get(skill_name, ['company_profile', 'deal_pipeline'])
        }

        return context

    def get_summary_for_ai_context(self, account_name: str, max_chars: int = 2000) -> str:
        """Get AI-ready summary"""
        context = self.get_enriched_context(account_name)
        account_path = self.hierarchy.get_account_path(account_name)
        if not account_path:
            return f"Account '{account_name}' not found."

        aggregator = ComprehensiveDataAggregator(str(account_path))
        summary = aggregator.get_summary_for_ai()

        if len(summary) > max_chars:
            summary = summary[:max_chars] + "\n[... truncated ...]"

        return summary

    def get_competitive_summary(self, account_name: str) -> str:
        """Get competitive intelligence"""
        context = self.get_enriched_context(account_name)
        if not context.get('competitive_intelligence'):
            return f"No competitive intelligence for {account_name}."

        intel = context['competitive_intelligence']
        lines = [
            "COMPETITIVE INTELLIGENCE:",
            f"  Competitors: {', '.join(intel.get('competitors', []))}",
            f"  Wins: {', '.join(intel.get('recent_wins', []))}",
            f"  Losses: {', '.join(intel.get('recent_losses', []))}",
        ]
        return "\n".join(lines)

    def get_deal_summary(self, account_name: str) -> str:
        """Get deal pipeline summary"""
        context = self.get_enriched_context(account_name)
        if not context.get('deal_pipeline'):
            return f"No deals for {account_name}."

        deals = context['deal_pipeline']
        lines = ["DEALS:"]
        for deal_id, deal in list(deals.items())[:10]:
            if isinstance(deal, dict):
                lines.append(f"  {deal_id}: ${deal.get('value', 0)} ({deal.get('stage', 'unknown')})")
        return "\n".join(lines)

    def get_relationships_summary(self, account_name: str) -> str:
        """Get relationships"""
        context = self.get_enriched_context(account_name)
        if not context.get('relationships'):
            return f"No relationships for {account_name}."

        rels = context['relationships']
        lines = ["RELATIONSHIPS:"]
        for rel_id, rel in list(rels.items())[:15]:
            if isinstance(rel, dict):
                lines.append(f"  • {rel.get('name', rel_id)} ({rel.get('title', 'unknown')})")
        return "\n".join(lines)

    def invalidate_cache(self, account_name: Optional[str] = None):
        """Clear cache"""
        if account_name:
            if account_name in self.aggregator_cache:
                del self.aggregator_cache[account_name]
                self.logger.info(f"Cleared cache for {account_name}")
        else:
            self.aggregator_cache.clear()
            self.logger.info("Cleared all caches")

    def _empty_context(self, account_name: str) -> Dict[str, Any]:
        return {
            'account_name': account_name,
            'account_path': None,
            'company_profile': {},
            'competitive_intelligence': {},
            'deal_pipeline': {},
            'relationships': {},
            '_error': f'Account not found'
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            'cached_accounts': list(self.aggregator_cache.keys()),
            'cache_size': len(self.aggregator_cache),
            'accounts_root': str(self.accounts_root)
        }
