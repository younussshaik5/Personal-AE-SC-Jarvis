"""
ContextDetector - Auto-detects account context from current working directory.
Enables automatic account selection without manual specification.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from .account_hierarchy import AccountHierarchy


class ContextDetector:
    """
    Detects account context from filesystem operations.
    If user is working in ACCOUNTS/Tata/TataTele/, automatically uses that account.
    """

    def __init__(self, accounts_root: Optional[str] = None):
        """Initialize context detector"""
        self.logger = logging.getLogger(__name__)
        self.accounts_root = Path(accounts_root) if accounts_root else Path.home() / "Documents" / "claude space" / "ACCOUNTS"
        self.hierarchy = AccountHierarchy(str(self.accounts_root))
        self._current_context = None
        
    def detect_context(self, cwd: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Detect account context from current working directory.
        
        Returns:
            Account context dict or None if not in account folder
        """
        cwd = Path(cwd) if cwd else Path.cwd()
        
        # Check if we're inside ACCOUNTS folder
        try:
            cwd_relative = cwd.relative_to(self.accounts_root)
        except ValueError:
            # Not in ACCOUNTS folder
            return None
            
        # Extract account name (first folder after ACCOUNTS/)
        parts = cwd_relative.parts
        if not parts:
            return None
            
        account_name = parts[0]
        
        # Get full context for this account
        context = self.hierarchy.get_account_context(account_name)
        
        if context:
            # Add current working directory info
            context['current_directory'] = str(cwd)
            context['relative_path'] = str(cwd_relative)
            context['detected_at'] = str(Path.cwd())
            
            # Check if working in a sub-account
            if len(parts) > 1:
                sub_account_name = parts[1]
                context['sub_account'] = sub_account_name
                sub_context = self.hierarchy.get_account_context(f"{account_name}/{sub_account_name}")
                if sub_context:
                    context.update(sub_context)
                    
            self._current_context = context
            self.logger.info(f"Detected account context: {context.get('name', 'unknown')} at {cwd}")
            return context
            
        return None
        
    def get_account_from_file_content(self, file_path: str) -> Optional[str]:
        """
        Extract account name from file content (for deal_stage.json detection).
        """
        try:
            path = Path(file_path)
            if path.name == "deal_stage.json":
                with open(path, 'r') as f:
                    data = json.load(f)
                    return data.get('account_name') or data.get('company')
        except Exception as e:
            self.logger.debug(f"Could not extract account from {file_path}: {e}")
            
        return None
        
    def detect_from_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect account context from a file path.
        
        Example: /ACCOUNTS/Tata/TataTele/proposal.pdf → TataTele context
        """
        path = Path(file_path)
        
        # Try to work backwards from file path to find ACCOUNTS folder
        for parent in path.parents:
            if parent.name == "ACCOUNTS":
                # Found ACCOUNTS folder, extract account names
                relative = path.relative_to(parent)
                parts = relative.parts
                
                if len(parts) >= 2:
                    account_name = parts[0]
                    context = self.hierarchy.get_account_context(account_name)
                    if context:
                        context['detected_from_file'] = file_path
                        return context
                        
        return None
        
    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get last detected context"""
        return self._current_context
        
    def is_in_account_folder(self, path: Optional[str] = None) -> bool:
        """Check if path is inside an account folder"""
        cwd = Path(path) if path else Path.cwd()
        try:
            cwd.relative_to(self.accounts_root)
            return True
        except ValueError:
            return False
            
    def get_context_for_skill(self, 
                             skill_name: str,
                             explicit_account: Optional[str] = None,
                             cwd: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get account context for a skill call.
        Prefers explicit account, falls back to current directory detection.
        
        Priority:
        1. explicit_account parameter
        2. Current working directory detection
        3. None
        """
        # Explicit account provided
        if explicit_account:
            context = self.hierarchy.get_account_context(explicit_account)
            if context:
                context['source'] = 'explicit'
                return context
                
        # Try to detect from cwd
        detected = self.detect_context(cwd)
        if detected:
            detected['source'] = 'auto_detected'
            return detected
            
        # Try to use last detected context
        if self._current_context:
            self._current_context['source'] = 'cached'
            return self._current_context
            
        return None
        
    def format_context_info(self, context: Dict[str, Any]) -> str:
        """Format context information for user display"""
        lines = []
        lines.append(f"📍 Account: {context.get('name', 'Unknown')}")
        
        if context.get('parent_name'):
            lines.append(f"   Parent: {context['parent_name']}")
            
        if context.get('source'):
            lines.append(f"   Source: {context['source']}")
            
        if context.get('company_research'):
            lines.append(f"   ✓ Has company research")
            
        if context.get('discovery'):
            lines.append(f"   ✓ Has discovery notes")
            
        if context.get('deal_stage'):
            lines.append(f"   ✓ Has deal stage")
            
        return "\n".join(lines)

    def get_current_account_path(self) -> Optional[Path]:
        """Get current account path if in account folder"""
        context = self.detect_context()
        if context:
            return Path(context['path'])
        return None
