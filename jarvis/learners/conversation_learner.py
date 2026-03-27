"""Conversation Learner - Self-evolution from all interactions.

This component listens to all system events (Telegram chats, OpenCode interactions,
AI responses, user confirmations) and continuously extracts insights to update
JARVIS's knowledge base. It enables true self-evolution by learning from every
interaction and improving future responses.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class ConversationLearner:
    """Learns from all conversations and interactions to evolve JARVIS."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("conversation_learner")
        self._running = False
        self._experience_buffer: List[Dict] = []
        self._last_reflection = datetime.now()
        self.reflection_interval = timedelta(minutes=30)  # Reflect every 30 minutes
        self.max_buffer_size = 1000  # Keep last 1000 experiences

        # Knowledge files to update
        self.workspace_root = self.config_manager.config.workspace_root
        self.memory_dir = Path(self.workspace_root) / "MEMORY"
        self.notes_file = self.memory_dir / "notes.json"
        self.learnings_file = self.memory_dir / "learnings.json"
        self.experience_file = self.memory_dir / "experience.jsonl"

    async def start(self):
        """Start the conversation learner."""
        self.logger.info("Starting conversation learner")
        self._running = True

        # Subscribe to all relevant events
        self.event_bus.subscribe("telegram.message", self._handle_telegram_message)
        self.event_bus.subscribe("telegram.response", self._handle_telegram_response)
        self.event_bus.subscribe("conversation.message", self._handle_opencode_conversation)
        self.event_bus.subscribe("modification.approved", self._handle_approval)
        self.event_bus.subscribe("modification.rejected", self._handle_rejection)
        self.event_bus.subscribe("scan.completed", self._handle_scan_completed)
        self.event_bus.subscribe("pattern.discovered", self._handle_pattern_discovered)
        self.event_bus.subscribe("competitor.detected", self._handle_competitor_detected)
        self.event_bus.subscribe("persona.switched", self._handle_persona_switched)
        # Meta‑learning: JARVIS's own actions
        self.event_bus.subscribe("account.initialized", self._handle_account_initialized)
        self.event_bus.subscribe("tool.executed", self._handle_tool_executed)
        self.event_bus.subscribe("skill.triggered", self._handle_skill_triggered)
        self.event_bus.subscribe("system.notice", self._handle_system_notice)

        # Start background reflection task
        asyncio.create_task(self._reflection_loop())

        self.logger.info("Conversation learner started")

    async def stop(self):
        """Stop the conversation learner."""
        self._running = False
        self.logger.info("Conversation learner stopped")

    async def _handle_telegram_message(self, event: Event):
        """Process incoming Telegram message."""
        data = event.data
        experience = {
            "type": "telegram_message",
            "timestamp": datetime.now().isoformat(),
            "user_id": data.get("user_id"),
            "username": data.get("username"),
            "message": data.get("message"),
            "chat_type": data.get("chat_type"),
            "context": {}
        }
        self._add_experience(experience)
        await self._extract_insights_from_message(data.get("message", ""), "telegram", data)

    async def _handle_telegram_response(self, event: Event):
        """Process JARVIS response to Telegram."""
        data = event.data
        experience = {
            "type": "telegram_response",
            "timestamp": datetime.now().isoformat(),
            "user_id": data.get("user_id"),
            "response": data.get("response"),
            "context": {}
        }
        self._add_experience(experience)

    async def _handle_opencode_conversation(self, event: Event):
        """Process OpenCode conversation message (from ConversationObserver)."""
        data = event.data
        experience = {
            "type": "opencode_conversation",
            "timestamp": datetime.now().isoformat(),
            "message_id": data.get("message_id"),
            "session_id": data.get("session_id"),
            "role": data.get("role"),
            "content": data.get("content"),
            "model": data.get("model"),
            "workspace_dir": data.get("workspace_dir"),
            "context": {}
        }
        self._add_experience(experience)
        # Also extract insights from the message content
        if data.get("content"):
            await self._extract_insights_from_message(data["content"], "opencode", data)

    async def _handle_approval(self, event: Event):
        """Process modification approval."""
        data = event.data
        experience = {
            "type": "approval",
            "timestamp": datetime.now().isoformat(),
            "approved_by": data.get("approved_by"),
            "description": data.get("description"),
            "context": data
        }
        self._add_experience(experience)
        await self._learn_from_approval(data)

    async def _handle_account_initialized(self, event: Event):
        """Process account auto-initialization (meta-learning)."""
        data = event.data
        experience = {
            "type": "account_initialized",
            "timestamp": datetime.now().isoformat(),
            "account_name": data.get("account_name"),
            "files_created": data.get("files_created", []),
            "context": data
        }
        self._add_experience(experience)

    async def _handle_tool_executed(self, event: Event):
        """Process tool execution (meta-learning)."""
        data = event.data
        experience = {
            "type": "tool_executed",
            "timestamp": datetime.now().isoformat(),
            "tool": data.get("tool"),
            "command": data.get("command"),
            "success": data.get("success", False),
            "context": data
        }
        self._add_experience(experience)

    async def _handle_skill_triggered(self, event: Event):
        """Process skill activation (meta-learning)."""
        data = event.data
        experience = {
            "type": "skill_triggered",
            "timestamp": datetime.now().isoformat(),
            "skill": data.get("skill"),
            "trigger": data.get("trigger"),
            "context": data
        }
        self._add_experience(experience)

    async def _handle_system_notice(self, event: Event):
        """Process general system notices (meta-learning)."""
        data = event.data
        experience = {
            "type": "system_notice",
            "timestamp": datetime.now().isoformat(),
            "notice": data.get("notice"),
            "component": event.source,
            "context": data
        }
        self._add_experience(experience)

    async def _handle_rejection(self, event: Event):
        """Process modification rejection."""
        data = event.data
        experience = {
            "type": "rejection",
            "timestamp": datetime.now().isoformat(),
            "rejected_by": data.get("rejected_by"),
            "description": data.get("description"),
            "context": data
        }
        self._add_experience(experience)

    async def _handle_scan_completed(self, event: Event):
        """Process scan completion."""
        data = event.data
        experience = {
            "type": "scan_completed",
            "timestamp": datetime.now().isoformat(),
            "changes_detected": data.get("changes_detected", 0),
            "patterns_learned": data.get("patterns_learned", 0)
        }
        self._add_experience(experience)

    async def _handle_pattern_discovered(self, event: Event):
        """Process new pattern discovery."""
        data = event.data
        experience = {
            "type": "pattern_discovered",
            "timestamp": datetime.now().isoformat(),
            "pattern": data.get("pattern"),
            "confidence": data.get("confidence", 0.0)
        }
        self._add_experience(experience)

    async def _handle_competitor_detected(self, event: Event):
        """Process competitor detection."""
        data = event.data
        experience = {
            "type": "competitor_detected",
            "timestamp": datetime.now().isoformat(),
            "competitor": data.get("competitor"),
            "context": data.get("context", "")[:200]
        }
        self._add_experience(experience)

    async def _handle_persona_switched(self, event: Event):
        """Process persona switch."""
        data = event.data
        experience = {
            "type": "persona_switched",
            "timestamp": datetime.now().isoformat(),
            "from_": data.get("from"),
            "to": data.get("to"),
            "reason": data.get("reason")
        }
        self._add_experience(experience)

    def _add_experience(self, experience: Dict):
        """Add experience to buffer and persist."""
        self._experience_buffer.append(experience)

        # Trim buffer if too large
        if len(self._experience_buffer) > self.max_buffer_size:
            self._experience_buffer = self._experience_buffer[-self.max_buffer_size:]

        # Append to experience file
        try:
            self.experience_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.experience_file, 'a') as f:
                f.write(json.dumps(experience) + '\n')
        except Exception as e:
            self.logger.error("Failed to write experience", error=str(e))

    async def _extract_insights_from_message(self, message: str, source: str, metadata: Dict):
        """Extract insights from a message using LLM."""
        try:
            llm_cfg = getattr(self.config_manager.config, 'llm', {})
            provider = llm_cfg.get('provider', 'none')
            if provider in ['mock', 'none']:
                return

            # Build extraction prompt
            extraction_prompt = f"""Analyze this user message and extract structured insights.

Message: "{message}"

Extract the following if present:
1. Intent (question, command, statement, feedback, greeting)
2. Entities (people, companies, deals, products, technologies)
3. New facts or information the user is sharing
4. User preferences or goals implied
5. Any mention of a specific deal/client with details (budget, timeline, status)
6. Questions that indicate knowledge gaps in JARVIS

Return as JSON with keys: intent, entities, facts, preferences, deals_mentioned, knowledge_gaps.
If nothing relevant, return empty values."""

            from jarvis.llm.llm_client import LLMManager, Message
            llm = LLMManager(self.config_manager)
            await llm.initialize()

            messages = [Message(role="system", content="You are an insight extraction engine."),
                       Message(role="user", content=extraction_prompt)]

            response = await llm.generate(messages)

            # Parse JSON response (may need cleanup)
            try:
                # Extract JSON from response (might be wrapped in text)
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    insights = json.loads(json_match.group())
                    insights['source'] = source
                    insights['timestamp'] = datetime.now().isoformat()
                    await self._apply_insights(insights)
            except json.JSONDecodeError:
                self.logger.warning("Could not parse insights JSON", response=response[:200])

        except Exception as e:
            self.logger.error("Insight extraction failed", error=str(e))

    async def _apply_insights(self, insights: Dict):
        """Apply extracted insights to knowledge bases."""
        # Update notes with new facts
        if insights.get('facts'):
            await self._append_notes('facts', insights['facts'])

        # Update deals if mentioned
        if insights.get('deals_mentioned'):
            await self._update_deals(insights['deals_mentioned'])

        # Update user preferences
        if insights.get('preferences'):
            await self._append_notes('preferences', insights['preferences'])

        # Log knowledge gaps for future improvement
        if insights.get('knowledge_gaps'):
            await self._append_notes('knowledge_gaps', insights['knowledge_gaps'])

        self.logger.info("Applied insights", facts=bool(insights.get('facts')), deals=bool(insights.get('deals_mentioned')))

    async def _append_notes(self, category: str, content: Any):
        """Append a note to notes.json."""
        try:
            self.notes_file.parent.mkdir(parents=True, exist_ok=True)
            # Load existing notes
            notes = {}
            if self.notes_file.exists():
                with open(self.notes_file) as f:
                    notes = json.load(f)

            # Initialize category if needed
            if category not in notes:
                notes[category] = []

            # Append new entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "content": content
            }
            notes[category].append(entry)

            # Keep last 1000 entries per category
            notes[category] = notes[category][-1000:]

            # Save
            with open(self.notes_file, 'w') as f:
                json.dump(notes, f, indent=2)

        except Exception as e:
            self.logger.error("Failed to update notes", error=str(e))

    async def _update_deals(self, deals_info: List[Dict]):
        """Update deals database with new information."""
        try:
            deals_file = Path('jarvis/data/personas/deals.json')
            if not deals_file.exists():
                deals_file.parent.mkdir(parents=True, exist_ok=True)
                deals_data = {"deals": []}
            else:
                with open(deals_file) as f:
                    deals_data = json.load(f)

            deals = deals_data.get('deals', [])

            for new_deal in deals_info:
                # Try to find existing deal by name/client
                existing_idx = None
                for i, deal in enumerate(deals):
                    if (new_deal.get('name', '').lower() in deal.get('title', '').lower() or
                        new_deal.get('client', '') == deal.get('client', '')):
                        existing_idx = i
                        break

                if existing_idx is not None:
                    # Update existing deal
                    deals[existing_idx].update(new_deal)
                    self.logger.info("Updated existing deal", deal=deals[existing_idx]['title'])
                else:
                    # Add new deal
                    deals.append({
                        "title": new_deal.get('name', 'Untitled Deal'),
                        "client": new_deal.get('client', 'Unknown'),
                        "status": new_deal.get('status', 'open'),
                        "budget": new_deal.get('budget', 0),
                        "last_updated": datetime.now().isoformat()
                    })
                    self.logger.info("Added new deal", deal=new_deal.get('name'))

            # Save
            with open(deals_file, 'w') as f:
                json.dump(deals_data, f, indent=2)

        except Exception as e:
            self.logger.error("Failed to update deals", error=str(e))

    async def _learn_from_approval(self, approval: Dict):
        """Learn from user approval/rejection patterns."""
        # Record which modifications get approved vs rejected
        await self._append_notes('approval_patterns', {
            "description": approval.get('description', ''),
            "approved_by": approval.get('approved_by'),
            "timestamp": datetime.now().isoformat()
        })

    async def _reflection_loop(self):
        """Periodic reflection to summarize and generalize learnings."""
        while self._running:
            await asyncio.sleep(60)  # Check every minute

            now = datetime.now()
            if now - self._last_reflection < self.reflection_interval:
                continue

            try:
                await self._perform_reflection()
                self._last_reflection = now
            except Exception as e:
                self.logger.error("Reflection failed", error=str(e))

    async def _perform_reflection(self):
        """Perform deep reflection on recent experiences."""
        if len(self._experience_buffer) < 10:
            return  # Not enough experiences

        self.logger.info("Starting reflection", buffer_size=len(self._experience_buffer))

        try:
            # Get recent experiences (last 100)
            recent = self._experience_buffer[-100:]

            # Summarize with LLM
            llm_summary = await self._summarize_experiences(recent)

            # Save learnings
            await self._save_learnings(llm_summary)

            # Update system prompts based on learnings (optional)
            await self._update_system_prompt_with_learnings(llm_summary)

            self.logger.info("Reflection completed")

        except Exception as e:
            self.logger.error("Reflection error", error=str(e))

    async def _summarize_experiences(self, experiences: List[Dict]) -> Dict:
        """Use LLM to summarize recent experiences into actionable insights."""
        try:
            llm_cfg = getattr(self.config_manager.config, 'llm', {})
            provider = llm_cfg.get('provider', 'none')
            if provider in ['mock', 'none']:
                return {"summary": "No LLM available for reflection"}

            # Format experiences for LLM
            exp_text = "\n".join([
                f"[{e.get('timestamp')}] {e.get('type')}: {str(e)[:200]}"
                for e in experiences[:50]  # Last 50 only
            ])

            prompt = f"""Analyze these recent interaction experiences and extract:

1. Recurring user intents and topics
2. User preferences that emerged
3. Knowledge gaps that keep appearing
4. Successful response patterns (what users liked)
5. Unsuccessful interactions (rejections, repeated questions)
6. New entities (companies, deals, technologies) encountered
7. Changes in user goals or focus areas

Experiences:
{exp_text}

Provide a structured summary as JSON with keys: recurring_intents, user_preferences, knowledge_gaps, successful_patterns, new_entities, focus_changes."""

            from jarvis.llm.llm_client import LLMManager, Message
            llm = LLMManager(self.config_manager)
            await llm.initialize()

            messages = [Message(role="system", content="You are a learning engine that reflects on experiences."),
                       Message(role="user", content=prompt)]

            response = await llm.generate(messages)

            # Parse JSON
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    summary = json.loads(json_match.group())
                    summary['generated_at'] = datetime.now().isoformat()
                    summary['experience_count'] = len(experiences)
                    return summary
            except json.JSONDecodeError:
                return {"raw_summary": response, "experience_count": len(experiences)}

        except Exception as e:
            self.logger.error("Failed to summarize experiences", error=str(e))
            return {}

    async def _save_learnings(self, summary: Dict):
        """Save reflection learnings to file."""
        try:
            self.learnings_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing learnings
            learnings = []
            if self.learnings_file.exists():
                with open(self.learnings_file) as f:
                    learnings = json.load(f)

            # Append new summary
            learnings.append(summary)

            # Keep last 100 summaries
            learnings = learnings[-100:]

            # Save
            with open(self.learnings_file, 'w') as f:
                json.dump(learnings, f, indent=2)

        except Exception as e:
            self.logger.error("Failed to save learnings", error=str(e))

    async def _update_system_prompt_with_learnings(self, summary: Dict):
        """Optionally update the system prompt to incorporate recent learnings."""
        # This could modify the ContextBuilder's system prompt generation
        # For now, we just log it. In future, we could store learned preferences
        # and inject them into the system prompt dynamically.
        if summary.get('user_preferences'):
            self.logger.info("Discovered user preferences", preferences=summary['user_preferences'])
