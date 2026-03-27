#!/usr/bin/env python3
"""Safety Guard - handles approvals, risk assessment, and emergency stop."""

import asyncio
from pathlib import Path
from typing import Dict, Any
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class SafetyGuard:
    """Central safety and approval authority."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("safety_guard")
        self.killswitch = Path(config.killswitch_path)
        self.approval_queue = asyncio.Queue()
        self.trust_scores: Dict[str, float] = {}  # persona_id -> trust score (0-1)
        self._processing = False

    async def start(self):
        """Start safety guard."""
        self.logger.info("Starting safety guard")
        # Subscribe to modification requests
        self.event_bus.subscribe("modification.requested", self._on_modification_request)
        # Start processing loop
        self._processing = True
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop safety guard."""
        self._processing = False
        self.logger.info("Safety guard stopped")

    def _on_modification_request(self, event: Event):
        """Handle a file modification request."""
        self.approval_queue.put_nowait(event)

    async def _process_queue(self):
        """Process approval queue."""
        while self._processing:
            try:
                event = await asyncio.wait_for(self.approval_queue.get(), timeout=1.0)
                await self._evaluate_modification(event)
                self.approval_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error("Error processing modification", error=str(e))

    async def _evaluate_modification(self, event: Event):
        """Evaluate a modification for safety and decide approval."""
        persona_id = event.data.get("persona_id", "default")
        risk_level = event.data.get("risk", "medium")
        description = event.data.get("description", "No description")
        files = event.data.get("files", [])

        # Check global killswitch
        if self.killswitch.exists():
            self.logger.warning("Modification blocked: killswitch active", description=description)
            self.event_bus.publish(Event("modification.blocked", "safety_guard", {
                "reason": "killswitch_active",
                "description": description
            }))
            return

        # Trust score adjustment
        trust = self.trust_scores.get(persona_id, 0.1)  # Start low

        # Auto-approve LOW risk if trust > 0.3
        if risk_level == "low" and trust >= 0.3:
            await self._approve(event, "auto_low_risk")
            return

        # Auto-approve MEDIUM risk if trust > 0.7 and CI passes (placeholder)
        if risk_level == "medium" and trust >= 0.7:
            # In real implementation, check CI status
            await self._approve(event, "auto_medium_trust")
            return

        # Otherwise require manual approval
        self.logger.info("Approval required", risk=risk_level, trust=trust, description=description)
        self.event_bus.publish(Event("approval.required", "safety_guard", {
            "event": event,
            "trust_score": trust,
            "suggested_action": "manual_review"
        }))

    async def _approve(self, event: Event, reason: str):
        """Mark a modification as approved."""
        self.logger.debug("Modification approved", reason=reason, description=event.data.get("description"))
        self.event_bus.publish(Event("modification.approved", "safety_guard", {
            "original_event": event,
            "approved_by": "safety_guard",
            "reason": reason
        }))

    def update_trust_score(self, persona_id: str, delta: float):
        """Adjust trust score for a persona (0.0 - 1.0)."""
        current = self.trust_scores.get(persona_id, 0.1)
        new_score = max(0.0, min(1.0, current + delta))
        self.trust_scores[persona_id] = new_score
        self.logger.debug("Trust score updated", persona=persona_id, score=new_score, delta=delta)