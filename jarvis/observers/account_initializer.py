"""Account Auto-Initializer - Automatically sets up new account folders with smartness.

This component watches for new directories under ACCOUNTS/ and automatically
creates the necessary structure and smartness files for that account.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class AccountAutoInitializer:
    """Automatically initialize new account folders with JARVIS smartness."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("account_initializer")
        self.workspace_root = config_manager.config.workspace_root
        # Keep memory_dir for competitor profile lookups
        self.memory_dir = Path(self.workspace_root) / "MEMORY"
        # CHANGED: Watch entire ACCOUNTS/ directory to support all teams (AE, Presales, etc.)
        self.accounts_dir = Path(self.workspace_root) / "ACCOUNTS"
        self.initialized_accounts: set = set()  # Track initialized to avoid re-init

    async def start(self):
        """Start the account initializer."""
        self.logger.info("Starting account auto-initializer")
        # Subscribe to file system events
        self.event_bus.subscribe("file.created", self._handle_file_created)
        # Also run initialization on startup for existing accounts that might be missing files
        asyncio.create_task(self._initialize_existing_accounts())
        self.logger.info("Account auto-initializer started")

    async def stop(self):
        """Stop the account initializer."""
        self.logger.info("Account auto-initializer stopped")

    async def _handle_file_created(self, event: Event):
        """Handle file/directory creation events."""
        path_str = event.data.get("path", "")
        is_dir = event.data.get("is_directory", False)

        if not is_dir:
            return  # Only care about directories

        path = Path(path_str)

        try:
            rel_path = path.resolve().relative_to(self.accounts_dir.resolve())
            parts = rel_path.parts

            if len(parts) == 1:
                # Direct child of ACCOUNTS/ — every folder is an account (or opportunity,
                # JARVIS makes no distinction: user decides what each folder represents)
                account_name = parts[0]
                if not account_name.startswith((".", "_")):
                    self.logger.info("Detected new account folder", account=account_name)
                    await self._initialize_account(account_name, account_path=path)

        except ValueError:
            return
        except Exception as e:
            self.logger.error("Error processing new folder", error=str(e))

    async def _initialize_existing_accounts(self):
        """Scan existing accounts and ensure they have required files."""
        await asyncio.sleep(5)  # Wait a bit for system to stabilize
        try:
            if not self.accounts_dir.exists():
                return
            # Walk through all subdirectories to find account folders
            for root, dirs, files in os.walk(self.accounts_dir):
                root_path = Path(root)
                # Skip the accounts_dir itself, only process subdirectories
                if root_path == self.accounts_dir:
                    continue
                # Check if this directory looks like an account folder
                dir_name = root_path.name
                # Skip if already initialized
                if dir_name in self.initialized_accounts:
                    continue
                # Initialize this as an account using the full path
                self.logger.info("Initializing existing account", account=dir_name, path=str(root_path))
                await self._initialize_account(dir_name, force_check=True, account_path=root_path)
        except Exception as e:
            self.logger.error("Failed to initialize existing accounts", error=str(e))

    async def _initialize_account(self, account_name: str, force_check: bool = False, account_path=None):
        """Create smartness files for an account if missing.
        
        Args:
            account_name: Name of the account
            force_check: If True, check and update even if already initialized
            account_path: Optional full path to account directory. If None, uses self.accounts_dir / account_name
        """
        try:
            if account_path is None:
                account_dir = self.accounts_dir / account_name
            else:
                account_dir = account_path
                
            if not account_dir.exists():
                self.logger.warning("Account dir missing", account=account_name)
                return

            # Skip if already initialized and not forcing
            if account_name in self.initialized_accounts and not force_check:
                return

            created_files = []

            # 1. Ensure standard subfolders exist
            # Note: opportunity subfolders (e.g. "Tata Sky/") are created by the user,
            # not listed here. Any non-standard folder → auto-initialized as opportunity.
            subfolders = {
                "MEETINGS":  "Drop recordings here — JARVIS auto-processes",
                "DOCUMENTS": "RFPs, contracts, briefs, NDAs — JARVIS reads and extracts",
                "EMAILS":    "Paste email threads as .md or .txt — JARVIS extracts context",
                "INTEL":     "Auto-generated by JARVIS — competitive, ROI, proposals",
                "meetings":  "Processed meeting notes (auto-written by JARVIS)",
            }
            for folder_name, description in subfolders.items():
                folder_path = account_dir / folder_name
                if not folder_path.exists():
                    folder_path.mkdir(parents=True, exist_ok=True)
                    # README.md inside each drop folder so user knows what to put there
                    if folder_name in ("MEETINGS", "DOCUMENTS", "EMAILS"):
                        (folder_path / "README.md").write_text(
                            f"# {folder_name}\n\n{description}\n\n"
                            f"JARVIS watches this folder and auto-processes anything you drop here.\n"
                        )
                    created_files.append(f"{folder_name}/")

            # 1b. Presales intelligence sections — auto-populated by JARVIS via NVIDIA + web research
            presales_sections = {
                "DISCOVERY": {
                    "discovery_prep.md": (
                        f"# Discovery Prep — {account_name}\n\n"
                        "*JARVIS is generating discovery questions based on company intel and MEDDPICC gaps.*\n"
                        "*This file is auto-refreshed when new intel arrives or MEDDPICC dimensions change.*\n\n"
                        "---\n\n## Company Background\n*Generating...*\n\n"
                        "## Top Discovery Questions\n*Generating...*\n\n"
                        "## MEDDPICC Gap Questions\n*Generating...*\n\n"
                        "## Stakeholders to Target\n*Generating...*\n"
                    ),
                    "final_discovery.md": (
                        f"# Final Discovery Notes — {account_name}\n\n"
                        "*Update this file after each discovery call.*\n"
                        "*Each update is appended — full history is preserved.*\n\n"
                        "---\n\n"
                        f"## [Add entry: {datetime.now().strftime('%Y-%m-%d')}]\n\n"
                        "**Attendees:**\n**Pain Points Confirmed:**\n**Budget Signal:**\n**Champion:**\n**Next Step:**\n"
                    ),
                },
                "RFP": {
                    "README.md": (
                        f"# RFP — {account_name}\n\n"
                        "Drop the RFP document here (PDF, DOCX, or TXT).\n\n"
                        "JARVIS will automatically:\n"
                        "1. Extract all requirements and scoring criteria\n"
                        "2. Generate `rfp_analysis.md` — requirements mapped to our capabilities\n"
                        "3. Generate `rfp_responses.md` — draft responses to each question\n\n"
                        "Ask Claude: *'fill the RFP for [account]'* to get the complete assembled response.\n"
                    ),
                },
                "BATTLECARD": {
                    "battlecard.md": (
                        f"# Battlecard — {account_name}\n\n"
                        "*JARVIS is generating competitive positioning using live web research + NVIDIA reasoning.*\n"
                        "*Auto-refreshed when new intel or competitive signals are detected.*\n\n"
                        "---\n\n## Top Differentiators\n*Generating...*\n\n"
                        "## Competitor Weaknesses\n*Generating...*\n\n"
                        "## Trap-Setting Questions\n*Generating...*\n\n"
                        "## Objection Responses\n*Generating...*\n\n"
                        "## Win Probability\n*Generating...*\n"
                    ),
                    "battlecard_data.json": json.dumps({
                        "account": account_name,
                        "generated_at": datetime.now().isoformat(),
                        "status": "pending",
                        "differentiators": [],
                        "competitors": [],
                        "objections": [],
                        "win_probability": None
                    }, indent=2),
                },
                "DEMO_STRATEGY": {
                    "demo_strategy.md": (
                        f"# Demo Strategy — {account_name}\n\n"
                        "*JARVIS generates this from your discovery notes + company intel.*\n"
                        "*Updates automatically after each discovery call.*\n\n"
                        "---\n\n## Narrative Hook\n*Generating from pain points...*\n\n"
                        "## Recommended Demo Flow (40 min)\n*Generating...*\n\n"
                        "## Use Cases to Show\n*Generating from requirements...*\n\n"
                        "## Competitive Landmines to Avoid\n*Generating...*\n"
                    ),
                    "demo_script.md": (
                        f"# Demo Script — {account_name}\n\n"
                        "*Line-by-line script with transitions and fallback responses.*\n"
                        "*Generated after discovery is complete.*\n\n"
                        "---\n\n*Waiting for discovery notes to generate script...*\n"
                    ),
                },
                "RISK_REPORT": {
                    "risk_report.md": (
                        f"# Risk Report — {account_name}\n\n"
                        "*Auto-filled weekly from activities, contacts, MEDDPICC, and web risk signals.*\n"
                        "*Format: [Initials] [Date] — append new entries, never overwrite.*\n\n"
                        "---\n\n"
                        f"## {datetime.now().strftime('%Y-%m-%d')} — Initial\n\n"
                        "**Owner:** SE\n\n"
                        "**Top 3 Technical Use Cases:**\n1. *Generating...*\n2.\n3.\n\n"
                        "**3 Challenges We Are Solving:**\n1. *Generating...*\n\n"
                        "**What Have We Done So Far:**\n"
                        "SE activities: (0) Discovery, (0) Demo, (0) POC, (0) RFP, (0) Competitive\n\n"
                        "**Stakeholders:**\nMet: *None yet*\nUpcoming: *Check calendar*\n\n"
                        "**Outstanding / Next Steps:**\n*From actions.md*\n\n"
                        "**Technical Gaps/Risks:**\n*MEDDPICC scores too low to assess yet*\n"
                    ),
                },
                "NEXT_STEPS": {
                    "next_steps.md": (
                        f"# Next Steps & Email Drafts — {account_name}\n\n"
                        "*JARVIS generates stage-appropriate email drafts after each interaction.*\n"
                        "*Updated when deal stage changes or meeting notes are saved.*\n\n"
                        "---\n\n## Current Stage: New Account\n\n"
                        "### Suggested Email: Initial Outreach\n*Generating based on company intel...*\n"
                    ),
                    "email_drafts.json": json.dumps({
                        "account": account_name,
                        "generated_at": datetime.now().isoformat(),
                        "current_stage": "new_account",
                        "drafts": []
                    }, indent=2),
                },
                "VALUE_ARCHITECTURE": {
                    "roi_model.md": (
                        f"# ROI Model — {account_name}\n\n"
                        "*JARVIS generates 3 ROI scenarios (conservative/realistic/optimistic)*\n"
                        "*using metrics extracted from your discovery calls and emails.*\n\n"
                        "---\n\n*Waiting for discovery data to build ROI model...*\n"
                    ),
                    "tco_analysis.md": (
                        f"# TCO Analysis — {account_name}\n\n"
                        "*Total Cost of Ownership vs current stack + competitors.*\n"
                        "*Generated from pricing intel + company size.*\n\n"
                        "---\n\n*Generating from available intel...*\n"
                    ),
                    "value_data.json": json.dumps({
                        "account": account_name,
                        "generated_at": datetime.now().isoformat(),
                        "status": "pending",
                        "metrics": {},
                        "roi_scenarios": {"conservative": {}, "realistic": {}, "optimistic": {}},
                        "tco": {}
                    }, indent=2),
                },
            }

            presales_created = []
            for section_name, files in presales_sections.items():
                section_path = account_dir / section_name
                if not section_path.exists():
                    section_path.mkdir(parents=True, exist_ok=True)
                    for fname, content in files.items():
                        (section_path / fname).write_text(content, encoding="utf-8")
                    presales_created.append(f"{section_name}/")
                    created_files.append(f"{section_name}/")

            if presales_created:
                self.logger.info("Presales sections created", account=account_name, sections=presales_created)

            # 2a. Create meddpicc.json
            meddpicc_file = account_dir / "meddpicc.json"
            if not meddpicc_file.exists():
                meddpicc_file.write_text(json.dumps({
                    "account": account_name,
                    "score": 0, "max_score": 8,
                    "last_updated": datetime.now().isoformat(),
                    "metrics": 0, "economic_buyer": 0, "decision_criteria": 0,
                    "decision_process": 0, "paper_process": 0, "implicate_pain": 0,
                    "champion": 0, "competition": 0,
                    "notes": {}
                }, indent=2))
                created_files.append("meddpicc.json")

            # 2b. Create deal_stage.json
            stage_file = account_dir / "deal_stage.json"
            if not stage_file.exists():
                stage_file.write_text(json.dumps({
                    "account": account_name,
                    "stage": "new_account",
                    "last_updated": datetime.now().isoformat(),
                    "history": []
                }, indent=2))
                created_files.append("deal_stage.json")

            # 2c. Create contacts.json
            contacts_file = account_dir / "contacts.json"
            if not contacts_file.exists():
                contacts_file.write_text(json.dumps({
                    "account": account_name,
                    "contacts": []
                }, indent=2))
                created_files.append("contacts.json")

            # 2d. Create actions.md
            actions_file = account_dir / "actions.md"
            if not actions_file.exists():
                actions_file.write_text(
                    f"# Action Items — {account_name}\n\n"
                    "*Auto-updated by JARVIS from meetings, emails, and conversations.*\n\n"
                )
                created_files.append("actions.md")

            # 2. Create account-specific notes.json if missing
            notes_file = account_dir / "notes.json"
            if not notes_file.exists():
                notes = {
                    "facts": [],
                    "preferences": [],
                    "knowledge_gaps": [],
                    "decisions": [],
                    "internal_notes": []
                }
                with open(notes_file, 'w') as f:
                    json.dump(notes, f, indent=2)
                created_files.append("notes.json")

            # 3. Create activities.jsonl (append-only log)
            activities_file = account_dir / "activities.jsonl"
            if not activities_file.exists():
                activities_file.touch()
                created_files.append("activities.jsonl")

            # 4. Create/update index.json
            index_file = account_dir / "index.json"
            if not index_file.exists():
                index = {
                    "account": account_name,
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "conversations": [],
                    "deals_count": 0,
                    "total_value": 0,
                    "smartness_files": ["deals/", "notes.json", "activities.jsonl", "summary.md"]
                }
                with open(index_file, 'w') as f:
                    json.dump(index, f, indent=2)
                created_files.append("index.json")
            else:
                # Update last_updated
                try:
                    with open(index_file, 'r') as f:
                        index = json.load(f)
                    index['last_updated'] = datetime.now().isoformat()
                    with open(index_file, 'w') as f:
                        json.dump(index, f, indent=2)
                except:
                    pass

            # 5. Create summary.md template (auto-generated summary)
            summary_file = account_dir / "summary.md"
            if not summary_file.exists():
                summary_content = f"""# Account Summary: {account_name}

*Auto-generated by JARVIS*

---
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Last Activity:** Never

**Deals:** 0 active

**Competitor?** Unknown

**Key Notes:** None yet

---

## Recent Conversations

*No conversations yet.*

## Active Deals

*No deals tracked.*

## Competitor Intelligence

*Not profiled as competitor.*

## Action Items

*None.*

---
*This file is automatically updated by JARVIS.*
"""
                with open(summary_file, 'w') as f:
                    f.write(summary_content)
                created_files.append("summary.md")

            # 6. Link to competitor profile if exists
            competitor_profile = self.memory_dir / "competitors" / f"{account_name.lower().replace(' ', '_')}.json"
            if competitor_profile.exists():
                # Create symlink or reference in index
                try:
                    index['competitor_linked'] = True
                    index['competitor_profile'] = str(competitor_profile)
                    with open(index_file, 'w') as f:
                        json.dump(index, f, indent=2)
                    self.logger.info("Linked account to competitor profile", account=account_name)
                except:
                    pass

            # Mark as initialized
            self.initialized_accounts.add(account_name)

            if created_files:
                self.logger.info("Initialized account with smartness files", account=account_name, files=created_files)

                # Broadcast event for other components
                init_event = Event("account.initialized", "account_initializer", {
                    "account_name": account_name,
                    "files_created": created_files,
                    "timestamp": datetime.now().isoformat()
                })
                self.event_bus.publish(init_event)

                # If presales sections were created, fire dedicated event for skill population
                if presales_created:
                    sections_event = Event("account.sections.created", "account_initializer", {
                        "account_name": account_name,
                        "sections": presales_created,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.event_bus.publish(sections_event)

        except Exception as e:
            self.logger.error("Failed to initialize account", account=account_name, error=str(e))

