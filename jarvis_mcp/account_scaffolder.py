"""
AccountScaffolder - Auto-creates account folders and templates from natural language.
Enables zero-manual-creation account setup.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging


class AccountScaffolder:
    """
    Automatically scaffolds new account folders with template files.
    """

    def __init__(self, accounts_root: Optional[str] = None):
        """Initialize scaffolder"""
        self.logger = logging.getLogger(__name__)
        if accounts_root:
            self.accounts_root = Path(accounts_root)
        else:
            # Fall back to environment variable or default
            import os
            jarvis_home = os.getenv("JARVIS_HOME")
            if jarvis_home:
                self.accounts_root = Path(jarvis_home) / "ACCOUNTS"
            else:
                raise RuntimeError(
                    "JARVIS_HOME environment variable not set. "
                    "Run setup.bat (Windows) or setup.sh (Mac/Linux) to initialize."
                )

        try:
            self.accounts_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create accounts root directory: {self.accounts_root}", exc_info=True)
            raise
        
    def scaffold_account(self, 
                        account_name: str,
                        company_info: Optional[Dict[str, Any]] = None,
                        parent_account: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new account folder with template files.
        
        Args:
            account_name: Name of account (e.g., "Tata", "TataTele")
            company_info: Dict with company details: name, industry, revenue, etc.
            parent_account: Parent account if this is a sub-account (e.g., "Tata" for "TataTele")
            
        Returns:
            Dict with created paths and status
        """
        # Sanitize name to match config.get_account_path() logic
        safe_name = account_name.replace(" ", "_").replace("/", "_")
        # Determine where to create account
        if parent_account:
            safe_parent = parent_account.replace(" ", "_").replace("/", "_")
            parent_path = self.accounts_root / safe_parent
            if not parent_path.exists():
                raise ValueError(f"Parent account '{parent_account}' not found")
            account_path = parent_path / safe_name
        else:
            account_path = self.accounts_root / safe_name
            
        # Check if already exists
        if account_path.exists():
            self.logger.warning(f"Account already exists: {account_path}")
            return {'status': 'already_exists', 'path': str(account_path)}
            
        # Create folder
        try:
            account_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created account folder: {account_path}")
        except OSError as e:
            self.logger.error(f"Failed to create account folder: {account_path}", exc_info=True)
            raise

        result = {
            'status': 'created',
            'path': str(account_path),
            'files': {}
        }

        # Create company_research.md
        try:
            company_research = self._create_company_research(account_name, company_info)
            research_path = account_path / "company_research.md"
            with open(research_path, 'w', encoding='utf-8') as f:
                f.write(company_research)
            result['files']['company_research'] = str(research_path)
            self.logger.info(f"Created company_research.md")
        except IOError as e:
            self.logger.error(f"Failed to write company_research.md: {e}", exc_info=True)
            raise

        # Create discovery.md
        try:
            discovery = self._create_discovery_template(account_name)
            discovery_path = account_path / "discovery.md"
            with open(discovery_path, 'w', encoding='utf-8') as f:
                f.write(discovery)
            result['files']['discovery'] = str(discovery_path)
            self.logger.info(f"Created discovery.md")
        except IOError as e:
            self.logger.error(f"Failed to write discovery.md: {e}", exc_info=True)
            raise

        # Create deal_stage.json
        try:
            deal_stage = self._create_deal_stage_template(account_name)
            deal_path = account_path / "deal_stage.json"
            with open(deal_path, 'w', encoding='utf-8') as f:
                json.dump(deal_stage, f, indent=2)
            result['files']['deal_stage'] = str(deal_path)
            self.logger.info(f"Created deal_stage.json")
        except IOError as e:
            self.logger.error(f"Failed to write deal_stage.json: {e}", exc_info=True)
            raise
        except TypeError as e:
            self.logger.error(f"Failed to serialize deal_stage.json: {e}", exc_info=True)
            raise

        # Create CLAUDE.md (account-specific config)
        try:
            claude_md = self._create_claude_md_template(account_name)
            claude_path = account_path / "CLAUDE.md"
            with open(claude_path, 'w', encoding='utf-8') as f:
                f.write(claude_md)
            result['files']['claude_md'] = str(claude_path)
            self.logger.info(f"Created CLAUDE.md")
        except IOError as e:
            self.logger.error(f"Failed to write CLAUDE.md: {e}", exc_info=True)
            raise
        
        result['message'] = f"✅ Account '{account_name}' scaffolded successfully"
        return result
        
    def _create_company_research(self, account_name: str, info: Optional[Dict[str, Any]] = None) -> str:
        """Create company_research.md template"""
        if not info:
            info = {}
            
        template = f"""# {info.get('company_name', account_name)} - Company Research

## Overview
- **Company**: {info.get('company_name', account_name)}
- **Industry**: {info.get('industry', '[Industry]')}
- **Revenue**: {info.get('revenue', '[Revenue Range]')}
- **Employee Count**: {info.get('employees', '[Employee Count]')}
- **Founded**: {info.get('founded', '[Year]')}

## Business Model
[Add business model details]

## Market Position
[Add competitive positioning]

## Key Contacts
- CEO: [Name]
- VP Engineering: [Name]
- VP Sales: [Name]

## Recent News
[Add recent company news, funding, acquisitions, partnerships]

## Competitors
[List main competitors]

## Our Relevance
[Why JARVIS/our solution is relevant for this company]

---
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Source**: [Auto-scaffolded]
"""
        return template
        
    def _create_discovery_template(self, account_name: str) -> str:
        """Create discovery.md template"""
        template = f"""# {account_name} - Discovery Notes

## Current State
[Add discovery questions and answers as you learn]

### Challenges
- [ ] Challenge 1
- [ ] Challenge 2
- [ ] Challenge 3

### Goals
- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

### Timeline
[Add timeline information]

### Budget
[Add budget information]

### Decision Makers
[Add decision maker info]

## Meeting Notes
[Add meeting notes and follow-ups]

---
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: Discovery Phase
"""
        return template
        
    def _create_deal_stage_template(self, account_name: str) -> Dict[str, Any]:
        """Create deal_stage.json template"""
        return {
            "account_name": account_name,
            "stage": "discovery",
            "value_usd": 0,
            "probability": 0,
            "close_date": "",
            "owner": "",
            "contacts": [],
            "notes": "Auto-scaffolded account",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
    def _create_claude_md_template(self, account_name: str) -> str:
        """Create CLAUDE.md template for account-specific configuration"""
        template = f"""# {account_name} - Deal-Specific Configuration

## Quick Deal Summary
- **Account**: {account_name}
- **Current Stage**: [discovery / qualify / demo / negotiate / close]
- **ARR Target**: $[X]k
- **Timeline**: [deadline]
- **Key Pain**: [primary problem they're solving]
- **Champion**: [internal advocate name]

## Your Next Action
[What should you work on this deal right now? Update this as you progress]

---

## MEDDPICC Status (Track as you discover)
- **M**etrics: [numbers, ROI, cost savings] - [ ] Confirmed
- **E**conomic Buyer: [CFO/VP title] - [ ] Engaged
- **D**ecision Criteria: [evaluation requirements] - [ ] Defined
- **D**ecision Process: [procurement steps] - [ ] Mapped
- **P**aper Process: [legal/security/contract requirements] - [ ] Started
- **I**mplications: [pain points they mentioned] - [ ] Confirmed
- **C**hampion: [internal advocate] - [ ] Aligned
- **C**ompetition: [competing solutions] - [ ] Analyzed

## Skills to Run Next (In Priority Order)
1. **Get Account Summary** — See full deal dossier
2. **Track MEDDPICC** — Score all 8 dimensions
3. **Quick Insights** — Fast deal health check
4. **Get Risk Report** — Identify biggest blockers
5. **Get Battlecard** — Prepare for competition
6. **Get Meeting Prep** — Prepare for next meeting
7. **Get Proposal** — When ready to close

## Custom Notes
[Add account-specific instructions, preferences, or special handling]

## Competitors
[Who are they evaluating? Update as you learn]

## Key Stakeholders
[Names, titles, what they care about]

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: Active (update this as stage changes)
**Owner**: [Your name]

*Tip: Keep this file updated. Claude reads it automatically and adjusts recommendations based on what's here.*
"""
        return template
        
    def detect_account_mentions(self, text: str) -> list[str]:
        """
        Detect potential account mentions in text.
        Simple heuristic: capitalized words that look like company names.
        
        Returns list of potential account names.
        """
        import re
        
        # Look for capitalized words or phrases
        # This is a simple heuristic - could be improved
        pattern = r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b'
        matches = re.findall(pattern, text)
        
        # Filter out common words
        common_words = {'The', 'I', 'We', 'Company', 'Corporation', 'Inc', 'Ltd', 'LLC', 'AI', 'MCP', 'JARVIS'}
        accounts = [m for m in matches if m not in common_words and len(m) > 2]
        
        return list(set(accounts))  # Remove duplicates
        
    def format_scaffold_result(self, result: Dict[str, Any]) -> str:
        """Format scaffolding result for display"""
        lines = []
        lines.append(result.get('message', ''))
        
        if result.get('files'):
            lines.append("\n📁 Created files:")
            for file_type, path in result['files'].items():
                lines.append(f"   ✓ {file_type}: {Path(path).name}")
                
        return "\n".join(lines)
