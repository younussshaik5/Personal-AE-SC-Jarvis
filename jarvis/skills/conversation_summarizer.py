"""Conversation Summarization Skill - Auto-organize and trigger knowledge updates.

This skill runs after conversations to:
1. Summarize the interaction with key entities, decisions, facts
2. Store in date-based organized folders
3. Extract structured insights and push to appropriate knowledge files
4. Create interconnections between related data
5. Trigger dependent skills/files that need updating
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class ConversationSummarizationSkill:
    """Skill to summarize and organize conversation data."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.conversation_summarizer")
        self.workspace_root = config_manager.config.workspace_root
        self.memory_dir = Path(self.workspace_root) / "MEMORY"
        self.summaries_dir = self.memory_dir / "summaries"

    async def start(self):
        """Start the skill."""
        self.logger.info("Starting conversation summarization skill")
        # Subscribe to completed conversations (telegram.response after each exchange)
        self.event_bus.subscribe("telegram.response", self._handle_conversation_complete)
        # Also subscribe to scan completions and other events that produce summaries
        self.event_bus.subscribe("scan.completed", self._handle_scan_complete)
        self.event_bus.subscribe("modification.approved", self._handle_modification_approved)
        self.logger.info("Skill started")

    async def stop(self):
        """Stop the skill."""
        self.logger.info("Skill stopped")

    async def _handle_conversation_complete(self, event: Event):
        """Process a completed conversation exchange."""
        data = event.data
        user_id = data.get("user_id")
        original_msg = data.get("original_message", "")
        response = data.get("response", "")

        if not original_msg or not response:
            return

        await self._summarize_and_store(
            source="telegram",
            user_id=user_id,
            messages=[{"role": "user", "content": original_msg},
                     {"role": "assistant", "content": response}],
            context=data
        )

    async def _handle_scan_complete(self, event: Event):
        """Process scan completion summary."""
        data = event.data
        await self._summarize_and_store(
            source="scan",
            user_id=None,
            messages=[{"role": "system", "content": f"Workspace scan completed. Changes: {data.get('changes_detected', 0)}"}],
            context=data
        )

    async def _handle_modification_approved(self, event: Event):
        """Process approval event."""
        data = event.data
        await self._summarize_and_store(
            source="approval",
            user_id=data.get("approved_by"),
            messages=[{"role": "system", "content": f"Modification approved: {data.get('description', '')}"}],
            context=data
        )

    async def _summarize_and_store(self, source: str, user_id, messages: List[Dict], context: Dict):
        """Create summary and store with metadata, organized by account if identifiable."""
        try:
            # Generate unique ID for this interaction
            timestamp = datetime.now().strftime("%H%M%S")
            conv_id = f"{source}_{user_id or 'system'}_{timestamp}"

            # Build summary structure
            summary = {
                "id": conv_id,
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "user_id": user_id,
                "messages": messages,
                "context": context,
                "account": None,  # Will be detected
                "insights": {},
                "linked_files": [],
                "metadata": {
                    "processed": False,
                    "extracted": False,
                    "triggers_fired": []
                }
            }

            # Detect account from messages using LLM (async, will fill later)
            asyncio.create_task(self._detect_account_and_store(conv_id, summary))

            self.logger.info("Processing conversation", conv_id=conv_id, source=source)

        except Exception as e:
            self.logger.error("Failed to store summary", error=str(e))

    async def _detect_account_and_store(self, conv_id, summary):
        """Detect which account this conversation relates to and store accordingly."""
        try:
            # Try to detect account from messages using LLM
            account_name = await self._extract_account_name(summary)
            summary['account'] = account_name

            if account_name:
                # Store in account-specific folder
                await self._store_by_account(conv_id, summary)
            else:
                # Fallback to date-based organization
                await self._store_by_date(conv_id, summary)

            # Continue with insight extraction (now with account context)
            asyncio.create_task(self._extract_insights(conv_id, summary))

        except Exception as e:
            self.logger.error("Account detection failed", conv_id=conv_id, error=str(e))
            # Fallback to date-based
            await self._store_by_date(conv_id, summary)
            asyncio.create_task(self._extract_insights(conv_id, summary))

    async def _infer_account_from_insights(self, insights: Dict) -> Optional[str]:
        """Extract account name from extracted entities (deals, companies)."""
        entities = insights.get('entities', {})
        deals = entities.get('deals', [])
        companies = entities.get('companies', [])
        people = entities.get('people', [])

        # If any deal has a client, that's likely the account
        if deals:
            for deal in deals:
                client = deal.get('client')
                if client:
                    return client

        # If companies mentioned, could be account (or competitor)
        if companies:
            # Return first non-"internal" company
            for comp in companies:
                name = comp.get('name', '')
                if name and 'internal' not in name.lower():
                    return name

        return None

    async def _extract_account_name(self, summary):
        """Use LLM to detect which account/company this conversation is about."""
        try:
            from jarvis.llm.llm_client import LLMManager, Message
            llm = LLMManager(self.config_manager)
            await llm.initialize()

            # Prepare text
            messages_list = summary.get('messages', [])
            text = "\n".join([m.get('content', '') for m in messages_list])
            prompt = f"""From this conversation, identify if it's about a specific company, client, or account.

Conversation:
{text[:1000]}

Return JSON:
{{
  "account_name": "Company/account name if clearly identified, else null",
  "confidence": "high/medium/low",
  "reason": "brief explanation"
}}

If no specific company/account is mentioned, return null for account_name."""

            messages = [
                Message(role="system", content="You are an entity classification engine."),
                Message(role="user", content=prompt)
            ]

            response = await llm.generate(messages)

            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if data.get('account_name') and data.get('confidence') != 'low':
                    return data['account_name'].strip()
        except Exception as e:
            self.logger.error("Account extraction failed", error=str(e))

        return None

    async def _store_by_account(self, conv_id: str, summary: Dict):
        """Store conversation in account-specific folder."""
        try:
            account_name = summary['account']
            # Sanitize account name for folder
            safe_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()

            account_dir = self.memory_dir / "accounts" / safe_name
            account_dir.mkdir(parents=True, exist_ok=True)

            # Store conversation
            conv_file = account_dir / f"{conv_id}.json"
            with open(conv_file, 'w') as f:
                json.dump(summary, f, indent=2)

            # Update account index
            await self._update_account_index(account_name, conv_id, summary)

            self.logger.info("Stored in account folder", account=account_name, conv_id=conv_id)
        except Exception as e:
            self.logger.error("Failed to store by account", error=str(e))
            # Fallback to date-based
            await self._store_by_date(conv_id, summary)

    async def _store_by_date(self, conv_id: str, summary: Dict):
        """Fallback: store in date-based summaries folder."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = self.summaries_dir / today
        today_dir.mkdir(parents=True, exist_ok=True)

        conv_file = today_dir / f"{conv_id}.json"
        with open(conv_file, 'w') as f:
            json.dump(summary, f, indent=2)

        await self._update_index(today, conv_id, summary)

    async def _update_account_index(self, account_name: str, conv_id: str, summary: Dict):
        """Update per-account index of conversations."""
        try:
            safe_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            index_file = self.memory_dir / "accounts" / safe_name / "index.json"

            if index_file.exists():
                with open(index_file) as f:
                    index = json.load(f)
            else:
                index = {"account": account_name, "conversations": []}

            entry = {
                "id": conv_id,
                "timestamp": summary['timestamp'],
                "source": summary['source'],
                "summary": summary.get('insights', {}).get('summary', 'No summary'),
                "file": f"{conv_id}.json"
            }
            index['conversations'].append(entry)
            index['conversations'] = index['conversations'][-500:]

            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            self.logger.error("Failed to update account index", error=str(e))

    async def _extract_insights(self, conv_id: str, summary: Dict):
        """Extract structured insights from the conversation."""
        try:
            # Use LLM to extract entities, decisions, facts
            from jarvis.llm.llm_client import LLMManager, Message
            llm = LLMManager(self.config_manager)
            await llm.initialize()

            # Prepare extraction prompt
            messages_list = summary.get('messages', [])
            messages_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages_list])

            extraction_prompt = f"""Analyze this conversation and extract structured insights:

{messages_text[:2000]}

Extract as JSON with these keys:
{{
  "entities": {{
    "deals": [{{"name": "", "client": "", "budget": 0, "status": ""}}],
    "companies": [],
    "people": [],
    "technologies": []
  }},
  "decisions": [""],
  "facts_shared": [""],
  "questions_asked": [""],
  "knowledge_gaps": [""],
  "action_items": [""],
  "sentiment": "positive/neutral/negative",
  "summary": "brief 1-2 sentence summary"
}}

If no relevant data, return empty structures."""

            messages = [
                Message(role="system", content="You are an insight extraction engine."),
                Message(role="user", content=extraction_prompt)
            ]

            response = await llm.generate(messages)

            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL | re.MULTILINE)
            if json_match:
                insights = json.loads(json_match.group())
                summary['insights'] = insights

                # Infer account from deals/companies if not already set
                if not summary.get('account'):
                    inferred_account = await self._infer_account_from_insights(insights)
                    if inferred_account:
                        summary['account'] = inferred_account
                        # Re-save to account folder if we just detected
                        await self._save_summary_file(conv_id, summary)

                # Save summary to correct location (account or date folder)
                await self._save_summary_file(conv_id, summary)

                # Trigger knowledge base updates based on insights
                await self._trigger_updates(insights, summary)

                # Mark as extracted
                summary['metadata']['extracted'] = True
                self.logger.info("Extracted insights", conv_id=conv_id, insights_count=len(insights))

                # Meta-learning: publish skill.triggered event
                try:
                    self.event_bus.publish(Event("skill.triggered", "conversation_summarizer", {
                        "action": "insights_extracted",
                        "conv_id": conv_id,
                        "account": summary.get('account'),
                        "triggers": summary['metadata'].get('triggers_fired', []),
                        "timestamp": datetime.now().isoformat()
                    }))
                except:
                    pass

        except Exception as e:
            self.logger.error("Insight extraction failed", conv_id=conv_id, error=str(e))

    async def _save_summary_file(self, conv_id: str, summary: Dict):
        """Save summary file to appropriate location (account or date)."""
        try:
            account = summary.get('account')
            if account:
                # Account-based storage
                safe_name = "".join(c for c in account if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_').lower()
                account_dir = self.memory_dir / "accounts" / safe_name
                conv_file = account_dir / f"{conv_id}.json"
            else:
                # Date-based fallback
                date_str = summary['timestamp'].split('T')[0]
                date_dir = self.summaries_dir / date_str
                conv_file = date_dir / f"{conv_id}.json"

            conv_file.parent.mkdir(parents=True, exist_ok=True)
            with open(conv_file, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            self.logger.error("Failed to save summary file", error=str(e))

    async def _trigger_updates(self, insights: Dict, summary: Dict):
        """Trigger updates to relevant knowledge files based on insights."""
        triggers_fired = []
        account = summary.get('account')

        # 1. Update deals if entities.deals present
        deals = insights.get('entities', {}).get('deals', [])
        if deals:
            # Add account reference to each deal
            if account:
                for deal in deals:
                    deal['account'] = account
                    # Also store in account-specific deals folder
                    await self._store_account_deal(account, deal)
            await self._update_deals_knowledge(deals)
            triggers_fired.append('deals.json')
            summary['linked_files'].append('jarvis/data/personas/deals.json')

        # 2. Update notes with facts
        facts = insights.get('facts_shared', [])
        if facts:
            await self._append_notes('facts_from_conversations', facts)
            triggers_fired.append('notes.json (facts)')
            summary['linked_files'].append('MEMORY/notes.json')

        # 3. Log knowledge gaps
        gaps = insights.get('knowledge_gaps', [])
        if gaps:
            await self._append_notes('knowledge_gaps', gaps)
            triggers_fired.append('notes.json (gaps)')

        # 4. Record decisions
        decisions = insights.get('decisions', [])
        if decisions:
            await self._append_notes('decisions', decisions)
            triggers_fired.append('notes.json (decisions)')

        # 5. Add to experience for reflection
        await self._append_notes('conversation_experiences', {
            "summary": insights.get('summary', ''),
            "sentiment": insights.get('sentiment', 'neutral'),
            "timestamp": summary['timestamp'],
            "account": account
        })

        summary['metadata']['triggers_fired'] = triggers_fired

        # Save updated summary (already handled by _extract_insights calling _save_summary_file)
        self.logger.info("Triggered knowledge updates", triggers=triggers_fired, account=account)

    async def _update_deals_knowledge(self, deals_info: List[Dict]):
        """Update deals.json with new/updated deal information."""
        try:
            deals_file = Path('jarvis/data/personas/deals.json')
            if not deals_file.exists():
                deals_data = {"deals": []}
            else:
                with open(deals_file) as f:
                    deals_data = json.load(f)

            deals = deals_data.get('deals', [])

            for new_deal in deals_info:
                # Find existing deal by name/client similarity
                existing_idx = None
                for i, deal in enumerate(deals):
                    if (new_deal.get('name', '').lower() in deal.get('title', '').lower() or
                        new_deal.get('client', '') and new_deal.get('client', '').lower() == deal.get('client', '').lower()):
                        existing_idx = i
                        break

                if existing_idx is not None:
                    # Merge info
                    deals[existing_idx].update(new_deal)
                    deals[existing_idx]['last_updated'] = datetime.now().isoformat()
                else:
                    # Add new deal with initial status
                    deals.append({
                        "title": new_deal.get('name', 'Untitled Deal'),
                        "client": new_deal.get('client', 'Unknown'),
                        "status": new_deal.get('status', 'active'),
                        "budget": new_deal.get('budget', 0),
                        "created": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat()
                    })

            # Save
            with open(deals_file, 'w') as f:
                json.dump(deals_data, f, indent=2)

            self.logger.info("Updated deals knowledge", count=len(deals_info))

        except Exception as e:
            self.logger.error("Failed to update deals", error=str(e))

    async def _append_notes(self, category: str, content: Any):
        """Append to notes.json."""
        try:
            notes_file = self.memory_dir / "notes.json"
            notes_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing
            notes = {}
            if notes_file.exists():
                with open(notes_file) as f:
                    notes = json.load(f)

            if category not in notes:
                notes[category] = []

            # Ensure content is a list
            items = content if isinstance(content, list) else [content]

            for item in items:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "content": item,
                    "source": "conversation_summarizer"
                }
                notes[category].append(entry)

            # Keep last 2000 entries per category
            notes[category] = notes[category][-2000:]

            with open(notes_file, 'w') as f:
                json.dump(notes, f, indent=2)

        except Exception as e:
            self.logger.error("Failed to update notes", category=category, error=str(e))

    async def _update_index(self, date: str, conv_id: str, summary: Dict):
        """Update the daily index file (deprecated - using account-based now)."""
        # Keeping for backward compatibility
        pass

    async def _store_account_deal(self, account: str, deal_info: Dict):
        """Store deal information in account-specific folder."""
        try:
            safe_name = "".join(c for c in account if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            account_dir = self.memory_dir / "accounts" / safe_name
            account_dir.mkdir(parents=True, exist_ok=True)

            # Store deal in account's deals subfolder
            deals_dir = account_dir / "deals"
            deals_dir.mkdir(exist_ok=True)

            deal_file = deals_dir / f"{deal_info.get('name', 'deal').lower().replace(' ', '_')}.json"
            with open(deal_file, 'w') as f:
                json.dump(deal_info, f, indent=2)

            self.logger.debug("Stored account deal", account=account, deal=deal_info.get('name'))
        except Exception as e:
            self.logger.error("Failed to store account deal", error=str(e))
