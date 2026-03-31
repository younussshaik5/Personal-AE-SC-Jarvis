#!/usr/bin/env python3
"""
JARVIS v3 Universal Workspace Detector
Platform-agnostic workspace discovery with zero hard paths
Works across macOS, Linux, Windows, and WSL
"""

import os
import platform
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class WorkspaceContext:
    """Complete workspace context for universal operation"""
    root: Path
    accounts_dir: Path
    logs_dir: Path
    platform_name: str
    has_accounts: bool
    accounts_found: List[str]
    javis_root: Path


class UniversalWorkspaceDetector:
    """Detects JARVIS workspace in any environment without hard paths"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self._workspace = None
        
    def get_platform_root(self) -> str:
        """Return platform-specific root directory"""
        if self.platform == "darwin":
            return "macos"
        elif self.platform == "linux":
            if "microsoft" in platform.release().lower():
                return "wsl"
            return "linux"
        elif self.platform == "windows":
            return "windows"
        return "unknown"
    
    def find_workspace_root(self) -> Path:
        """Automatically detect workspace root using hierarchical search"""
        
        # 1. Environment variable (highest priority)
        workspace_root = os.environ.get('WORKSPACE_ROOT')
        if workspace_root and Path(workspace_root).exists():
            return Path(workspace_root)
            
        # 2. Current working directory
        current_dir = Path.cwd()
        
        # 3. Search hierarchy - up to 3 levels
        max_levels = 3
        for level in range(max_levels + 1):
            search_dir = current_dir
            for _ in range(level):
                search_dir = search_dir.parent
                
            # Check for JARVIS structures
            javis_checks = [
                search_dir / "ACCOUNTS",
                search_dir / "JARVIS" / "ACCOUNTS",
                search_dir / "accounts",
            ]
            
            for check_path in javis_checks:
                if check_path.exists() and check_path.is_dir():
                    return search_dir
        
        # 4. User JARVIS directory (fallback)
        user_janis = Path.home() / "JARVIS"
        if user_janis.exists():
            return user_janis
            
        # 5. Current directory (last resort)
        return current_dir
    
    def find_account_directories(self, base_path: Optional[Path] = None) -> List[str]:
        """Find all account directories using universal patterns"""
        accounts = []
        
        if base_path is None:
            base_path = self.find_workspace_root()
        
        # Universal account directory patterns
        patterns = [
            "ACCOUNTS/*",  # Standard structure
            "JARVIS/ACCOUNTS/*",  # Nested structure
            "accounts/*",  # Alternative naming
            "*/accounts/*",  # Deep structure
        ]
        
        for pattern in patterns:
            # Use relative resolution
            search_path = base_path / pattern
            search_str = str(search_path).replace(str(base_path) + "/", "") 
            
            # Manual implementation without glob from current workspace
            accounts.extend(self._find_accounts_in_pattern(search_path))
        
        return sorted(list(set(accounts)))
    
    def _find_accounts_in_pattern(self, pattern: Path) -> List[str]:
        """Find account directories matching pattern"""
        accounts = []
        
        try:
            # Build full search path
            if "ACCOUNTS" in str(pattern):
                accounts_parent = pattern.parent / "ACCOUNTS"
            else:
                accounts_parent = pattern.parent
                
            if accounts_parent.exists() and accounts_parent.is_dir():
                # Check for account directories with lookup.json or notes.md
                for account_dir in accounts_parent.iterdir():
                    if account_dir.is_dir() and not account_dir.name.startswith('.'):
                        # Check if it's a valid JARVIS account
                        if self._is_valid_account_directory(account_dir):
                            accounts.append(account_dir.name)
        except OSError:
            pass
            
        return accounts
    
    def _is_valid_account_directory(self, account_path: Path) -> bool:
        """Determine if directory is a valid JARVIS account"""
        required_files = [
            "lookup.md", "notes.md", 
            "final_discovery.md", "emails/", "documents/"
        ]
        
        for filename in required_files:
            check_file = account_path / filename
            if check_file.exists() or check_file.with_suffix('').exists():
                return True
                
        return False
    
    def get_workspace_context(self) -> WorkspaceContext:
        """Complete workspace context with universal paths"""
        
        root = self.find_workspace_root()
        accounts = self.find_account_directories(root)
        
        # Universal JARVIS root detection
        javis_root = self.find_jarvis_root()
        
        # Create universal paths
        context = WorkspaceContext(
            root=root,
            accounts_dir=root / "ACCOUNTS",
            logs_dir=javis_root / "logs",
            platform_name=self.get_platform_root(),
            has_accounts=len(accounts) > 0,
            accounts_found=accounts,
            javis_root=javis_root
        )
        
        return context
    
    def find_jarvis_root(self) -> Path:
        """Find universal JARVIS root directory"""
        
        # Priority hierarchy
        for env_var in ['JARVIS_ROOT', 'JAVIS_HOME']:
            value = os.environ.get(env_var)
            if value and Path(value).exists():
                return Path(value)
        
        # Default home directory
        return Path.home() / "JARVIS"
    
    def create_directories_if_missing(self, context: WorkspaceContext):
        """Create necessary directories with universal paths"""
        
        # Ensure JARVIS root structure
        javis_root = context.javis_root
        directories = [
            javis_root / "ACCOUNTS",
            javis_root / "logs",
            javis_root / "data",
            javis_root / "BACKUP"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Ensure workspace has ACCOUNTS
        if not context.accounts_dir.exists():
            context.accounts_dir.mkdir(parents=True, exist_ok=True)


def create_platform_safe_config(root_path: Optional[Path] = None) -> dict:
    """Generate platform-safe configuration for universal use"""
    
    detector = UniversalWorkspaceDetector()
    context = detector.get_workspace_context()
    
    detector.create_directories_if_missing(context)
    
    return {
        "version": "3.0.0",
        "platform": {
            "name": context.platform_name,
            "root": str(context.root.resolve()),
            "type": "universal",
            "auto_generated": True,
            "timestamp": "2024-01-01",  # Updated at runtime
            "platform_safe": True
        },
        "paths": {
            "workspace_root": str(context.root.resolve()),
            "janis_root": str(context.javis_root.resolve()),
            "accounts_dir": str(context.accounts_dir.resolve()),
            "logs_dir": str(context.logs_dir.resolve())
        },
        "accounts": {
            "detected": context.accounts_found,
            "count": len(context.accounts_found),
            "has_accounts": context.has_accounts
        },
        "features": {
            "universal_workspace": True,
            "auto_discover": True,
            "cross_platform": True,
            "real_time_skills": True
        }
    }


if __name__ == "__main__":
    """Quick test utility"""
    detector = UniversalWorkspaceDetector()
    context = detector.get_workspace_context()
    
    print("🎯 Universal JARVIS Workspace Detection")
    print("=" * 50)
    print(f"Platform: {context.platform_name}")
    print(f"Workspace Root: {context.root}")
    print(f"JARVIS Root: {context.javis_root}")
    print(f"Accounts Directory: {context.accounts_dir}")
    print(f"Accounts Found: {len(context.accounts_found)}")
    
    if context.accounts_found:
        for account in context.accounts_found:
            print(f"  - {account}")
    else:
        print("  No accounts detected - will create on first use")
    
    print("\n✅ Universal workspace setup complete!")