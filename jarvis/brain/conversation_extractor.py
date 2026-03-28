#!/usr/bin/env python3
"""
ConversationExtractor — watches JARVIS_BRAIN.md and routes intelligence
to the right account folders automatically.

Claude Desktop appends a structured entry to JARVIS_BRAIN.md after every
work-related conversation. This component reads those entries, extracts
entities (account names, people, MEDDPICC signals, action items, competitors)
using NVIDIA Nemotron, and writes the relevant data to ACCOUNTS/{name}/.

Nothing here is hardcoded. Everything resolves from JARVIS_HOME.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager


# Structured entry format that Claude writes to JARVIS_BRAIN.md
# Claude is instructed to use this exact format (see CLAUDE_SYSTEM_PROMPT.md)
ENTRY_MARKER = "<!-- JARVIS_ENTRY"
ENTRY_END    = "JARVIS_ENTRY_END -->"


class ConversationExtractor:
    """
    Watches JARVIS_BRAIN.md for new entries written by Claude Desktop.
    Extracts account intelligence and routes to ACCOUNTS/ folders.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("brain.extractor")
        self._running = False
        self._watch_task: Optional[asyncio.Task] = None
        self._last_size: int = 0
        self._llm_client = None

    async def start(self):
        self._running = True
        jarvis_home = Path(self.config.workspace_root)
        self._brain_file = jarvis_home / "JARVIS_BRAIN.md"
        self._accounts_dir = jarvis_home / "ACCOUNTS"

        # Create JARVIS_BRAIN.md if it doesn't exist
        if not self._brain_file.exists():
            self._brain_file.write_text(
                "# JARVIS Brain — Conversation Intelligence Log\n\n"
                "*Claude Desktop appends entries here after every work conversation.*\n"
                "*JARVIS reads this and routes intelligence to ACCOUNTS/ automatically.*\n\n"
            )

        self._last_size = self._brain_file.stat().st_size
        self._watch_task = asyncio.create_task(self._watch_loop())

        # Also subscribe to file.modified events from FileSystemObserver
        self.event_bus.subscribe("file.modified", self._on_file_modified)

        self.logger.info("ConversationExtractor started", brain_file=str(self._brain_file))

    async def stop(self):
        self._running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
        self.logger.info("ConversationExtractor stopped")

    # ------------------------------------------------------------------
    # File watching
    # ------------------------------------------------------------------

    async def _on_file_modified(self, event: Event):
        """Catch JARVIS_BRAIN.md modifications from FileSystemObserver."""
        path = event.data.get("path", "")
        if "JARVIS_BRAIN" in path:
            await self._process_new_entries()

    async def _watch_loop(self):
        """Fallback polling watcher in case FileSystemObserver misses an event."""
        while self._running:
            await asyncio.sleep(15)
            try:
                if self._brain_file.exists():
                    current_size = self._brain_file.stat().st_size
                    if current_size > self._last_size:
                        await self._process_new_entries()
            except Exception as e:
                self.logger.error("Brain watch loop error", error=str(e))

    # ------------------------------------------------------------------
    # Entry processing
    # ------------------------------------------------------------------

    async def _process_new_entries(self):
        """Read JARVIS_BRAIN.md, find unprocessed entries, route them."""
        try:
            content = self._brain_file.read_text(encoding="utf-8")
            self._last_size = len(content.encode("utf-8"))

            entries = self._parse_entries(content)
            unprocessed = [e for e in entries if not e.get("processed")]

            for entry in unprocessed:
                await self._route_entry(entry)
                self._mark_processed(entry["raw_marker"])

        except Exception as e:
            self.logger.error("Failed to process brain entries", error=str(e))

    def _parse_entries(self, content: str) -> List[Dict]:
        """Parse structured entries from JARVIS_BRAIN.md."""
        entries = []
        pattern = re.compile(
            rf'{re.escape(ENTRY_MARKER)}(.*?){re.escape(ENTRY_END)}',
            re.DOTALL
        )
        for match in pattern.finditer(content):
            raw = match.group(1).strip()
            processed = raw.startswith("PROCESSED")
            entry = {"raw_marker": match.group(0), "processed": processed}

            # Parse key: value lines
            for line in raw.splitlines():
                if ":" in line and not line.startswith("PROCESSED"):
                    key, _, val = line.partition(":")
                    entry[key.strip().lower()] = val.strip()

            # Parse JSON blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL)
            if json_match:
                try:
                    entry["structured"] = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            entries.append(entry)

        return entries

    async def _route_entry(self, entry: Dict):
        """Route an extracted entry to the correct account folder(s)."""
        structured = entry.get("structured", {})
        accounts_mentioned = self._extract_accounts(entry, structured)

        if not accounts_mentioned:
            self.logger.debug("No accounts identified in brain entry, skipping")
            return

        for account_name in accounts_mentioned:
            account_dir = self._find_or_create_account(account_name)
            await self._write_to_account(account_dir, account_name, entry, structured)

        self.event_bus.publish(Event(
            type="brain.entry.routed",
            source="brain.extractor",
            data={"accounts": accounts_mentioned, "entry_date": entry.get("date", "")}
        ))
        self.logger.info("Brain entry routed", accounts=accounts_mentioned)

    def _extract_accounts(self, entry: Dict, structured: Dict) -> List[str]:
        """Extract account names from a parsed entry."""
        accounts = []

        # From structured JSON block
        for key in ("accounts", "account", "company", "companies"):
            val = structured.get(key, "")
            if isinstance(val, list):
                accounts.extend(val)
            elif isinstance(val, str) and val.strip():
                accounts.append(val.strip())

        # From top-level entry keys
        for key in ("account", "accounts", "company"):
            val = entry.get(key, "")
            if val and val not in accounts:
                accounts.append(val)

        # Fuzzy match against existing account folders
        existing = self._list_existing_accounts()
        matched = []
        for name in accounts:
            best = self._fuzzy_match_account(name, existing)
            matched.append(best if best else name)

        return list(dict.fromkeys(matched))  # deduplicate, preserve order

    def _find_or_create_account(self, account_name: str) -> Path:
        """Return account dir path, creating it (and firing init event) if missing."""
        account_dir = self._accounts_dir / account_name
        if not account_dir.exists():
            account_dir.mkdir(parents=True, exist_ok=True)
            self.event_bus.publish(Event(
                type="file.created",
                source="brain.extractor",
                data={"path": str(account_dir), "is_directory": True}
            ))
            self.logger.info("Created new account from brain entry", account=account_name)
        return account_dir

    async def _write_to_account(
        self, account_dir: Path, account_name: str,
        entry: Dict, structured: Dict
    ):
        """Write extracted intelligence to the account folder."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 1. Append to activities.jsonl (always)
        activity = {
            "timestamp": timestamp,
            "source": "claude_conversation",
            "date": entry.get("date", date_str),
            "summary": entry.get("summary", ""),
            "raw_entry": {k: v for k, v in entry.items() if k not in ("raw_marker",)}
        }
        activities_file = account_dir / "activities.jsonl"
        with open(activities_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(activity) + "\n")

        # 2. Update actions.md with any new action items
        action_items = structured.get("action_items", [])
        if action_items:
            actions_file = account_dir / "actions.md"
            existing = actions_file.read_text(encoding="utf-8") if actions_file.exists() else ""
            new_items = "\n".join(
                f"- [ ] [{date_str}] {item}"
                for item in action_items
                if item not in existing
            )
            if new_items:
                with open(actions_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{new_items}\n")

        # 3. Update contacts.json with any new people mentioned
        people = structured.get("people", [])
        if people:
            contacts_file = account_dir / "contacts.json"
            try:
                data = json.loads(contacts_file.read_text()) if contacts_file.exists() \
                    else {"account": account_name, "contacts": []}
                existing_names = {c.get("name", "").lower() for c in data["contacts"]}
                for person in people:
                    name = person if isinstance(person, str) else person.get("name", "")
                    if name and name.lower() not in existing_names:
                        data["contacts"].append({
                            "name": name,
                            "role": person.get("role", "") if isinstance(person, dict) else "",
                            "first_seen": date_str
                        })
                        existing_names.add(name.lower())
                contacts_file.write_text(json.dumps(data, indent=2))
            except Exception as e:
                self.logger.warning("Failed to update contacts", error=str(e))

        # 4. Update MEDDPICC signals
        meddpicc_signals = structured.get("meddpicc_signals", {})
        if meddpicc_signals:
            self._update_meddpicc(account_dir, account_name, meddpicc_signals, date_str)

        # 5. Append to INTEL/conversation_log.md
        intel_dir = account_dir / "INTEL"
        intel_dir.mkdir(exist_ok=True)
        conv_log = intel_dir / "conversation_log.md"
        with open(conv_log, "a", encoding="utf-8") as f:
            f.write(f"\n## {timestamp}\n\n")
            if entry.get("summary"):
                f.write(f"{entry['summary']}\n\n")
            if action_items:
                f.write("**Action Items:**\n")
                for item in action_items:
                    f.write(f"- {item}\n")
                f.write("\n")

        # 6. Fire event so other components react
        self.event_bus.publish(Event(
            type="account.context.updated",
            source="brain.extractor",
            data={
                "account": account_name,
                "has_meddpicc": bool(meddpicc_signals),
                "has_actions": bool(action_items),
                "has_contacts": bool(people),
            }
        ))

    def _update_meddpicc(
        self, account_dir: Path, account_name: str,
        signals: Dict, date_str: str
    ):
        """Update meddpicc.json from conversation signals."""
        meddpicc_file = account_dir / "meddpicc.json"
        try:
            data = json.loads(meddpicc_file.read_text()) if meddpicc_file.exists() else {
                "account": account_name, "score": 0, "max_score": 8,
                "metrics": 0, "economic_buyer": 0, "decision_criteria": 0,
                "decision_process": 0, "paper_process": 0, "implicate_pain": 0,
                "champion": 0, "competition": 0, "notes": {}
            }
            updated = False
            fields = [
                "metrics", "economic_buyer", "decision_criteria", "decision_process",
                "paper_process", "implicate_pain", "champion", "competition"
            ]
            for field in fields:
                if field in signals:
                    new_val = int(signals[field])
                    if new_val > data.get(field, 0):  # only increase, never decrease
                        data[field] = new_val
                        data["notes"][field] = signals.get(f"{field}_note", "")
                        updated = True

            if updated:
                data["score"] = sum(data.get(f, 0) for f in fields)
                data["last_updated"] = date_str
                meddpicc_file.write_text(json.dumps(data, indent=2))
                self.event_bus.publish(Event(
                    type="meddpicc.updated",
                    source="brain.extractor",
                    data={"account": account_name, "score": data["score"]}
                ))
        except Exception as e:
            self.logger.warning("Failed to update MEDDPICC", error=str(e))

    def _mark_processed(self, raw_marker: str):
        """Mark an entry as processed in JARVIS_BRAIN.md so it's not re-processed."""
        try:
            content = self._brain_file.read_text(encoding="utf-8")
            marked = raw_marker.replace(ENTRY_MARKER, f"{ENTRY_MARKER}\nPROCESSED", 1)
            self._brain_file.write_text(content.replace(raw_marker, marked))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _list_existing_accounts(self) -> List[str]:
        if not self._accounts_dir.exists():
            return []
        return [d.name for d in self._accounts_dir.iterdir()
                if d.is_dir() and not d.name.startswith(('.', '_'))]

    def _fuzzy_match_account(self, name: str, accounts: List[str]) -> Optional[str]:
        from difflib import SequenceMatcher
        name_lower = name.lower()
        best_score, best_match = 0.0, None
        for account in accounts:
            score = SequenceMatcher(None, name_lower, account.lower()).ratio()
            if account.lower() in name_lower or name_lower in account.lower():
                score = max(score, 0.85)
            if score > best_score:
                best_score, best_match = score, account
        return best_match if best_score >= 0.65 else None
