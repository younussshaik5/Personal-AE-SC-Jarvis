"""
ComprehensiveDataAggregator - Pulls and aggregates all account data from all sources.
Feeds complete context to AI models for comprehensive understanding.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class ComprehensiveDataAggregator:
    """
    Aggregates ALL account data for AI models.
    Sources: files, deals, notes, emails, skills, learning history.
    """

    def __init__(self, account_path: str):
        """Initialize aggregator"""
        self.logger = logging.getLogger(__name__)
        self.account_path = Path(account_path)

    def aggregate_all_context(self) -> Dict[str, Any]:
        """
        Aggregate EVERYTHING about the account.
        Returns comprehensive context for AI models.
        """
        context = {
            'account_name': self.account_path.name,
            'aggregated_at': datetime.now().isoformat(),
            'company_profile': self._load_company_profile(),
            'discovery_notes': self._load_discovery_notes(),
            'deal_pipeline': self._load_deal_pipeline(),
            'document_inventory': self._load_document_inventory(),
            'learning_history': self._load_learning_history(),
            'competitive_intelligence': self._load_competitive_intelligence(),
            'skill_history': self._load_skill_history(),
            'key_metrics': self._calculate_key_metrics(),
            'relationships': self._extract_relationships(),
            'timeline': self._build_timeline(),
        }
        return context

    def _load_company_profile(self) -> Dict[str, Any]:
        """Load company research"""
        profile = {}
        research_file = self.account_path / "company_research.md"
        if research_file.exists():
            content = research_file.read_text()
            profile['overview'] = content
            profile['parsed'] = True
        return profile

    def _load_discovery_notes(self) -> List[Dict[str, Any]]:
        """Load all discovery and meeting notes"""
        notes = []
        for file_path in self.account_path.rglob("*.md"):
            if any(keyword in file_path.name.lower() for keyword in ['discovery', 'meeting', 'note', 'call']):
                try:
                    content = file_path.read_text()
                    notes.append({
                        'filename': file_path.name,
                        'size': len(content),
                        'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        'summary': content[:500]
                    })
                except Exception as e:
                    self.logger.warning(f"Could not read {file_path}: {e}")
        return notes

    def _load_deal_pipeline(self) -> Dict[str, Any]:
        """Load deal stage and pipeline"""
        pipeline = {}
        deal_file = self.account_path / "deal_stage.json"
        if deal_file.exists():
            try:
                pipeline = json.loads(deal_file.read_text())
            except Exception as e:
                self.logger.warning(f"Could not load deal_stage.json: {e}")
        return pipeline

    def _load_document_inventory(self) -> Dict[str, List[str]]:
        """Inventory all documents in account"""
        inventory = {
            'proposals': [],
            'contracts': [],
            'presentations': [],
            'spreadsheets': [],
            'notes': [],
            'other': []
        }
        
        for file_path in self.account_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                suffix = file_path.suffix.lower()
                name = file_path.name
                
                if suffix == '.pdf':
                    if 'proposal' in name.lower():
                        inventory['proposals'].append(name)
                    elif 'contract' in name.lower():
                        inventory['contracts'].append(name)
                    else:
                        inventory['other'].append(name)
                elif suffix in ['.ppt', '.pptx']:
                    inventory['presentations'].append(name)
                elif suffix in ['.xlsx', '.xls', '.csv']:
                    inventory['spreadsheets'].append(name)
                elif suffix in ['.md', '.txt']:
                    inventory['notes'].append(name)
                else:
                    inventory['other'].append(name)
        
        return {k: v for k, v in inventory.items() if v}

    def _load_learning_history(self) -> Dict[str, Any]:
        """Load what system has learned"""
        history = {
            'files_analyzed': 0,
            'patterns_identified': [],
            'improvements_suggested': [],
            'last_learning_cycle': None
        }
        
        learning_file = self.account_path / ".learning_history.json"
        if learning_file.exists():
            try:
                history = json.loads(learning_file.read_text())
            except Exception as e:
                self.logger.warning(f"Could not load learning history: {e}")
        return history

    def _load_competitive_intelligence(self) -> Dict[str, Any]:
        """Load competitor knowledge base"""
        intelligence = {}
        kb_file = self.account_path / ".competitor_kb.json"
        if kb_file.exists():
            try:
                intelligence = json.loads(kb_file.read_text())
            except Exception as e:
                self.logger.warning(f"Could not load competitor KB: {e}")
        return intelligence

    def _load_skill_history(self) -> List[Dict[str, Any]]:
        """Load history of skill usage"""
        history = []
        skill_history_file = self.account_path / ".skill_history.json"
        if skill_history_file.exists():
            try:
                history = json.loads(skill_history_file.read_text())
            except Exception as e:
                self.logger.warning(f"Could not load skill history: {e}")
        return history

    def _calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key metrics about the account"""
        metrics = {
            'total_documents': len(list(self.account_path.rglob("*"))),
            'total_size_mb': sum(f.stat().st_size for f in self.account_path.rglob("*")) / (1024*1024),
            'days_active': 0,
            'documents_per_week': 0,
            'skills_used': 0,
        }
        
        if self.account_path.exists():
            created = datetime.fromtimestamp(self.account_path.stat().st_ctime)
            metrics['days_active'] = (datetime.now() - created).days
        
        return metrics

    def _extract_relationships(self) -> Dict[str, Any]:
        """Extract relationships and contacts mentioned"""
        relationships = {
            'decision_makers': [],
            'contacts_mentioned': [],
            'organizations': []
        }
        
        for file_path in self.account_path.rglob("*.md"):
            try:
                content = file_path.read_text()
                import re
                patterns = re.findall(r'([A-Z][a-z]+\s[A-Z][a-z]+)\s*[-–]\s*([A-Za-z\s]+)', content)
                for name, title in patterns:
                    if 'director' in title.lower() or 'vp' in title.lower() or 'ceo' in title.lower():
                        relationships['decision_makers'].append({'name': name, 'title': title})
            except Exception as e:
                self.logger.debug(f"Could not extract relationships: {e}")
        
        return relationships

    def _build_timeline(self) -> List[Dict[str, Any]]:
        """Build timeline of important events"""
        timeline = []
        
        for file_path in sorted(self.account_path.rglob("*"), key=lambda f: f.stat().st_mtime):
            if file_path.is_file() and not file_path.name.startswith('.'):
                timeline.append({
                    'date': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'event': f"File added/modified: {file_path.name}",
                    'type': 'file_change'
                })
        
        return timeline[-50:]

    def get_summary_for_ai(self) -> str:
        """Get formatted summary to feed to AI models"""
        context = self.aggregate_all_context()
        
        account_name = context['account_name']
        agg_time = context['aggregated_at']
        
        company_info = str(context['company_profile'])
        deal_data = json.dumps(context['deal_pipeline'], indent=2)
        doc_data = json.dumps(context['document_inventory'], indent=2)
        metrics_data = json.dumps(context['key_metrics'], indent=2)
        comp_data = json.dumps(context['competitive_intelligence'], indent=2)
        timeline_data = json.dumps(context['timeline'][-10:], indent=2)
        rel_data = json.dumps(context['relationships'], indent=2)
        
        summary = f"ACCOUNT CONTEXT SUMMARY\nAccount: {account_name}\nAggregated: {agg_time}\n\nCOMPANY PROFILE:\n{company_info[:300]}\n\nDEAL PIPELINE:\n{deal_data}\n\nDOCUMENT INVENTORY:\n{doc_data}\n\nKEY METRICS:\n{metrics_data}\n\nCOMPETITIVE INTELLIGENCE:\n{comp_data[:300]}\n\nRECENT ACTIVITIES:\n{timeline_data}\n\nRELATIONSHIPS:\n{rel_data}"
        
        return summary
