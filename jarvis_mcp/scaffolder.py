"""Account Scaffolder - Auto-creates account folders and template files"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AccountScaffolder:
    """Scaffolds new accounts with template files"""

    def __init__(self, accounts_root: Path):
        self.accounts_root = Path(accounts_root).expanduser()

    @staticmethod
    def _safe_name(account_name: str) -> str:
        """Sanitize account name to match config.get_account_path() logic."""
        return account_name.replace(" ", "_").replace("/", "_")

    def scaffold_account(
        self,
        account_name: str,
        parent_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Create a new account folder with template files.

        Args:
            account_name: Name of the account (e.g., "Tata")
            parent_path: Optional parent folder for sub-accounts
            metadata: Optional metadata to pre-fill (company_name, revenue, industry, etc.)

        Returns:
            Path to newly created account folder
        """
        safe = self._safe_name(account_name)
        # Determine account folder path
        if parent_path:
            account_path = parent_path / safe
        else:
            account_path = self.accounts_root / safe

        # Create folder
        account_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created account folder: {account_path}")

        # Create template files
        self._create_deal_stage_json(account_path, account_name, metadata)
        self._create_company_research_md(account_path, account_name, metadata)
        self._create_discovery_md(account_path, account_name, metadata)
        self._create_claude_md(account_path, account_name)

        logger.info(f"Scaffolded account: {account_name}")
        return account_path

    def _create_deal_stage_json(
        self,
        account_path: Path,
        account_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create deal_stage.json template"""
        metadata = metadata or {}

        deal_stage = {
            "account_name": metadata.get("company_name", account_name),
            "stage": metadata.get("stage", "Initial Contact"),
            "probability": metadata.get("probability", 0),
            "deal_size": metadata.get("deal_size", 0),
            "timeline": metadata.get("timeline", "TBD"),
            "stakeholders": [],
            "activities": [],
            "next_milestone": {
                "date": "TBD",
                "activity": "To be determined",
                "description": "Set after first discovery call",
            },
            "competitive_situation": {
                "primary_competitor": metadata.get("primary_competitor", "TBD"),
                "competitor_status": "Unknown",
                "our_price": "TBD",
                "win_probability_vs_competitor": 0,
            },
            "constraints": [],
            "last_updated": datetime.now().isoformat(),
        }

        file_path = account_path / "deal_stage.json"
        file_path.write_text(json.dumps(deal_stage, indent=2))
        logger.info(f"Created {file_path.name}")

    def _create_company_research_md(
        self,
        account_path: Path,
        account_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create company_research.md template"""
        metadata = metadata or {}

        company_name = metadata.get("company_name", account_name)
        revenue = metadata.get("revenue", "TBD")
        industry = metadata.get("industry", "TBD")
        employees = metadata.get("employees", "TBD")

        content = f"""# Company Research: {company_name}

## Overview
- Company Name: {company_name}
- Revenue: {revenue}
- Industry: {industry}
- Employees: {employees}
- Founded: TBD
- HQ: TBD

## Business Model
- Primary Revenue Stream: TBD
- Customer Base: TBD
- Market Position: TBD

## Tech Stack
- Cloud Platform: TBD
- Programming Languages: TBD
- Databases: TBD
- Infrastructure: TBD

## Organizational Structure
- CEO: TBD
- VP Engineering: TBD
- VP Sales: TBD
- VP Operations: TBD

## Current Pain Points
1. **TBD** - To be identified in discovery calls
2. **TBD** - To be identified in discovery calls
3. **TBD** - To be identified in discovery calls

## Competitive Landscape
- Primary Competitors: TBD
- Differentiation: TBD
- Market Positioning: TBD

## Budget & Timeline
- Annual Tech Budget: TBD
- Estimated Deal Size: TBD
- Decision Timeline: TBD
- Approval Process: TBD

## Recent Activity
- Last researched: {datetime.now().strftime('%Y-%m-%d')}

## Strategic Initiatives
- To be identified during discovery

---

**Next Step:** Complete during first discovery call
"""

        file_path = account_path / "company_research.md"
        file_path.write_text(content)
        logger.info(f"Created {file_path.name}")

    def _create_discovery_md(
        self,
        account_path: Path,
        account_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create discovery.md template"""
        metadata = metadata or {}

        company_name = metadata.get("company_name", account_name)

        content = f"""# Discovery Notes: {company_name}

## MEDDPICC Assessment

### Metrics
- Key Metrics: To be discovered
- Business Impact: To be discovered
- Cost Impact: To be discovered

### Economic Buyer
- Economic Buyer: TBD
- Budget Authority: TBD
- Approval Authority: TBD

### Decision Criteria
1. To be identified
2. To be identified
3. To be identified

### Decision Process
- Evaluation Timeline: TBD
- Approval Process: TBD
- Key Decision Makers: TBD
- Timeline for Decision: TBD

### Paper Process
- Procurement Process: TBD
- Legal Review Required: TBD
- Security Review Required: TBD

### Pain Points
- Pain Point 1: TBD
- Pain Point 2: TBD
- Pain Point 3: TBD

### Champion
- Champion Identified: No
- Champion Name: TBD
- Champion Title: TBD
- Champion Motivation: TBD

### Competition
- Primary Competitor: TBD
- Incumbent: TBD
- Alternative Solutions: TBD

## Key Insights from Calls

**Call 1: (Date TBD)**
- Topics Discussed: TBD
- Key Insights: TBD
- Objections: TBD
- Buying Signals: TBD

## Next Steps
- Next Call: TBD
- Pre-Call Preparation: TBD
- Success Metrics: TBD

## Risk Factors
- Risk 1: TBD
- Risk 2: TBD
- Risk 3: TBD

---

**Status:** Discovery in progress
**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
"""

        file_path = account_path / "discovery.md"
        file_path.write_text(content)
        logger.info(f"Created {file_path.name}")

    def _create_claude_md(self, account_path: Path, account_name: str):
        """Create account-level CLAUDE.md template"""
        content = f"""# CLAUDE.md - {account_name}

## Account Context
- Account Name: {account_name}
- Status: New
- Created: {datetime.now().strftime('%Y-%m-%d')}

## Static Instructions (You Control These)

### Model Preferences
- Default: Claude Sonnet (balanced quality/speed)
- Reasoning tasks: Claude Opus (complex analysis)

### Skill Preferences
- Customize which skills to use and how

### Routing Rules
- Define custom skill triggers

## Dynamic Section (Auto-Updated)

### Performance Metrics
- Interactions: 0
- Average Quality: TBD

### Learned Preferences
- Auto-populated after first interactions

### Suggestions Pending
- None yet

---

**Note:** This file auto-evolves as you use the account.
"""

        file_path = account_path / "CLAUDE.md"
        file_path.write_text(content)
        logger.info(f"Created {file_path.name}")

    def prompt_for_metadata(self) -> Dict[str, Any]:
        """
        Prompt user for account metadata interactively.
        (In CLI context, this would be user input. In MCP context, this would be LLM-based.)
        """
        # Placeholder - in actual implementation, this would be interactive
        return {
            "company_name": None,
            "revenue": None,
            "industry": None,
            "employees": None,
            "stage": "Initial Contact",
            "probability": 0,
            "deal_size": 0,
        }

    def scaffold_sub_account(
        self,
        parent_path: Path,
        sub_account_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Create a sub-account under an existing account.

        Args:
            parent_path: Path to parent account
            sub_account_name: Name of sub-account
            metadata: Optional metadata

        Returns:
            Path to newly created sub-account
        """
        return self.scaffold_account(
            sub_account_name, parent_path=parent_path, metadata=metadata
        )
