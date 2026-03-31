#!/usr/bin/env python3
"""
JARVIS v3 Smart Account Resolver
Intelligent account detection from conversations and files
Platform-agnostic, zero hard paths
"""

import re
from typing import Optional, List, Dict, Any
from pathlib import Path
from difflib import get_close_matches
from dataclasses import dataclass
from .autodetect import UniversalWorkspaceDetector


@dataclass
class AccountMatch:
    """Account detection result"""
    account_name: str
    confidence: float
    detection_method: str
    alternative_matches: List[str] = None


class SmartAccountResolver:
    """Multi-strategy account detection system"""
    
    def __init__(self, workspace_root: Path = None):
        self.detector = UniversalWorkspaceDetector()
        self.context = self.detector.get_workspace_context()
        self.workspace_root = workspace_root or self.context.root
        
        # Cache for performance
        self._account_cache = None
        self.load_accounts()
    
    def load_accounts(self) -> List[str]:
        """Load all known accounts"""
        if self._account_cache is None:
            accounts = set()
            
            # From context
            if self.context.accounts_found:
                accounts.update(self.context.accounts_found)
            
            # Direct scan
            accounts_dir = self.context.accounts_dir
            if accounts_dir.exists():
                for account_path in accounts_dir.iterdir():
                    if account_path.is_dir() and not account_path.name.startswith('.'):
                        accounts.add(account_path.name)
            
            self._account_cache = sorted(list(accounts))
        
        return self._account_cache
    
    def detect_account(self, text: str) -> Optional[AccountMatch]:
        """Detect account using multiple strategies"""
        
        if not self._account_cache:
            return None
        
        strategies = [
            self._exact_name_match,
            self._fuzzy_match,
            self._company_pattern_match,
            self._email_domain_match,
            self._file_context_match
        ]
        
        best_match = None
        best_confidence = 0.0
        best_method = None
        
        for strategy in strategies:
            result = strategy(text)
            if result and result.confidence > best_confidence:
                best_match = result.account_name
                best_confidence = result.confidence
                best_method = result.detection_method
        
        if best_match and best_confidence >= 0.3:  # Threshold
            return AccountMatch(
                account_name=best_match,
                confidence=best_confidence,
                detection_method=best_method or "unknown",
                alternative_matches=self.get_alternatives(best_match, text)
            )
        
        return None
    
    def _exact_name_match(self, text: str) -> Optional[AccountMatch]:
        """Direct exact name matching"""
        text_lower = text.lower()
        
        for account in self._account_cache:
            if account.lower() in text_lower:
                return AccountMatch(
                    account_name=account,
                    confidence=0.95,
                    detection_method="exact_match"
                )
        return None
    
    def _fuzzy_match(self, text: str) -> Optional[AccountMatch]:
        """Fuzzy string matching"""
        text_lower = text.lower()
        
        # Get close matches
        matches = get_close_matches(
            text_lower,
            [acc.lower() for acc in self._account_cache],
            n=3,
            cutoff=0.6
        )
        
        if matches:
            # Find original account name
            for account in self._account_cache:
                if account.lower() == matches[0]:
                    return AccountMatch(
                        account_name=account,
                        confidence=0.8,
                        detection_method="fuzzy_match"
                    )
        return None
    
    def _company_pattern_match(self, text: str) -> Optional[AccountMatch]:
        """Extract company names using patterns"""
        # Company name patterns (CamelCase, Title Case, etc.)
        company_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Microsoft Corp
            r'\b([A-Z][a-z]+(?:[.-][A-Z][a-z]+)*)\b',  # AT&T, U.S.Bank
            r'"([^"]+)"',  # Quoted names
            r'\'([^\']+)\'',  # Single quoted
        ]
        
        candidates = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            candidates.extend(matches)
        
        # Score against known accounts
        best_account = None
        best_score = 0.0
        
        for candidate in candidates:
            candidate_clean = candidate.strip().lower()
            
            for account in self._account_cache:
                account_clean = account.lower()
                
                # Exact match
                if candidate_clean == account_clean:
                    return AccountMatch(
                        account_name=account,
                        confidence=0.9,
                        detection_method="company_pattern_exact"
                    )
                
                # Partial match (token overlap)
                cand_tokens = set(candidate_clean.split())
                acc_tokens = set(account_clean.replace('_', ' ').split())
                if cand_tokens and acc_tokens:
                    overlap = len(cand_tokens.intersection(acc_tokens))
                    total = len(cand_tokens.union(acc_tokens))
                    score = overlap / total if total > 0 else 0.0
                    
                    if score > best_score and score >= 0.5:
                        best_score = score
                        best_account = account
        
        if best_account:
            return AccountMatch(
                account_name=best_account,
                confidence=best_score,
                detection_method="company_pattern_fuzzy"
            )
        
        return None
    
    def _email_domain_match(self, text: str) -> Optional[AccountMatch]:
        """Match email domains to account names"""
        emails = re.findall(r'\b[\w.-]+@([\w.-]+)\b', text)
        
        if not emails:
            return None
        
        for email_domain in emails:
            domain_clean = email_domain.split('.')[0].lower()
            
            # Direct domain to account match
            for account in self._account_cache:
                account_clean = account.lower().replace(' ', '').replace('_', '')
                
                if domain_clean == account_clean or \
                   domain_clean in account_clean or \
                   account_clean in domain_clean:
                    
                    confidence = 0.85 if domain_clean == account_clean else 0.7
                    
                    return AccountMatch(
                        account_name=account,
                        confidence=confidence,
                        detection_method="email_domain"
                    )
        
        return None
    
    def _file_context_match(self, text: str) -> Optional[AccountMatch]:
        """Check if conversation references specific account files"""
        # Look for account-specific references in surrounding context
        recent_files = self.get_recent_account_files()
        
        if not recent_files:
            return None
        
        # Use most recently touched account as candidate
        latest_account = recent_files[0] if recent_files else None
        
        if latest_account:
            # Check if text mentions account-specific terms
            account_terms = self.extract_account_terms(latest_account)
            
            for term in account_terms:
                if term.lower() in text.lower():
                    return AccountMatch(
                        account_name=latest_account,
                        confidence=0.6,
                        detection_method="file_context"
                    )
        
        return None
    
    def get_recent_account_files(self) -> List[str]:
        """Get recently accessed account files"""
        accounts = []
        
        try:
            import os
            import time
            
            cutoff = time.time() - (7 * 24 * 3600)  # Last 7 days
            
            accounts_dir = self.context.accounts_dir
            if accounts_dir.exists():
                for account_path in accounts_dir.iterdir():
                    if account_path.is_dir():
                        # Check modification time of key files
                        key_files = [
                            account_path / "lookup.md",
                            account_path / "notes.md",
                            account_path / "INTEL" / "conversations.jsonl"
                        ]
                        
                        latest_mtime = 0
                        for key_file in key_files:
                            if key_file.exists():
                                mtime = key_file.stat().st_mtime
                                latest_mtime = max(latest_mtime, mtime)
                        
                        if latest_mtime > cutoff:
                            accounts.append(account_path.name)
            
            # Sort by recency
            accounts.sort(key=lambda x: self._get_account_recency(x), reverse=True)
            
        except Exception as e:
            print(f"Warning: Could not scan recent files: {e}")
        
        return accounts
    
    def _get_account_recency(self, account_name: str) -> float:
        """Get recency score for account"""
        try:
            account_path = self.context.accounts_dir / account_name
            intel_dir = account_path / "INTEL"
            
            if intel_dir.exists():
                latest = max(
                    f.stat().st_mtime
                    for f in intel_dir.iterdir()
                    if f.is_file()
                )
                return latest
        except:
            pass
        return 0.0
    
    def extract_account_terms(self, account_name: str) -> List[str]:
        """Extract search terms from account name"""
        terms = [account_name]
        
        # Add variations
        account_lower = account_name.lower()
        terms.append(account_lower)
        
        # Split and add parts
        parts = account_name.replace('_', ' ').split()
        for part in parts:
            if len(part) > 2:  # Skip short words
                terms.append(part.lower())
        
        return list(set(terms))
    
    def get_alternatives(self, best_match: str, text: str, limit: int = 3) -> List[str]:
        """Get alternative account suggestions"""
        alternatives = []
        
        # Add fuzzy matches
        text_lower = text.lower()
        for account in self._account_cache:
            if account != best_match:
                # Simple scoring
                score = self._simple_score(account.lower(), text_lower)
                if score >= 0.4:
                    alternatives.append(account)
        
        # Return top N
        return alternatives[:limit]
    
    def _simple_score(self, account: str, text: str) -> float:
        """Simple scoring function"""
        account_tokens = set(account.split())
        text_tokens = set(text.split())
        
        if not account_tokens:
            return 0.0
        
        overlap = len(account_tokens.intersection(text_tokens))
        return overlap / len(account_tokens)
    
    def resolve_or_create(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve account or create new one if not found"""
        
        match = self.detect_account(text)
        
        result = {
            "resolved": False,
            "account_name": None,
            "confidence": 0.0,
            "method": None,
            "suggestions": [],
            "needs_creation": False
        }
        
        if match:
            result.update({
                "resolved": True,
                "account_name": match.account_name,
                "confidence": match.confidence,
                "method": match.detection_method,
                "suggestions": match.alternative_matches or []
            })
        else:
            # No match found - suggest creating new account
            result["needs_creation"] = True
            
            # Extract potential account name from text
            potential = self._extract_potential_account(text)
            if potential:
                result["suggestions"] = [potential]
            
            # Add top fuzzy matches as suggestions
            result["suggestions"].extend(
                self._get_top_fuzzy_matches(text, limit=2)
            )
        
        return result
    
    def _extract_potential_account(self, text: str) -> Optional[str]:
        """Extract potential company name for new account"""
        # Extract capitalized phrases
        company_candidates = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b', text)
        
        for candidate in company_candidates:
            # Filter out common non-company words
            skip_words = {'I', 'We', 'The', 'This', 'That', 'These', 'Those', 'Monday', 'Tuesday', 
                         'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'January', 'February',
                         'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                         'November', 'December'}
            
            if candidate not in skip_words and len(candidate) > 2:
                return candidate
        
        return None
    
    def _get_top_fuzzy_matches(self, text: str, limit: int = 2) -> List[str]:
        """Get top fuzzy matches from existing accounts"""
        text_lower = text.lower()
        
        # Score all accounts
        scored = []
        for account in self._account_cache:
            score = self._simple_score(account.lower(), text_lower)
            if score > 0.3:
                scored.append((score, account))
        
        # Sort by score and return top N
        scored.sort(reverse=True)
        return [account for score, account in scored[:limit]]
    
    def get_account_summary(self, account_name: str) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        account_path = self.context.accounts_dir / account_name
        
        summary = {
            "account": account_name,
            "path": str(account_path),
            "exists": account_path.exists(),
            "files": [],
            "last_updated": None,
            "intelligence": {}
        }
        
        if account_path.exists():
            # Scan key directories
            for subdir in ["INTEL", "emails", "documents", "MEETINGS"]:
                dir_path = account_path / subdir
                if dir_path.exists():
                    files = [f.name for f in dir_path.iterdir() if f.is_file()]
                    summary["files"].extend([f"{subdir}/{f}" for f in files])
            
            # Get latest modification time
            try:
                latest = max(
                    f.stat().st_mtime
                    for f in account_path.rglob("*")
                    if f.is_file()
                )
                from datetime import datetime
                summary["last_updated"] = datetime.fromtimestamp(latest).isoformat()
            except:
                pass
        
        return summary


def main():
    """Quick test of account resolver"""
    import sys
    
    resolver = SmartAccountResolver()
    
    print("🎯 Smart Account Resolver Test")
    print("=" * 50)
    print(f"Known accounts: {len(resolver.load_accounts())}")
    
    if resolver._account_cache:
        print("\nAccounts:")
        for acc in resolver._account_cache[:5]:
            print(f"  - {acc}")
    
    # Test detection
    test_texts = [
        "Meeting with Microsoft about Teams integration",
        "Email from john@microsoft.com about the proposal",
        "Discussion with Apple regarding security",
        "Call with Google Cloud team"
    ]
    
    print("\n🧪 Detection Tests:")
    for text in test_texts:
        result = resolver.detect_account(text)
        if result:
            print(f"  ✓ '{text[:40]}...' → {result.account_name} ({result.confidence:.2f})")
        else:
            print(f"  ✗ '{text[:40]}...' → No match")
    
    print("\n✅ Account Resolver ready!")


if __name__ == "__main__":
    main()