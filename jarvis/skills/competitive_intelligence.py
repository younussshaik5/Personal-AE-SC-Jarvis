"""Competitive Intelligence Skill - Proactively gather and store competitive data.

This skill activates when you ask about competitors or competitive intelligence.
It will:
1. Probe for details (if needed) via conversational follow-up
2. Store competitor profiles, differentiators, battle cards
3. Organize by competitor name, date, deal context
4. Create interconnected knowledge (which deals they're involved in, which features they lack)
5. Trigger updates to pattern_recognition and notes
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class CompetitiveIntelligenceSkill:
    """Skill for competitive intelligence gathering and storage."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.competitive_intel")
        self.workspace_root = config_manager.config.workspace_root
        self.memory_dir = Path(self.workspace_root) / "MEMORY"
        self.competitors_dir = self.memory_dir / "competitors"
        self.battle_cards_dir = self.competitors_dir / "battle_cards"

    async def start(self):
        """Start the skill."""
        self.logger.info("Starting competitive intelligence skill")
        # Listen for competitor-related queries
        self.event_bus.subscribe("telegram.message", self._detect_competitor_intent)
        self.event_bus.subscribe("telegram.response", self._capture_response_insights)
        self.logger.info("Skill started")

    async def stop(self):
        """Stop the skill."""
        self.logger.info("Skill stopped")

    async def _detect_competitor_intent(self, event: Event):
        """Detect if user is asking about competitors."""
        message = event.data.get("message", "").lower()
        user_id = event.data.get("user_id")

        # Keywords indicating competitive intel request
        competitor_keywords = ['competitor', 'competition', 'rival', 'battle', 'against', 'vs', 'versus',
                               'differentiate', 'weakness', 'strength', 'battle card', 'compare',
                               'how do we stack', 'who are they', 'what do they offer']

        if any(keyword in message for keyword in competitor_keywords):
            await self._trigger_intelligence_gathering(user_id, message, event.data)

    async def _trigger_intelligence_gathering(self, user_id: int, message: str, context: Dict):
        """Initiate competitive intelligence gathering."""
        self.logger.info("Competitor intel requested", user_id=user_id, message_preview=message[:50])

        # Create a probing response to gather more details if needed
        # The actual gathering happens through conversation_learner extraction
        # But we can also proactively ask clarifying questions if info is missing

        # Check if we already have battle cards for mentioned competitors
        mentioned_competitors = self._extract_competitor_names(message)

        # For each mentioned competitor, ensure we have a profile
        for competitor in mentioned_competitors:
            profile = await self._get_or_create_profile(competitor)
            if not profile.get('differentiators', []):
                # We lack info - could ask user in a follow-up message
                # But for now, we'll rely on the conversation flow
                pass

    def _extract_competitor_names(self, message: str) -> List[str]:
        """Extract competitor names from message (simple keyword matching)."""
        # Load known competitors
        known_file = self.competitors_dir / "known_competitors.json"
        known = []
        if known_file.exists():
            with open(known_file) as f:
                known = json.load(f)

        # Also check mentions history
        mentions_file = self.memory_dir / "competitor_mentions.json"
        if mentions_file.exists():
            with open(mentions_file) as f:
                data = json.load(f)
                for m in data.get('mentions', []):
                    comp = m.get('competitor', '')
                    if comp and comp not in known:
                        known.append(comp)

        # Check which known competitors are mentioned in current message
        mentioned = []
        msg_lower = message.lower()
        for comp in known:
            if comp.lower() in msg_lower:
                mentioned.append(comp)

        return mentioned

    async def _get_or_create_profile(self, competitor_name: str) -> Dict:
        """Get or create a competitor profile."""
        profile_file = self.competitors_dir / f"{competitor_name.lower().replace(' ', '_')}.json"
        if profile_file.exists():
            with open(profile_file) as f:
                return json.load(f)
        else:
            # Create new profile
            profile = {
                "name": competitor_name,
                "first_mentioned": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "mentions_count": 0,
                "differentiators": [],
                "weaknesses": [],
                "strengths": [],
                "features": [],
                "pricing": "Unknown",
                "target_market": "Unknown",
                "battle_cards": []
            }
            profile_file.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2)
            return profile

    async def _capture_response_insights(self, event: Event):
        """Capture competitive insights from AI responses."""
        response = event.data.get("response", "")
        original_msg = event.data.get("original_message", "")

        # If response contains competitor info, extract and store
        if 'competitor' in response.lower() or 'vs' in response.lower():
            await self._extract_and_store_competitor_info(original_msg, response)

    async def _extract_and_store_competitor_info(self, query: str, response: str):
        """Extract competitor data from conversation and store."""
        try:
            from jarvis.llm.llm_client import LLMManager, Message
            llm = LLMManager(self.config_manager)
            await llm.initialize()

            extraction_prompt = f"""From this Q&A about competitors, extract structured competitive intelligence:

Question: {query}
Answer: {response}

Extract as JSON:
{{
  "competitors_mentioned": ["name1", "name2"],
  "for_each": [
    {{
      "name": "competitor_name",
      "differentiators": ["our advantage over them", ...],
      "their_strengths": [...],
      "their_weaknesses": [...],
      "features_they_lack": [...],
      "our_advantages": [...],
      "battle_card_tactics": ["how to win against them", ...]
    }}
  ],
  "key_insights": ["main takeaway", ...]
}}"""

            messages = [
                Message(role="system", content="You are a competitive intelligence analyst."),
                Message(role="user", content=extraction_prompt)
            ]

            result = await llm.generate(messages)

            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                await self._store_competitive_intelligence(data)
        except Exception as e:
            self.logger.error("Failed to extract competitive intel", error=str(e))

    async def _store_competitive_intelligence(self, data: Dict):
        """Store extracted competitive intelligence."""
        for comp_data in data.get('for_each', []):
            name = comp_data.get('name')
            if not name:
                continue

            profile = await self._get_or_create_profile(name)

            # Update profile
            profile['last_updated'] = datetime.now().isoformat()
            profile['mentions_count'] = profile.get('mentions_count', 0) + 1

            # Append arrays (avoid duplicates)
            for key in ['differentiators', 'their_strengths', 'their_weaknesses', 'features_they_lack', 'our_advantages', 'battle_card_tactics']:
                existing = profile.get(key, [])
                new_items = comp_data.get(key, [])
                for item in new_items:
                    if item not in existing:
                        existing.append(item)
                profile[key] = existing

            # Save profile
            profile_file = self.competitors_dir / f"{name.lower().replace(' ', '_')}.json"
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2)

            # Create/update battle card
            await self._create_battle_card(name, profile)

            self.logger.info("Updated competitor profile", competitor=name, mentions=profile['mentions_count'])

            # Meta-learning: publish skill.triggered event
            try:
                self.event_bus.publish(Event("skill.triggered", "competitive_intelligence", {
                    "action": "profile_updated",
                    "competitor": name,
                    "mentions": profile['mentions_count'],
                    "battle_card_created": True,
                    "timestamp": datetime.now().isoformat()
                }))
            except:
                pass

    async def _create_battle_card(self, competitor_name: str, profile: Dict):
        """Create a concise battle card for quick reference."""
        battle_card = {
            "competitor": competitor_name,
            "generated": datetime.now().isoformat(),
            "our_advantage_summary": "\n".join(profile.get('differentiators', [])[:5]),
            "their_weaknesses": profile.get('their_weaknesses', [])[:5],
            "winning_strategy": profile.get('battle_card_tactics', [])[:3],
            "quick_reference": True
        }

        bc_file = self.battle_cards_dir / f"{competitor_name.lower().replace(' ', '_')}_battle_card.json"
        bc_file.parent.mkdir(parents=True, exist_ok=True)
        with open(bc_file, 'w') as f:
            json.dump(battle_card, f, indent=2)

    async def get_competitor_profile(self, competitor_name: str) -> Dict:
        """Retrieve competitor profile (used by other components)."""
        profile_file = self.competitors_dir / f"{competitor_name.lower().replace(' ', '_')}.json"
        if profile_file.exists():
            with open(profile_file) as f:
                return json.load(f)
        return {}
