"""Documentation Skill - Capture, organize, and link documentation requests.

This skill activates when you ask for documents, presentations, or reference materials.
It will:
1. Probe to clarify what type of doc/PPT you need
2. Store doc requests and outputs in organized structure
3. Create cross-references (which deal needs which doc, which competitor analysis needs a PPT)
4. Build a searchable doc library over time
5. Link docs to deals, competitors, and patterns
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class DocumentationSkill:
    """Skill for documentation gathering and organization."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.documentation")
        self.workspace_root = config_manager.config.workspace_root
        self.memory_dir = Path(self.workspace_root) / "MEMORY"
        self.docs_dir = self.memory_dir / "documents"
        self.requests_dir = self.docs_dir / "requests"
        self.generated_dir = self.docs_dir / "generated"

    async def start(self):
        """Start the skill."""
        self.logger.info("Starting documentation skill")
        self.event_bus.subscribe("telegram.message", self._detect_document_intent)
        self.event_bus.subscribe("telegram.response", self._capture_document_response)
        self.logger.info("Skill started")

    async def stop(self):
        """Stop the skill."""
        self.logger.info("Skill stopped")

    async def _detect_document_intent(self, event: Event):
        """Detect if user is requesting documentation or PPTs."""
        message = event.data.get("message", "").lower()
        user_id = event.data.get("user_id")

        # Keywords indicating document/PPT request
        doc_keywords = ['doc', 'document', 'ppt', 'presentation', 'deck', 'proposal',
                        'one pager', 'one-pager', 'brief', 'summary', 'overview',
                        'handout', 'materials', 'collateral', 'send me', 'share',
                        'can you provide', 'give me', 'prepare', 'create doc',
                        'sales doc', 'technical doc', 'proposal', 'quote']

        if any(keyword in message for keyword in doc_keywords):
            await self._log_document_request(user_id, message, event.data)

    async def _log_document_request(self, user_id: int, message: str, context: Dict):
        """Log a document request for tracking and analysis."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            request_id = f"doc_{datetime.now().strftime('%H%M%S')}_{user_id}"

            # Infer document type from message
            doc_type = self._infer_document_type(message)

            request_data = {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "original_message": message,
                "inferred_type": doc_type,
                "context": context,
                "status": "pending",  # pending, fulfilled, rejected
                "fulfilled_at": None,
                "response_summary": None,
                "linked_entities": []  # Will be filled later (deals, competitors, etc.)
            }

            # Save request
            request_file = self.requests_dir / today / f"{request_id}.json"
            request_file.parent.mkdir(parents=True, exist_ok=True)
            with open(request_file, 'w') as f:
                json.dump(request_data, f, indent=2)

            # Update daily index
            await self._update_daily_index(today, request_id, request_data)

            self.logger.info("Logged document request", request_id=request_id, type=doc_type)
        except Exception as e:
            self.logger.error("Failed to log doc request", error=str(e))

    def _infer_document_type(self, message: str) -> str:
        """Infer the type of document being requested."""
        msg = message.lower()
        if 'ppt' in msg or 'presentation' in msg or 'deck' in msg:
            return 'presentation'
        elif 'proposal' in msg or 'quote' in msg:
            return 'proposal'
        elif 'one pager' in msg or 'one-pager' in msg or 'brief' in msg:
            return 'one_pager'
        elif 'summary' in msg or 'overview' in msg:
            return 'summary'
        elif 'technical' in msg or 'spec' in msg:
            return 'technical_document'
        elif 'sales' in msg or 'collateral' in msg:
            return 'sales_collateral'
        else:
            return 'general'

    async def _capture_document_response(self, event: Event):
        """Capture when AI provides document-related response."""
        response = event.data.get("response", "")
        original_msg = event.data.get("original_message", "")

        # Check if response indicates document was provided or created
        if any(word in response.lower() for word in ['document', 'proposal', 'presentation', 'ppt', 'deck', 'attached', 'generated']):
            await self._fulfill_document_request(original_msg, response, event.data)

    async def _fulfill_document_request(self, query: str, response: str, context: Dict):
        """Mark a document request as fulfilled and store the output."""
        try:
            # Find the most recent pending request for this user
            user_id = context.get("user_id")
            if not user_id:
                return

            # Search recent request files
            today = datetime.now().strftime("%Y-%m-%d")
            requests_today_dir = self.requests_dir / today
            if not requests_today_dir.exists():
                return

            request_files = sorted(requests_today_dir.glob("*.json"), reverse=True)
            for req_file in request_files:
                with open(req_file) as f:
                    req_data = json.load(f)
                if req_data["user_id"] == user_id and req_data["status"] == "pending":
                    # Mark as fulfilled
                    req_data["status"] = "fulfilled"
                    req_data["fulfilled_at"] = datetime.now().isoformat()
                    req_data["response_summary"] = response[:500]
                    req_data["linked_entities"] = await self._extract_linked_entities(query, response)

                    # Save updated request
                    with open(req_file, 'w') as f:
                        json.dump(req_data, f, indent=2)

                    # Store generated document in generated folder
                    await self._store_generated_document(req_data, response)

                    self.logger.info("Fulfilled document request", request_id=req_data["request_id"])

                    # Meta-learning: publish skill.triggered event
                    try:
                        self.event_bus.publish(Event("skill.triggered", "documentation", {
                            "action": "fulfilled_request",
                            "request_id": req_data["request_id"],
                            "doc_type": req_data.get("inferred_type"),
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat()
                        }))
                    except:
                        pass

                    break
        except Exception as e:
            self.logger.error("Failed to fulfill doc request", error=str(e))

    async def _extract_linked_entities(self, query: str, response: str) -> List[Dict]:
        """Extract linked entities (deals, competitors, etc.) from conversation."""
        entities = []
        text = f"{query}\n{response}".lower()

        # Check for deals
        deals_file = Path('jarvis/data/personas/deals.json')
        if deals_file.exists():
            with open(deals_file) as f:
                deals_data = json.load(f)
                for deal in deals_data.get('deals', []):
                    if deal['title'].lower() in text or deal['client'].lower() in text:
                        entities.append({
                            "type": "deal",
                            "id": deal.get('id', deal['title']),
                            "title": deal['title'],
                            "client": deal['client']
                        })

        # Check for competitors
        competitors_file = self.memory_dir / "competitor_mentions.json"
        if competitors_file.exists():
            with open(competitors_file) as f:
                comp_data = json.load(f)
                for mention in comp_data.get('mentions', []):
                    comp = mention.get('competitor', '')
                    if comp and comp.lower() in text:
                        entities.append({
                            "type": "competitor",
                            "name": comp
                        })

        # Deduplicate
        seen = set()
        unique = []
        for e in entities:
            key = (e['type'], e.get('id', e.get('name', '')))
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique

    async def _store_generated_document(self, request_data: Dict, content: str):
        """Store the generated document content."""
        doc_id = request_data["request_id"]
        doc_type = request_data["inferred_type"]
        today = datetime.now().strftime("%Y-%m-%d")

        doc_file = self.generated_dir / today / f"{doc_id}.md"
        doc_file.parent.mkdir(parents=True, exist_ok=True)

        # Wrap content in markdown with metadata
        full_content = f"""---
type: {doc_type}
request_id: {doc_id}
timestamp: {request_data['timestamp']}
user_id: {request_data['user_id']}
original_request: {request_data['original_message']}
linked_entities: {json.dumps(request_data.get('linked_entities', []), indent=2)}
---

{content}
"""

        with open(doc_file, 'w') as f:
            f.write(full_content)

        # Also store as plain text version for searching
        txt_file = doc_file.with_suffix('.txt')
        with open(txt_file, 'w') as f:
            f.write(content)

    async def _update_daily_index(self, date: str, request_id: str, request_data: Dict):
        """Update the daily index of documentation requests."""
        index_file = self.docs_dir / "index.json"
        if index_file.exists():
            with open(index_file) as f:
                index = json.load(f)
        else:
            index = {"dates": {}}

        if date not in index["dates"]:
            index["dates"][date] = []

        index["dates"][date].append({
            "request_id": request_id,
            "timestamp": request_data["timestamp"],
            "user_id": request_data["user_id"],
            "type": request_data["inferred_type"],
            "status": request_data["status"]
        })

        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)

    async def get_document_history(self, user_id: int = None, doc_type: str = None) -> List[Dict]:
        """Retrieve document history for analysis."""
        results = []
        if not self.requests_dir.exists():
            return results

        # Walk through all request files
        for req_file in self.requests_dir.rglob("*.json"):
            try:
                with open(req_file) as f:
                    data = json.load(f)
                if user_id and data["user_id"] != user_id:
                    continue
                if doc_type and data["inferred_type"] != doc_type:
                    continue
                results.append(data)
            except:
                continue

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)
