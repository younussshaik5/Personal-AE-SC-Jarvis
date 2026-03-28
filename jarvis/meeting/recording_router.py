#!/usr/bin/env python3
"""
RecordingRouter — Identifies which account a recording belongs to.

Strategy (in order of cost):
  1. Filename fuzzy match against existing ACCOUNTS/ folders
  2. Transcribe first 3 minutes → extract company/people names → fuzzy match
  3. Full transcript NLP entity extraction → majority vote
  4. Create new account if no match found, notify for confirmation
"""

import json
import re
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher

from jarvis.utils.logger import JARVISLogger


class RecordingRouter:

    CONFIDENCE_AUTO_ROUTE = 0.75   # above this → route silently
    CONFIDENCE_NOTIFY = 0.50       # above this → route + notify for confirmation
    # below 0.50 → create new account

    def __init__(self, accounts_dir: Path, nvidia_api_key: str, nvidia_base_url: str):
        self.accounts_dir = accounts_dir
        self.nvidia_api_key = nvidia_api_key
        self.nvidia_base_url = nvidia_base_url
        self.logger = JARVISLogger("meeting.router")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def identify_account(
        self,
        recording_path: Path,
        transcriber=None,
        llm_client=None,
    ) -> dict:
        """
        Given a recording file, return:
        {
            "account": "Jio Platforms",
            "confidence": 0.92,
            "method": "filename|transcript_quick|transcript_full|new",
            "created_new": False,
            "notify": False,
        }
        """
        accounts = self._list_accounts()

        # Layer 1 — filename
        result = self._match_filename(recording_path.stem, accounts)
        if result and result["confidence"] >= self.CONFIDENCE_AUTO_ROUTE:
            self.logger.info("Routed via filename", account=result["account"],
                             confidence=result["confidence"])
            return {**result, "method": "filename", "created_new": False, "notify": False}

        # Layer 2 — quick transcript (first 3 min)
        if transcriber:
            quick_text = await self._quick_transcript(recording_path, transcriber)
            if quick_text:
                result2 = self._match_from_text(quick_text, accounts)
                if result2 and result2["confidence"] >= self.CONFIDENCE_AUTO_ROUTE:
                    self.logger.info("Routed via quick transcript",
                                     account=result2["account"],
                                     confidence=result2["confidence"])
                    return {**result2, "method": "transcript_quick",
                            "created_new": False, "notify": False}

        # Layer 3 — full transcript NLP
        if transcriber and llm_client:
            full_text = await self._full_transcript(recording_path, transcriber)
            if full_text:
                detected = await self._llm_extract_company(full_text, llm_client)
                if detected:
                    result3 = self._match_from_text(detected, accounts)
                    if result3 and result3["confidence"] >= self.CONFIDENCE_NOTIFY:
                        notify = result3["confidence"] < self.CONFIDENCE_AUTO_ROUTE
                        self.logger.info("Routed via LLM extraction",
                                         account=result3["account"],
                                         confidence=result3["confidence"],
                                         notify=notify)
                        return {**result3, "method": "transcript_full",
                                "created_new": False, "notify": notify}

                    # No match in existing accounts → create new
                    if detected and detected.strip():
                        account_name = self._clean_company_name(detected)
                        self._create_account_folder(account_name)
                        self.logger.info("Created new account from recording",
                                         account=account_name)
                        return {
                            "account": account_name,
                            "confidence": 0.70,
                            "method": "new",
                            "created_new": True,
                            "notify": True,
                        }

        # Layer 4 — fallback: use filename stem as account name
        fallback_name = self._clean_company_name(recording_path.stem)
        self._create_account_folder(fallback_name)
        self.logger.warning("Using filename as fallback account name",
                            account=fallback_name)
        return {
            "account": fallback_name,
            "confidence": 0.30,
            "method": "fallback",
            "created_new": True,
            "notify": True,
        }

    # ------------------------------------------------------------------
    # Layer 1: Filename matching
    # ------------------------------------------------------------------

    def _match_filename(self, filename_stem: str, accounts: list[str]) -> Optional[dict]:
        """
        Match recording filename against account names.
        E.g. "jio_platforms_discovery_2026-03-28" → "Jio Platforms"
        """
        # Strip dates, timestamps, common suffixes
        clean = re.sub(
            r'[\-_]?(\d{4}[\-_]\d{2}[\-_]\d{2}|\d{8}|'
            r'discovery|demo|call|meeting|poc|proposal|kickoff|followup|sync)',
            '', filename_stem, flags=re.IGNORECASE
        )
        clean = re.sub(r'[\-_]+', ' ', clean).strip()

        if not clean:
            return None

        return self._best_fuzzy_match(clean, accounts)

    # ------------------------------------------------------------------
    # Layer 2: Quick transcript (first 3 minutes)
    # ------------------------------------------------------------------

    async def _quick_transcript(self, recording_path: Path, transcriber) -> Optional[str]:
        """Extract and transcribe just the first 3 minutes of the recording."""
        try:
            import asyncio
            import tempfile

            clip_path = Path(tempfile.mktemp(suffix=".wav"))
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", str(recording_path),
                "-t", "180",           # first 3 minutes
                "-vn",                 # no video
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(clip_path),
                "-y",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()

            if clip_path.exists():
                result = await transcriber.transcribe(str(clip_path))
                clip_path.unlink(missing_ok=True)
                return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as e:
            self.logger.warning("Quick transcript failed", error=str(e))
        return None

    # ------------------------------------------------------------------
    # Layer 3: Full transcript + LLM entity extraction
    # ------------------------------------------------------------------

    async def _full_transcript(self, recording_path: Path, transcriber) -> Optional[str]:
        """Full transcription of the recording."""
        try:
            result = await transcriber.transcribe(str(recording_path))
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as e:
            self.logger.warning("Full transcript failed", error=str(e))
        return None

    async def _llm_extract_company(self, transcript_text: str, llm_client) -> Optional[str]:
        """Use NVIDIA LLM to extract the primary customer company from a transcript."""
        prompt = f"""You are analyzing a sales call transcript. Identify the PRIMARY CUSTOMER company being discussed (not the seller's company).

Return ONLY the company name, nothing else. If unclear, return your best guess.

Transcript (first 2000 chars):
{transcript_text[:2000]}

Company name:"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await llm_client.generate_with_routing(
                messages, task_type="text", source="background"
            )
            company = response.strip().strip('"\'').strip()
            return company if len(company) < 100 else None
        except Exception as e:
            self.logger.warning("LLM entity extraction failed", error=str(e))
        return None

    # ------------------------------------------------------------------
    # Fuzzy matching helpers
    # ------------------------------------------------------------------

    def _match_from_text(self, text: str, accounts: list[str]) -> Optional[dict]:
        """Find the best account match from a block of text or extracted name."""
        # Try direct fuzzy match first
        direct = self._best_fuzzy_match(text, accounts)
        if direct and direct["confidence"] >= self.CONFIDENCE_NOTIFY:
            return direct

        # Try each word/phrase in the text against accounts
        words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
        best = None
        for word in words:
            match = self._best_fuzzy_match(word, accounts)
            if match and (not best or match["confidence"] > best["confidence"]):
                best = match

        return best

    def _best_fuzzy_match(self, query: str, accounts: list[str]) -> Optional[dict]:
        """Find the best fuzzy match for query against the list of account names."""
        if not accounts or not query:
            return None

        query_lower = query.lower().strip()
        best_score = 0.0
        best_account = None

        for account in accounts:
            account_lower = account.lower()

            # Exact substring match → high confidence
            if query_lower in account_lower or account_lower in query_lower:
                score = 0.90
            else:
                # Sequence matcher ratio
                score = SequenceMatcher(None, query_lower, account_lower).ratio()

                # Token overlap boost
                q_tokens = set(query_lower.split())
                a_tokens = set(account_lower.split())
                overlap = q_tokens & a_tokens
                if overlap:
                    overlap_ratio = len(overlap) / max(len(q_tokens), len(a_tokens))
                    score = max(score, overlap_ratio * 0.85)

            if score > best_score:
                best_score = score
                best_account = account

        if best_account and best_score >= 0.40:
            return {"account": best_account, "confidence": round(best_score, 3)}
        return None

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _list_accounts(self) -> list[str]:
        """List all existing account folder names."""
        if not self.accounts_dir.exists():
            return []
        return [
            d.name for d in self.accounts_dir.iterdir()
            if d.is_dir() and not d.name.startswith('_') and not d.name.startswith('.')
        ]

    def _clean_company_name(self, raw: str) -> str:
        """Turn a raw string into a clean account folder name."""
        # Remove dates, timestamps
        clean = re.sub(r'\d{4}[-_]\d{2}[-_]\d{2}', '', raw)
        clean = re.sub(r'[\-_]+', ' ', clean)
        # Title case
        clean = ' '.join(w.capitalize() for w in clean.split())
        # Remove common noise words at the end
        for noise in ['Call', 'Meeting', 'Demo', 'Poc', 'Discovery', 'Recording']:
            clean = re.sub(rf'\b{noise}\b', '', clean, flags=re.IGNORECASE)
        return clean.strip() or raw.strip()

    def _create_account_folder(self, account_name: str):
        """Create a new account folder with starter files."""
        folder = self.accounts_dir / account_name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "meetings").mkdir(exist_ok=True)

        # Starter files
        if not (folder / "meddpicc.json").exists():
            (folder / "meddpicc.json").write_text(json.dumps({
                "account": account_name,
                "score": 0,
                "max_score": 8,
                "last_updated": "",
                "metrics": 0, "economic_buyer": 0, "decision_criteria": 0,
                "decision_process": 0, "paper_process": 0, "implicate_pain": 0,
                "champion": 0, "competition": 0,
                "notes": {}
            }, indent=2))

        if not (folder / "deal_stage.json").exists():
            (folder / "deal_stage.json").write_text(json.dumps({
                "account": account_name,
                "stage": "new_account",
                "last_updated": "",
                "history": []
            }, indent=2))

        if not (folder / "contacts.json").exists():
            (folder / "contacts.json").write_text(json.dumps({
                "account": account_name,
                "contacts": []
            }, indent=2))

        if not (folder / "README.md").exists():
            (folder / "README.md").write_text(
                f"# {account_name}\n\n"
                "## Quick Facts\n- Industry: \n- Size: \n- HQ: \n\n"
                "## Pain Points\n\n## Key Contacts\n\n## Deal Status\n"
            )
