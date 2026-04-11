"""
CRM API Server - Real backend for interactive dashboard
Serves account data, deals, contacts, and activity logs
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from .account_hierarchy import AccountHierarchy
from .comprehensive_data_aggregator import ComprehensiveDataAggregator


class CRMAPIServer:
    """Backend API for interactive CRM dashboard"""

    def __init__(self, accounts_root: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.accounts_root = Path(accounts_root) if accounts_root else Path.home() / "Documents" / "claude space" / "ACCOUNTS"
        self.hierarchy = AccountHierarchy(str(self.accounts_root))

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts with basic info"""
        self.hierarchy.rebuild_cache()
        accounts = []

        for account_info in self.hierarchy.list_accounts():
            account_name = account_info['name']
            account_path = Path(account_info['path'])

            # Load basic account data
            company_profile = {}
            deal_count = 0
            contact_count = 0

            # Load company profile
            profile_file = account_path / "company_profile.json"
            if profile_file.exists():
                try:
                    company_profile = json.loads(profile_file.read_text())
                except:
                    pass

            # Load deals
            deal_file = account_path / "deal_stage.json"
            if deal_file.exists():
                try:
                    deal_data = json.loads(deal_file.read_text())
                    if isinstance(deal_data, dict) and "deals" in deal_data:
                        deal_count = len(deal_data["deals"])
                    elif isinstance(deal_data, dict):
                        deal_count = len(deal_data)
                except:
                    pass

            # Extract contacts from discovery notes
            discovery_file = account_path / "discovery.md"
            if discovery_file.exists():
                try:
                    content = discovery_file.read_text()
                    # Count email mentions as rough contact count
                    contact_count = content.count("@")
                except:
                    pass

            accounts.append({
                'id': account_name.lower(),
                'name': account_name,
                'path': str(account_path),
                'parent': account_info.get('parent'),
                'revenue': company_profile.get('revenue', 'Unknown'),
                'industry': company_profile.get('industry', 'Unknown'),
                'size': company_profile.get('size', 'Unknown'),
                'deals_count': deal_count,
                'contacts_count': contact_count,
                'description': company_profile.get('description', ''),
                'last_updated': datetime.now().isoformat()
            })

        return sorted(accounts, key=lambda x: x['name'])

    def get_account_detail(self, account_name: str) -> Dict[str, Any]:
        """Get full account details"""
        account_path = self.hierarchy.get_account_path(account_name)
        if not account_path:
            return {'error': 'Account not found'}

        aggregator = ComprehensiveDataAggregator(str(account_path))
        context = aggregator.aggregate_all_context()

        return {
            'account_name': account_name,
            'account_path': str(account_path),
            'company_profile': context.get('company_profile', {}),
            'competitive_intelligence': context.get('competitive_intelligence', {}),
            'deal_pipeline': context.get('deal_pipeline', {}),
            'relationships': context.get('relationships', {}),
            'discovery_notes': context.get('discovery_notes', []),
            'timeline': context.get('timeline', [])
        }

    def get_deals(self, account_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all deals or deals for specific account"""
        deals = []

        if account_name:
            # Get deals for specific account
            account_path = self.hierarchy.get_account_path(account_name)
            if not account_path:
                return []

            deal_file = account_path / "deal_stage.json"
            if deal_file.exists():
                try:
                    data = json.loads(deal_file.read_text())
                    deal_dict = data.get("deals", data) if isinstance(data, dict) and "deals" in data else data

                    for deal_id, deal_info in deal_dict.items():
                        if isinstance(deal_info, dict):
                            deals.append({
                                'id': deal_id,
                                'account': account_name,
                                'name': deal_info.get('name', deal_id),
                                'stage': deal_info.get('stage', 'unknown'),
                                'value': deal_info.get('value', 0),
                                'probability': deal_info.get('probability', 0),
                                'close_date': deal_info.get('close_date', '')
                            })
                except:
                    pass
        else:
            # Get deals from all accounts
            self.hierarchy.rebuild_cache()
            for account_info in self.hierarchy.list_accounts():
                account = account_info['name']
                account_path = Path(account_info['path'])
                deal_file = account_path / "deal_stage.json"

                if deal_file.exists():
                    try:
                        data = json.loads(deal_file.read_text())
                        deal_dict = data.get("deals", data) if isinstance(data, dict) and "deals" in data else data

                        for deal_id, deal_info in deal_dict.items():
                            if isinstance(deal_info, dict):
                                deals.append({
                                    'id': f"{account}_{deal_id}",
                                    'account': account,
                                    'name': deal_info.get('name', deal_id),
                                    'stage': deal_info.get('stage', 'unknown'),
                                    'value': deal_info.get('value', 0),
                                    'probability': deal_info.get('probability', 0),
                                    'close_date': deal_info.get('close_date', '')
                                })
                    except:
                        pass

        # Sort by stage and value
        stage_order = {'discovery': 0, 'qualify': 1, 'demo': 2, 'negotiate': 3, 'close': 4}
        deals.sort(key=lambda x: (stage_order.get(x['stage'], 99), -x['value']))

        return deals

    def get_contacts(self, account_name: str) -> List[Dict[str, Any]]:
        """Get contacts for an account"""
        account_path = self.hierarchy.get_account_path(account_name)
        if not account_path:
            return []

        contacts = []
        aggregator = ComprehensiveDataAggregator(str(account_path))
        context = aggregator.aggregate_all_context()

        relationships = context.get('relationships', {})
        for rel_id, rel_info in relationships.items():
            if isinstance(rel_info, dict):
                contacts.append({
                    'id': rel_id,
                    'name': rel_info.get('name', 'Unknown'),
                    'title': rel_info.get('title', 'Unknown'),
                    'email': rel_info.get('email', ''),
                    'phone': rel_info.get('phone', ''),
                    'influence': rel_info.get('influence', 'medium')
                })

        return contacts

    def get_activity_log(self, account_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity log for account(s)"""
        activities = []

        if account_name:
            # Get activity for specific account
            account_path = self.hierarchy.get_account_path(account_name)
            if account_path:
                activity_file = account_path / ".activity_log.json"
                if activity_file.exists():
                    try:
                        data = json.loads(activity_file.read_text())
                        activities = data.get('activities', [])[:limit]
                    except:
                        pass
        else:
            # Get activity from all accounts
            self.hierarchy.rebuild_cache()
            for account_info in self.hierarchy.list_accounts():
                account = account_info['name']
                account_path = Path(account_info['path'])
                activity_file = account_path / ".activity_log.json"

                if activity_file.exists():
                    try:
                        data = json.loads(activity_file.read_text())
                        for activity in data.get('activities', []):
                            activity['account'] = account
                            activities.append(activity)
                    except:
                        pass

        # Sort by timestamp descending
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return activities[:limit]

    def search_accounts(self, query: str) -> List[Dict[str, Any]]:
        """Search accounts by name, industry, etc"""
        all_accounts = self.get_all_accounts()
        query_lower = query.lower()

        matches = [
            acc for acc in all_accounts
            if query_lower in acc['name'].lower()
            or query_lower in acc.get('industry', '').lower()
            or query_lower in acc.get('description', '').lower()
        ]

        return matches

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary stats for dashboard"""
        self.hierarchy.rebuild_cache()

        all_accounts = self.get_all_accounts()
        all_deals = self.get_deals()

        # Calculate metrics
        total_revenue = sum(d.get('value', 0) for d in all_deals)
        deal_by_stage = {}
        for deal in all_deals:
            stage = deal['stage']
            deal_by_stage[stage] = deal_by_stage.get(stage, 0) + 1

        probability_weighted_value = sum(
            d.get('value', 0) * d.get('probability', 0)
            for d in all_deals
        )

        return {
            'total_accounts': len(all_accounts),
            'total_deals': len(all_deals),
            'total_pipeline_value': total_revenue,
            'weighted_value': probability_weighted_value,
            'deals_by_stage': deal_by_stage,
            'accounts_by_industry': self._group_by_industry(all_accounts),
            'top_accounts': sorted(all_accounts, key=lambda x: x['deals_count'], reverse=True)[:5],
            'top_deals': sorted(all_deals, key=lambda x: x['value'], reverse=True)[:5]
        }

    def _group_by_industry(self, accounts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group accounts by industry"""
        industries = {}
        for account in accounts:
            industry = account.get('industry', 'Unknown')
            industries[industry] = industries.get(industry, 0) + 1
        return industries

    def create_account(self, account_name: str, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new account"""
        account_path = self.accounts_root / account_name
        account_path.mkdir(parents=True, exist_ok=True)

        # Create company profile
        profile_file = account_path / "company_profile.json"
        profile_file.write_text(json.dumps(company_data, indent=2))

        # Create empty deal stage
        deal_file = account_path / "deal_stage.json"
        deal_file.write_text(json.dumps({"deals": {}}, indent=2))

        # Create empty discovery
        discovery_file = account_path / "discovery.md"
        discovery_file.write_text(f"# {account_name} Discovery Notes\n\n")

        # Invalidate cache
        self.hierarchy._cache_valid = False

        return {
            'success': True,
            'account_name': account_name,
            'account_path': str(account_path)
        }

    def update_deal(self, account_name: str, deal_id: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update deal information"""
        account_path = self.hierarchy.get_account_path(account_name)
        if not account_path:
            return {'error': 'Account not found'}

        deal_file = account_path / "deal_stage.json"
        try:
            data = json.loads(deal_file.read_text())
            deals = data.get("deals", data) if isinstance(data, dict) and "deals" in data else data

            deals[deal_id] = deal_data
            deal_file.write_text(json.dumps({"deals": deals}, indent=2))

            return {'success': True, 'deal_id': deal_id}
        except Exception as e:
            return {'error': str(e)}

    def log_activity(self, account_name: str, activity_type: str, description: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Log activity for an account"""
        account_path = self.hierarchy.get_account_path(account_name)
        if not account_path:
            return {'error': 'Account not found'}

        activity_file = account_path / ".activity_log.json"

        activities = []
        if activity_file.exists():
            try:
                existing = json.loads(activity_file.read_text())
                activities = existing.get('activities', [])
            except:
                pass

        # Add new activity
        activities.append({
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'description': description,
            'data': data or {}
        })

        activity_file.write_text(json.dumps({'activities': activities}, indent=2))

        return {'success': True, 'activity_logged': True}
