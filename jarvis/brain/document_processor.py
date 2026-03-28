#!/usr/bin/env python3
"""
DocumentProcessor — processes files dropped into ACCOUNTS/{name}/DOCUMENTS/.

When you drop an RFP, contract, NDA, brief, or any document into an account's
DOCUMENTS/ folder, JARVIS reads it with NVIDIA, extracts intelligence,
and updates the account's context files automatically.

Supported formats: .pdf .docx .txt .md
"""

import asyncio
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager


SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".md", ".doc"}

DOCUMENT_TYPE_PROMPTS = {
    "rfp": (
        "This is an RFP (Request for Proposal). Extract: "
        "1) key requirements and evaluation criteria "
        "2) decision timeline and submission deadline "
        "3) budget range if mentioned "
        "4) competitors likely being evaluated "
        "5) top 5 win themes we should address "
        "6) MEDDPICC signals (decision process, paper process, metrics). "
        "Return as JSON."
    ),
    "contract": (
        "This is a contract or agreement. Extract: "
        "1) deal value and payment terms "
        "2) key obligations and milestones "
        "3) renewal and cancellation terms "
        "4) stakeholders and signatories. "
        "Return as JSON."
    ),
    "brief": (
        "This is a company or project brief. Extract: "
        "1) company background and size "
        "2) stated pain points or goals "
        "3) key people mentioned "
        "4) budget or investment signals "
        "5) competitive mentions. "
        "Return as JSON."
    ),
    "email": (
        "This is an email thread. Extract: "
        "1) all people mentioned with roles "
        "2) action items with owners "
        "3) deal status signals "
        "4) MEDDPICC signals "
        "5) next steps agreed. "
        "Return as JSON."
    ),
    "general": (
        "Extract from this document: "
        "1) company names and people mentioned "
        "2) key facts relevant to a sales deal "
        "3) any action items or commitments "
        "4) budget or timeline signals "
        "5) competitive mentions. "
        "Return as JSON."
    ),
}


class DocumentProcessor:
    """Processes files dropped into account DOCUMENTS/ or EMAILS/ folders."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("brain.documents")
        self._llm_client = None

    async def start(self):
        self.event_bus.subscribe("document.added", self._on_document_added)
        self.event_bus.subscribe("email.added", self._on_email_added)
        self.logger.info("DocumentProcessor started")

    async def stop(self):
        self.logger.info("DocumentProcessor stopped")

    async def _on_document_added(self, event: Event):
        await self.process_document(
            file_path=Path(event.data["path"]),
            account_name=event.data["account"],
            folder_type="DOCUMENTS",
        )

    async def _on_email_added(self, event: Event):
        await self.process_document(
            file_path=Path(event.data["path"]),
            account_name=event.data["account"],
            folder_type="EMAILS",
        )

    async def process_document(
        self, file_path: Path, account_name: str, folder_type: str = "DOCUMENTS"
    ):
        """Full pipeline: read → classify → NLP extract → update account files."""
        if not file_path.exists():
            return
        if file_path.suffix.lower() not in SUPPORTED_EXTS:
            self.logger.debug("Unsupported file type, skipping", path=str(file_path))
            return

        self.logger.info("Processing document", file=file_path.name, account=account_name)

        try:
            # Step 1: Extract text
            text = self._extract_text(file_path)
            if not text or len(text.strip()) < 50:
                self.logger.warning("Document too short or empty", file=file_path.name)
                return

            # Step 2: Classify document type
            doc_type = self._classify_document(file_path.name, text)

            # Step 3: NLP extraction via NVIDIA
            extracted = await self._extract_intelligence(text, doc_type, account_name)

            # Step 4: Write intelligence to account folder
            account_dir = Path(self.config.workspace_root) / "ACCOUNTS" / account_name
            await self._update_account(account_dir, account_name, file_path, doc_type, extracted)

            # Step 5: Trigger downstream skills based on doc type
            self._trigger_skills(account_name, doc_type, extracted)

            self.logger.info("Document processed", file=file_path.name,
                             account=account_name, doc_type=doc_type)

        except Exception as e:
            self.logger.error("Document processing failed",
                              file=file_path.name, error=str(e))

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def _extract_text(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()

        if ext in (".txt", ".md"):
            return file_path.read_text(encoding="utf-8", errors="ignore")

        if ext == ".docx":
            return self._extract_docx(file_path)

        if ext == ".pdf":
            return self._extract_pdf(file_path)

        return ""

    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from .docx without external deps."""
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                with z.open("word/document.xml") as f:
                    tree = ET.parse(f)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            texts = [node.text for node in tree.findall(".//w:t", ns) if node.text]
            return " ".join(texts)
        except Exception as e:
            self.logger.warning("DOCX extraction failed", error=str(e))
            return ""

    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF — tries pypdf, falls back to pdfminer."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except ImportError:
            pass
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            return pdfminer_extract(str(file_path))
        except ImportError:
            pass
        self.logger.warning("No PDF library available — install pypdf or pdfminer.six")
        return ""

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify_document(self, filename: str, text: str) -> str:
        fname = filename.lower()
        text_lower = text[:500].lower()

        if any(k in fname for k in ("rfp", "request_for_proposal", "rfi", "rfq")):
            return "rfp"
        if any(k in fname for k in ("contract", "agreement", "nda", "msa", "sow")):
            return "contract"
        if any(k in fname for k in ("brief", "overview", "background")):
            return "brief"
        if any(k in fname for k in ("email", "thread", "mail")):
            return "email"
        if "request for proposal" in text_lower or "rfp" in text_lower:
            return "rfp"
        if "agreement" in text_lower and "parties" in text_lower:
            return "contract"
        return "general"

    # ------------------------------------------------------------------
    # NLP extraction
    # ------------------------------------------------------------------

    async def _extract_intelligence(
        self, text: str, doc_type: str, account_name: str
    ) -> Dict:
        """Use NVIDIA LLM to extract structured intelligence from document text."""
        if not self._llm_client:
            self._llm_client = self._build_llm_client()

        if not self._llm_client:
            return {}

        prompt = (
            f"Account: {account_name}\n"
            f"Document type: {doc_type}\n\n"
            f"{DOCUMENT_TYPE_PROMPTS.get(doc_type, DOCUMENT_TYPE_PROMPTS['general'])}\n\n"
            f"Document text (first 4000 chars):\n{text[:4000]}"
        )

        try:
            response = await self._llm_client.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text",
                source="background",
            )
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            self.logger.warning("LLM extraction failed", error=str(e))

        return {}

    def _build_llm_client(self):
        try:
            from jarvis.llm.llm_client import LLMClient
            return LLMClient(self.config)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Account updates
    # ------------------------------------------------------------------

    async def _update_account(
        self, account_dir: Path, account_name: str,
        file_path: Path, doc_type: str, extracted: Dict
    ):
        date_str = datetime.now().strftime("%Y-%m-%d")
        intel_dir = account_dir / "INTEL"
        intel_dir.mkdir(exist_ok=True)

        # Write extracted intelligence as a markdown file
        out_name = f"{date_str}_{file_path.stem}_{doc_type}_intel.md"
        out_file = intel_dir / out_name
        out_file.write_text(
            f"# Document Intelligence: {file_path.name}\n"
            f"**Account:** {account_name}  \n"
            f"**Type:** {doc_type}  \n"
            f"**Processed:** {date_str}  \n\n"
            f"```json\n{json.dumps(extracted, indent=2)}\n```\n",
            encoding="utf-8"
        )

        # Update actions.md with extracted action items
        action_items = extracted.get("action_items", [])
        if action_items:
            actions_file = account_dir / "actions.md"
            with open(actions_file, "a", encoding="utf-8") as f:
                for item in action_items:
                    f.write(f"- [ ] [{date_str}] {item}\n")

        # Update contacts.json
        people = extracted.get("stakeholders", extracted.get("people", []))
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
                            "source": file_path.name,
                            "first_seen": date_str,
                        })
                        existing_names.add(name.lower())
                contacts_file.write_text(json.dumps(data, indent=2))
            except Exception as e:
                self.logger.warning("Contacts update failed", error=str(e))

        # Log activity
        activities_file = account_dir / "activities.jsonl"
        with open(activities_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "source": "document_processor",
                "doc_type": doc_type,
                "file": file_path.name,
                "intel_file": out_name,
            }) + "\n")

    # ------------------------------------------------------------------
    # Downstream skill triggers
    # ------------------------------------------------------------------

    def _trigger_skills(self, account_name: str, doc_type: str, extracted: Dict):
        """Fire skill-trigger events based on what was found in the document."""
        if doc_type == "rfp":
            self.event_bus.publish(Event(
                type="skill.trigger.request",
                source="brain.documents",
                data={"skill": "proposal_generator", "account": account_name,
                      "reason": "RFP detected in DOCUMENTS/"}
            ))
        if extracted.get("competitors"):
            self.event_bus.publish(Event(
                type="skill.trigger.request",
                source="brain.documents",
                data={"skill": "battlecards", "account": account_name,
                      "competitors": extracted["competitors"],
                      "reason": "Competitors mentioned in document"}
            ))
        self.event_bus.publish(Event(
            type="document.processed",
            source="brain.documents",
            data={"account": account_name, "doc_type": doc_type}
        ))
