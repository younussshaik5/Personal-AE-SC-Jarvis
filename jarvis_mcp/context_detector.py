"""Context Detector - Detects account context from current working directory"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ContextDetector:
    """Detects account context from current working directory and environment"""

    def __init__(self, accounts_root: Path):
        self.accounts_root = Path(accounts_root).expanduser()

    def detect_account_context(self) -> Optional[Dict[str, Any]]:
        """
        Detect if current working directory is an account folder.

        Returns:
            Dict with account context if detected:
            {
                'account_name': 'Tata',
                'account_path': Path('/...../ACCOUNTS/Tata'),
                'is_cowork': True
            }
            None if not in an account folder
        """
        cwd = Path.cwd()

        # Check if cwd or any parent is an account folder (has deal_stage.json)
        current = cwd
        while current != current.parent:  # Stop at root
            deal_stage_path = current / "deal_stage.json"

            if deal_stage_path.exists():
                try:
                    deal_stage_data = json.loads(deal_stage_path.read_text())
                    account_name = deal_stage_data.get("account_name", current.name)

                    logger.info(
                        f"Detected account context: {account_name} "
                        f"at {current}"
                    )

                    return {
                        "account_name": account_name,
                        "account_path": current,
                        "is_cowork": True,
                        "cwd": cwd,
                    }
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Error reading deal_stage.json: {e}")

            current = current.parent

        return None

    def is_in_account_folder(self) -> bool:
        """Check if current working directory is inside an account folder"""
        return self.detect_account_context() is not None

    def get_account_from_context(
        self, explicit_account: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get account context, preferring explicit account if provided.

        Args:
            explicit_account: Explicitly provided account name (takes priority)

        Returns:
            Account context dict if found, None otherwise
        """
        # Explicit account takes priority
        if explicit_account:
            logger.info(f"Using explicit account: {explicit_account}")
            return {
                "account_name": explicit_account,
                "is_explicit": True,
            }

        # Otherwise detect from context
        context = self.detect_account_context()
        if context:
            context["is_explicit"] = False
            return context

        return None

    def get_environment_account(self) -> Optional[str]:
        """Get account from environment variable JARVIS_ACCOUNT"""
        account = os.getenv("JARVIS_ACCOUNT")
        if account:
            logger.info(f"Account from environment: {account}")
        return account

    def infer_context_info(self) -> Dict[str, Any]:
        """Get comprehensive context information"""
        context = {
            "cwd": Path.cwd(),
            "accounts_root": self.accounts_root,
            "in_account": False,
            "account_context": None,
            "env_account": None,
        }

        # Check environment
        context["env_account"] = self.get_environment_account()

        # Check CWD
        account_context = self.detect_account_context()
        if account_context:
            context["in_account"] = True
            context["account_context"] = account_context

        return context
