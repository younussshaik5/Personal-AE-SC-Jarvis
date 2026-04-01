"""
CompetitorKnowledgeBase - Builds comprehensive competitor intelligence from all account data.
Learns from: proposals, contracts, emails, discovery notes, deals, pricing, wins/losses.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import re
import logging


class CompetitorKnowledgeBase:
    """
    Automatically builds competitor knowledge base from account data.
    Learns: competitors, pricing strategies, win/loss patterns, market positioning.
    """

    def __init__(self, account_path: str):
        """Initialize knowledge base for account"""
        self.logger = logging.getLogger(__name__)
        self.account_path = Path(account_path)
        self.kb_file = self.account_path / ".competitor_kb.json"
        
        # Load or initialize
        self.knowledge = {
            'competitors': {},  # {name: {pricing, strengths, weaknesses, customers, win_rate}}
            'market_insights': {},  # {insight_type: [insights]}
            'win_patterns': [],  # Winning strategies
            'loss_patterns': [],  # Why we lose
            'pricing_intelligence': {},  # Pricing strategies
            'customer_segments': {},  # Customer types and behaviors
            'last_updated': None
        }
        self._load()

    def analyze_all_account_data(self) -> Dict[str, Any]:
        """
        Analyze ALL data sources in account folder.
        Extracts: proposals, deals, emails, notes, contracts.
        """
        self.logger.info(f"Analyzing all data sources in {self.account_path}")
        
        sources_analyzed = {
            'proposals': 0,
            'deals': 0,
            'emails': 0,
            'notes': 0,
            'contracts': 0
        }
        
        # Scan for files to analyze
        for file_path in self.account_path.rglob('*'):
            if file_path.is_file():
                if file_path.suffix == '.pdf' or 'proposal' in file_path.name.lower():
                    self._analyze_proposal(file_path)
                    sources_analyzed['proposals'] += 1
                elif file_path.name == 'deal_stage.json':
                    self._analyze_deal(file_path)
                    sources_analyzed['deals'] += 1
                elif file_path.suffix in ['.txt', '.md'] and 'email' in file_path.name.lower():
                    self._analyze_email(file_path)
                    sources_analyzed['emails'] += 1
                elif file_path.suffix in ['.md', '.txt'] and 'discovery' in file_path.name.lower():
                    self._analyze_notes(file_path)
                    sources_analyzed['notes'] += 1
        
        self.knowledge['last_updated'] = datetime.now().isoformat()
        self._save()
        
        return sources_analyzed

    def _analyze_proposal(self, proposal_path: Path):
        """Extract competitor info from proposal"""
        try:
            content = proposal_path.read_text(errors='ignore').lower()
            
            # Look for competitor mentions
            competitor_patterns = [
                r'(?:vs|versus|compared to|alternative|instead of)\s+([a-z\s&]+?)(?:,|\.|\s+(?:is|has|offers))',
                r'(?:competitor|competing|competition)\s+(?:from|with|against)\s+([a-z\s&]+?)(?:,|\.)',
            ]
            
            for pattern in competitor_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    competitor = match.strip()
                    self._record_competitor(competitor, 'proposal_comparison', proposal_path.name)
            
            # Extract pricing if mentioned
            pricing = re.findall(r'\$[\d,]+(?:\.\d{2})?', content)
            if pricing:
                self.knowledge['pricing_intelligence']['found_in_proposals'] = pricing[:5]
        
        except Exception as e:
            self.logger.warning(f"Could not analyze proposal {proposal_path}: {e}")

    def _analyze_deal(self, deal_path: Path):
        """Extract deal insights"""
        try:
            deal_data = json.loads(deal_path.read_text())
            
            # Record lost deal analysis
            if deal_data.get('status') == 'lost':
                lost_reason = deal_data.get('lost_reason', 'unknown')
                if 'competitor' in lost_reason.lower():
                    # Extract competitor name
                    match = re.search(r'lost to ([a-z\s&]+?)(?:,|$)', lost_reason, re.IGNORECASE)
                    if match:
                        competitor = match.group(1).strip()
                        self._record_loss(competitor, lost_reason)
            
            # Record won deal
            elif deal_data.get('status') == 'won':
                self._record_win(deal_data)
        
        except Exception as e:
            self.logger.warning(f"Could not analyze deal {deal_path}: {e}")

    def _analyze_email(self, email_path: Path):
        """Extract insights from email threads"""
        try:
            content = email_path.read_text(errors='ignore').lower()
            
            # Look for competitive positioning mentions
            positioning_keywords = ['advantage', 'differentiate', 'unique', 'better than', 'superior', 'leading']
            found_positioning = [kw for kw in positioning_keywords if kw in content]
            
            if found_positioning:
                self.knowledge['market_insights'].setdefault('positioning_mentions', []).append({
                    'file': email_path.name,
                    'keywords': found_positioning,
                    'date': datetime.now().isoformat()
                })
        
        except Exception as e:
            self.logger.warning(f"Could not analyze email {email_path}: {e}")

    def _analyze_notes(self, notes_path: Path):
        """Extract insights from discovery/meeting notes"""
        try:
            content = notes_path.read_text(errors='ignore')
            
            # Extract customer pain points (competitive opportunities)
            pain_patterns = [
                r'(?:pain point|challenge|problem|issue)\s*:?\s*([a-z\s,&]+?)(?:,|\.|;)',
            ]
            
            for pattern in pain_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    pain_point = match.strip()
                    self.knowledge['market_insights'].setdefault('customer_pain_points', []).append(pain_point)
        
        except Exception as e:
            self.logger.warning(f"Could not analyze notes {notes_path}: {e}")

    def _record_competitor(self, name: str, source: str, source_file: str):
        """Record competitor mention"""
        name_clean = name.strip().title()
        
        if name_clean not in self.knowledge['competitors']:
            self.knowledge['competitors'][name_clean] = {
                'name': name_clean,
                'mentions': [],
                'win_rate': 0,
                'loss_rate': 0,
                'pricing': [],
                'strengths': [],
                'weaknesses': [],
                'customer_segments': []
            }
        
        self.knowledge['competitors'][name_clean]['mentions'].append({
            'source': source,
            'file': source_file,
            'date': datetime.now().isoformat()
        })

    def _record_win(self, deal_data: Dict[str, Any]):
        """Record successful deal"""
        win_insight = {
            'account': deal_data.get('account_name', 'unknown'),
            'value': deal_data.get('value_usd', 0),
            'date': deal_data.get('close_date', datetime.now().isoformat())
        }
        self.knowledge['win_patterns'].append(win_insight)

    def _record_loss(self, competitor: str, reason: str):
        """Record lost deal"""
        competitor_clean = competitor.strip().title()
        
        if competitor_clean not in self.knowledge['competitors']:
            self._record_competitor(competitor_clean, 'lost_deal', '')
        
        self.knowledge['competitors'][competitor_clean]['loss_rate'] += 1
        
        loss_insight = {
            'lost_to': competitor_clean,
            'reason': reason,
            'date': datetime.now().isoformat()
        }
        self.knowledge['loss_patterns'].append(loss_insight)

    def get_competitor_profile(self, competitor_name: str) -> Optional[Dict[str, Any]]:
        """Get full competitive profile"""
        for name, data in self.knowledge['competitors'].items():
            if name.lower() == competitor_name.lower() or competitor_name.lower() in name.lower():
                return data
        return None

    def get_key_insights(self) -> Dict[str, Any]:
        """Get key market and competitive insights"""
        return {
            'top_competitors': self._get_top_competitors(5),
            'market_positioning': self.knowledge['market_insights'],
            'win_rate_by_competitor': self._calculate_win_rates(),
            'customer_segments': self.knowledge['customer_segments'],
            'pricing_intelligence': self.knowledge['pricing_intelligence'],
            'key_pain_points': self.knowledge['market_insights'].get('customer_pain_points', [])[:10]
        }

    def _get_top_competitors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently mentioned competitors"""
        competitors_by_mentions = sorted(
            self.knowledge['competitors'].items(),
            key=lambda x: len(x[1]['mentions']),
            reverse=True
        )
        return [{'name': name, 'mentions': len(data['mentions'])} 
                for name, data in competitors_by_mentions[:limit]]

    def _calculate_win_rates(self) -> Dict[str, float]:
        """Calculate win rate against each competitor"""
        win_rates = {}
        for competitor_name, data in self.knowledge['competitors'].items():
            total_deals = len([d for d in self.knowledge['loss_patterns'] if d.get('lost_to') == competitor_name])
            win_rate = 1.0 - (data['loss_rate'] / total_deals) if total_deals > 0 else 0.0
            win_rates[competitor_name] = win_rate
        return win_rates

    def generate_competitive_brief(self) -> str:
        """Generate executive brief from all insights"""
        insights = self.get_key_insights()
        
        brief = f"""
COMPETITIVE INTELLIGENCE BRIEF
Generated: {self.knowledge['last_updated']}

TOP COMPETITORS:
"""
        for comp in insights['top_competitors']:
            brief += f"\n  • {comp['name']} ({comp['mentions']} mentions)"
        
        brief += f"\n\nKEY MARKET PAIN POINTS:\n"
        for pain in insights.get('key_pain_points', [])[:5]:
            brief += f"  • {pain}\n"
        
        brief += f"\nWIN RATE VS COMPETITORS:\n"
        for comp, rate in list(insights.get('win_rate_by_competitor', {}).items())[:5]:
            brief += f"  • {comp}: {rate:.0%}\n"
        
        return brief

    def _load(self):
        """Load knowledge base from disk"""
        if self.kb_file.exists():
            try:
                self.knowledge = json.loads(self.kb_file.read_text())
                self.logger.info(f"Loaded knowledge base from {self.kb_file}")
            except Exception as e:
                self.logger.warning(f"Could not load KB: {e}")

    def _save(self):
        """Save knowledge base to disk"""
        try:
            self.kb_file.write_text(json.dumps(self.knowledge, indent=2))
            self.logger.info(f"Saved knowledge base to {self.kb_file}")
        except Exception as e:
            self.logger.warning(f"Could not save KB: {e}")
