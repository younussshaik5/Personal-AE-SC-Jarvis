"""
AccountHierarchy - Manages parent/child account relationships.
Supports Tata → TataTele, TataSky sub-accounts with inheritance.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging
from difflib import SequenceMatcher


class AccountHierarchy:
    """
    Manages account folder hierarchy and relationships.
    Supports nested accounts: ACCOUNTS/Tata/TataTele/ inherits from ACCOUNTS/Tata/
    """

    def __init__(self, accounts_root: Optional[str] = None):
        """Initialize hierarchy manager"""
        self.logger = logging.getLogger(__name__)
        self.accounts_root = Path(accounts_root) if accounts_root else Path.home() / "Documents" / "claude space" / "ACCOUNTS"
        self.accounts_root.mkdir(parents=True, exist_ok=True)
        
        # Cache for account lookups (account_name -> path)
        self._hierarchy_cache = {}
        self._cache_valid = False
        
    def rebuild_cache(self):
        """Rebuild account hierarchy cache"""
        self._hierarchy_cache = {}
        self._scan_hierarchy(self.accounts_root, parent_path=None)
        self._cache_valid = True
        self.logger.info(f"Rebuilt hierarchy cache: {len(self._hierarchy_cache)} accounts found")
        
    def _scan_hierarchy(self, path: Path, parent_path: Optional[str] = None, depth: int = 0):
        """Recursively scan for account folders"""
        if depth > 5:  # Limit recursion depth
            return
            
        try:
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if this looks like an account folder
                    if self._is_account_folder(item):
                        account_name = item.name
                        self._hierarchy_cache[account_name.lower()] = {
                            'path': str(item),
                            'name': account_name,
                            'parent': parent_path,
                            'depth': depth
                        }
                        # Recurse into child accounts
                        self._scan_hierarchy(item, parent_path=account_name, depth=depth+1)
        except PermissionError:
            self.logger.warning(f"Permission denied scanning {path}")
            
    def _is_account_folder(self, path: Path) -> bool:
        """Check if folder looks like an account folder"""
        # Look for account markers: deal_stage.json or discovery.md
        has_deal_stage = (path / "deal_stage.json").exists()
        has_discovery = (path / "discovery.md").exists()
        return has_deal_stage or has_discovery
        
    def get_account_path(self, account_name: str, fuzzy_match: bool = True) -> Optional[Path]:
        """
        Find account path by name, with optional fuzzy matching.
        
        Returns:
            Path to account folder or None if not found
            
        Examples:
            get_account_path("Tata") → /ACCOUNTS/Tata/
            get_account_path("TataTele") → /ACCOUNTS/Tata/TataTele/
            get_account_path("tata", fuzzy_match=True) → /ACCOUNTS/Tata/ (case-insensitive)
            get_account_path("tata tele", fuzzy_match=True) → /ACCOUNTS/Tata/TataTele/ (removes spaces)
        """
        if not self._cache_valid:
            self.rebuild_cache()
            
        account_key = account_name.lower()
        
        # Exact match first
        if account_key in self._hierarchy_cache:
            return Path(self._hierarchy_cache[account_key]['path'])
            
        # Fuzzy matching
        if fuzzy_match:
            # Try removing spaces
            normalized = account_name.replace(" ", "").lower()
            if normalized in self._hierarchy_cache:
                return Path(self._hierarchy_cache[normalized]['path'])
                
            # Try similarity matching (best match)
            best_match = None
            best_ratio = 0.0
            
            for cached_name in self._hierarchy_cache.keys():
                ratio = SequenceMatcher(None, normalized, cached_name).ratio()
                if ratio > best_ratio and ratio > 0.75:  # 75% match threshold
                    best_ratio = ratio
                    best_match = cached_name
                    
            if best_match:
                self.logger.info(f"Fuzzy matched '{account_name}' → '{best_match}' (similarity: {best_ratio:.1%})")
                return Path(self._hierarchy_cache[best_match]['path'])
                
        return None
        
    def get_parent_account_path(self, account_name: str) -> Optional[Path]:
        """Get parent account path if this is a child account"""
        if not self._cache_valid:
            self.rebuild_cache()
            
        account_key = account_name.lower()
        
        # Exact match
        if account_key in self._hierarchy_cache:
            parent_name = self._hierarchy_cache[account_key].get('parent')
            if parent_name:
                return Path(self._hierarchy_cache[parent_name.lower()]['path'])
                
        return None
        
    def list_accounts(self, parent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all accounts, optionally filtered by parent.
        
        Returns:
            List of account info dicts with: name, path, parent, depth
        """
        if not self._cache_valid:
            self.rebuild_cache()
            
        if parent_name:
            parent_key = parent_name.lower()
            return [
                info for info in self._hierarchy_cache.values()
                if info['parent'] and info['parent'].lower() == parent_key
            ]
        else:
            return list(self._hierarchy_cache.values())
            
    def get_account_context(self, account_name: str) -> Dict[str, Any]:
        """
        Get full account context including parent account info.
        
        Returns:
            Dict with: path, name, parent_path, parent_name, company_research (if exists), discovery (if exists), deal_stage (if exists)
        """
        account_path = self.get_account_path(account_name)
        if not account_path:
            return {}
            
        context = {
            'path': str(account_path),
            'name': account_path.name,
            'account_key': account_path.name.lower()
        }
        
        # Parent account info
        parent_path = self.get_parent_account_path(account_name)
        if parent_path:
            context['parent_path'] = str(parent_path)
            context['parent_name'] = parent_path.name
            
        # Load company research (inherit from parent if not present)
        company_research_path = account_path / "company_research.md"
        if company_research_path.exists():
            with open(company_research_path, 'r') as f:
                context['company_research'] = f.read()
        elif parent_path:
            parent_research = parent_path / "company_research.md"
            if parent_research.exists():
                with open(parent_research, 'r') as f:
                    context['company_research_inherited'] = f.read()
                    context['company_research_source'] = 'parent'
                    
        # Load discovery
        discovery_path = account_path / "discovery.md"
        if discovery_path.exists():
            with open(discovery_path, 'r') as f:
                context['discovery'] = f.read()
                
        # Load deal stage
        deal_stage_path = account_path / "deal_stage.json"
        if deal_stage_path.exists():
            with open(deal_stage_path, 'r') as f:
                context['deal_stage'] = json.load(f)
                
        return context
        
    def get_child_accounts(self, parent_name: str) -> List[str]:
        """Get list of child account names for a parent"""
        return [info['name'] for info in self.list_accounts(parent_name)]
        
    def create_child_account(self, parent_name: str, child_name: str) -> Path:
        """
        Create a child account under a parent.
        
        Example: create_child_account("Tata", "TataTele") → /ACCOUNTS/Tata/TataTele/
        """
        parent_path = self.get_account_path(parent_name)
        if not parent_path:
            raise ValueError(f"Parent account '{parent_name}' not found")
            
        child_path = parent_path / child_name
        child_path.mkdir(parents=True, exist_ok=True)
        
        # Invalidate cache
        self._cache_valid = False
        
        self.logger.info(f"Created child account: {parent_name}/{child_name}")
        return child_path
        
    def get_hierarchy_tree(self, root_name: Optional[str] = None, indent: int = 0) -> str:
        """
        Get visual tree representation of account hierarchy.
        
        Example output:
            Tata/
              TataTele/
              TataSky/
            AcmeCorp/
        """
        if not self._cache_valid:
            self.rebuild_cache()
            
        lines = []
        
        if root_name:
            root_path = self.get_account_path(root_name)
            if root_path:
                lines.append("  " * indent + root_path.name + "/")
                for child in self.get_child_accounts(root_name):
                    lines.append(self.get_hierarchy_tree(child, indent+1))
        else:
            # Show top-level accounts only
            for account in self._hierarchy_cache.values():
                if account['depth'] == 0:
                    lines.append(account['name'] + "/")
                    for child in self.get_child_accounts(account['name']):
                        lines.append("  " + child + "/")
                        
        return "\n".join(lines)
