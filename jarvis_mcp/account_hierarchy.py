"""Account Hierarchy Manager - Handles parent/child account relationships and recursive discovery"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import functools

logger = logging.getLogger(__name__)


class AccountHierarchy:
    """Manages account hierarchy with parent/child relationships and recursive discovery"""

    def __init__(self, accounts_root: Path):
        self.accounts_root = Path(accounts_root).expanduser()
        self._account_cache: Dict[str, Path] = {}  # Cache: account_name -> account_path
        self._parent_cache: Dict[str, Optional[Path]] = {}  # Cache: account_path -> parent_path
        self._rebuild_cache()

    def _rebuild_cache(self):
        """Rebuild the account cache by scanning accounts_root recursively"""
        self._account_cache.clear()
        self._parent_cache.clear()

        if not self.accounts_root.exists():
            logger.warning(f"Accounts root does not exist: {self.accounts_root}")
            return

        # Recursively scan for account folders (folders with deal_stage.json)
        for account_path in self.accounts_root.rglob("deal_stage.json"):
            account_dir = account_path.parent
            account_name = account_dir.name

            # Only cache if it's a valid account (has deal_stage.json)
            if account_path.exists():
                self._account_cache[account_name] = account_dir
                # Store parent directory if it exists
                parent_dir = account_dir.parent
                if parent_dir != self.accounts_root:
                    self._parent_cache[str(account_dir)] = parent_dir

    def find_account(
        self, account_name: str, fuzzy: bool = True, threshold: float = 0.6
    ) -> Optional[Path]:
        """
        Find account by name, optionally using fuzzy matching.

        Args:
            account_name: Account name to find (e.g., "Tata", "TataTele", "Tata Tele")
            fuzzy: Use fuzzy matching if exact match not found
            threshold: Minimum similarity score for fuzzy match (0-1)

        Returns:
            Path to account folder if found, None otherwise
        """
        # Exact match
        if account_name in self._account_cache:
            return self._account_cache[account_name]

        # Fuzzy match
        if fuzzy:
            normalized_query = account_name.lower().replace(" ", "").replace("-", "")

            best_match = None
            best_score = threshold

            for cached_name, account_path in self._account_cache.items():
                normalized_cached = cached_name.lower().replace(" ", "").replace("-", "")
                score = SequenceMatcher(None, normalized_query, normalized_cached).ratio()

                if score > best_score:
                    best_score = score
                    best_match = account_path

            if best_match:
                logger.info(
                    f"Fuzzy matched '{account_name}' to '{best_match.name}' "
                    f"(score: {best_score:.2f})"
                )
                return best_match

        return None

    def get_account_context(self, account_path: Path) -> Dict[str, Path]:
        """
        Get account context including parent account if exists.

        Returns:
            Dict with 'account' and 'parent' (if exists) paths
        """
        context = {"account": account_path}

        # Check if this account has a parent (is a sub-account)
        parent_dir = account_path.parent
        if parent_dir != self.accounts_root and (
            parent_dir / "deal_stage.json"
        ).exists():
            context["parent"] = parent_dir

        return context

    def get_file_with_inheritance(
        self, account_path: Path, filename: str
    ) -> Optional[Path]:
        """
        Get file from account, falling back to parent if not found.

        Useful for company_research.md which should be inherited from parent if child doesn't have own.

        Args:
            account_path: Path to account folder
            filename: File to look for (e.g., "company_research.md")

        Returns:
            Path to file if found in account or parent, None otherwise
        """
        # Check account itself
        file_path = account_path / filename
        if file_path.exists():
            return file_path

        # Check parent account if exists
        parent_dir = account_path.parent
        if parent_dir != self.accounts_root and (
            parent_dir / "deal_stage.json"
        ).exists():
            parent_file = parent_dir / filename
            if parent_file.exists():
                logger.debug(
                    f"Inheriting {filename} from parent account "
                    f"{parent_dir.name}"
                )
                return parent_file

        return None

    def get_sub_accounts(self, account_path: Path) -> List[Path]:
        """Get all sub-accounts (direct children) of an account"""
        sub_accounts = []

        if not account_path.exists():
            return sub_accounts

        # Look for direct children with deal_stage.json
        for child_dir in account_path.iterdir():
            if child_dir.is_dir() and (child_dir / "deal_stage.json").exists():
                sub_accounts.append(child_dir)

        return sorted(sub_accounts)

    def get_account_hierarchy_tree(self, account_path: Path, indent: int = 0) -> str:
        """Get a text tree representation of account hierarchy"""
        lines = []
        account_name = account_path.name

        lines.append("  " * indent + f"├─ {account_name}/")

        # Add sub-accounts
        sub_accounts = self.get_sub_accounts(account_path)
        for sub_account in sub_accounts:
            tree = self.get_account_hierarchy_tree(sub_account, indent + 1)
            lines.append(tree)

        return "\n".join(lines)

    def create_sub_account(
        self, parent_path: Path, sub_account_name: str
    ) -> Path:
        """
        Create a new sub-account under a parent account.

        Args:
            parent_path: Path to parent account
            sub_account_name: Name of sub-account to create

        Returns:
            Path to newly created sub-account
        """
        sub_account_path = parent_path / sub_account_name
        sub_account_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Created sub-account {sub_account_name} under "
            f"{parent_path.name}"
        )

        # Invalidate cache
        self._rebuild_cache()

        return sub_account_path

    def list_all_accounts(self) -> List[Tuple[str, Path]]:
        """List all accounts in hierarchy (flattened)"""
        return sorted(self._account_cache.items())

    def refresh_cache(self):
        """Manually refresh account cache"""
        self._rebuild_cache()
