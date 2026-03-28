#!/usr/bin/env python3
"""
Playbook automation engine.
Listens for events, evaluates stage triggers, advances deals through the
sales pipeline, and runs automated stage-entry actions.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager
from jarvis.playbook.stage_definitions import (
    DealStage,
    StageDefinition,
    PLAYBOOK_STAGES,
    get_stage_definition,
    get_all_trigger_events,
)


class PlaybookAutomationEngine:
    """
    Monitors events and automatically advances deals through the
    yellow.ai sales playbook stages, triggering skill actions at each stage.
    """

    STALE_DEAL_DAYS = 7  # Days without activity before flagging as stale

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("playbook.automation")
        self._running = False
        self._stale_check_task: Optional[asyncio.Task] = None
        self._trigger_map = get_all_trigger_events()

    async def start(self):
        """Start the automation engine and subscribe to events."""
        self._running = True
        self._subscribe_to_events()
        # Start periodic stale deal checker (every 6 hours)
        self._stale_check_task = asyncio.create_task(self._stale_check_loop())
        self.logger.info("Playbook automation engine started")

    async def stop(self):
        """Stop the automation engine."""
        self._running = False
        if self._stale_check_task and not self._stale_check_task.done():
            self._stale_check_task.cancel()
            try:
                await self._stale_check_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Playbook automation engine stopped")

    def get_deal_stage(self, account_name: str) -> Optional[DealStage]:
        """
        Read the current deal stage from ACCOUNTS/{account}/deal_stage.json.

        Args:
            account_name: Name of the account.

        Returns:
            Current DealStage or None if no stage file exists.
        """
        stage_file = self._get_stage_file(account_name)
        if not stage_file.exists():
            return None

        try:
            data = json.loads(stage_file.read_text(encoding="utf-8"))
            return DealStage(data.get("stage", "new_account"))
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(
                "Failed to read deal stage",
                account=account_name,
                error=str(e),
            )
            return None

    def advance_stage(
        self, account_name: str, new_stage: DealStage, reason: str
    ):
        """
        Advance a deal to a new stage, persist the change, and trigger auto_actions.

        Args:
            account_name: Name of the account.
            new_stage: The DealStage to advance to.
            reason: Human-readable reason for the stage change.
        """
        old_stage = self.get_deal_stage(account_name)
        stage_file = self._get_stage_file(account_name)
        stage_file.parent.mkdir(parents=True, exist_ok=True)

        # Build stage history
        history = []
        if stage_file.exists():
            try:
                existing = json.loads(stage_file.read_text(encoding="utf-8"))
                history = existing.get("history", [])
            except (json.JSONDecodeError, ValueError):
                pass

        history.append({
            "from_stage": old_stage.value if old_stage else None,
            "to_stage": new_stage.value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

        stage_data = {
            "stage": new_stage.value,
            "account_name": account_name,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "reason": reason,
            "history": history,
        }

        stage_file.write_text(
            json.dumps(stage_data, indent=2), encoding="utf-8"
        )

        self.logger.info(
            "Deal stage advanced",
            account=account_name,
            from_stage=old_stage.value if old_stage else "none",
            to_stage=new_stage.value,
            reason=reason,
        )

        # Publish stage advancement event
        self.event_bus.publish(
            Event(
                type="playbook.stage.advanced",
                source="playbook.automation",
                data={
                    "account_name": account_name,
                    "from_stage": old_stage.value if old_stage else None,
                    "to_stage": new_stage.value,
                    "reason": reason,
                },
            )
        )

        # Run auto_actions for the new stage
        self.run_stage_actions(account_name, new_stage)

    def check_stage_triggers(self, account_name: str, event_type: str) -> bool:
        """
        Evaluate whether an event should trigger a stage advancement.

        Args:
            account_name: Name of the account.
            event_type: The event type that occurred.

        Returns:
            True if a stage advancement was triggered.
        """
        if event_type not in self._trigger_map:
            return False

        target_stage = self._trigger_map[event_type]
        current_stage = self.get_deal_stage(account_name)

        # Don't regress (unless going to terminal stages)
        if current_stage is not None:
            current_def = get_stage_definition(current_stage)
            if target_stage not in current_def.next_stages:
                self.logger.debug(
                    "Stage trigger ignored (not a valid next stage)",
                    account=account_name,
                    current=current_stage.value,
                    target=target_stage.value,
                    event=event_type,
                )
                return False

        # Check if MEDDPICC threshold is met for demo stage
        if target_stage == DealStage.DEMO:
            meddpicc_score = self._get_meddpicc_score(account_name)
            if meddpicc_score is not None and meddpicc_score < 60:
                self.logger.info(
                    "Demo stage trigger blocked (MEDDPICC < 60)",
                    account=account_name,
                    meddpicc_score=meddpicc_score,
                )
                return False

        self.advance_stage(
            account_name,
            target_stage,
            f"Auto-triggered by event: {event_type}",
        )
        return True

    def run_stage_actions(self, account_name: str, stage: DealStage):
        """
        Trigger the auto_actions for a stage by publishing skill events.

        Args:
            account_name: Name of the account.
            stage: The DealStage whose actions should run.
        """
        definition = get_stage_definition(stage)

        for action in definition.auto_actions:
            self.logger.info(
                "Triggering stage action",
                account=account_name,
                stage=stage.value,
                action=action,
            )
            self.event_bus.publish(
                Event(
                    type="skill.triggered",
                    source="playbook.automation",
                    data={
                        "skill_name": action,
                        "account_name": account_name,
                        "stage": stage.value,
                        "triggered_by": "playbook_automation",
                    },
                )
            )

    async def check_stale_deals(self) -> List[dict]:
        """
        Iterate all accounts and flag deals with no activity for 7+ days.

        Returns:
            List of stale deal dicts with account name and days stale.
        """
        workspace_root = Path(self.config.workspace_root)
        accounts_dir = workspace_root / "ACCOUNTS"
        stale_deals = []

        if not accounts_dir.exists():
            return stale_deals

        now = datetime.utcnow()

        for account_dir in accounts_dir.iterdir():
            if not account_dir.is_dir():
                continue

            account_name = account_dir.name
            stage = self.get_deal_stage(account_name)

            # Skip terminal stages
            if stage in (DealStage.CLOSED_WON, DealStage.CLOSED_LOST, None):
                continue

            # Check last activity timestamp
            last_activity = self._get_last_activity(account_dir)
            if last_activity is None:
                continue

            days_stale = (now - last_activity).days
            if days_stale >= self.STALE_DEAL_DAYS:
                stale_info = {
                    "account_name": account_name,
                    "current_stage": stage.value if stage else "unknown",
                    "days_since_activity": days_stale,
                    "last_activity": last_activity.isoformat() + "Z",
                }
                stale_deals.append(stale_info)

                self.logger.warning(
                    "Stale deal detected",
                    account=account_name,
                    days_stale=days_stale,
                    stage=stage.value if stage else "unknown",
                )

                # Publish stale deal event
                self.event_bus.publish(
                    Event(
                        type="playbook.deal.stale",
                        source="playbook.automation",
                        data=stale_info,
                    )
                )

        return stale_deals

    def _subscribe_to_events(self):
        """Subscribe to relevant events for stage trigger evaluation."""

        # Meeting events
        async def _on_meeting_ended(event: Event):
            account = event.data.get("account_name")
            if account:
                self.check_stage_triggers(account, "meeting.ended")

        self.event_bus.subscribe("meeting.ended", _on_meeting_ended)

        # Meeting summary events
        async def _on_meeting_summary(event: Event):
            account = event.data.get("account_name")
            if account:
                self.check_stage_triggers(account, "meeting.summary.ready")

                # Check if demo was positive
                sentiment = event.data.get("overall_sentiment", "")
                if "positive" in str(sentiment).lower():
                    self.check_stage_triggers(
                        account, "meeting.summary.demo_positive"
                    )

        self.event_bus.subscribe("meeting.summary.ready", _on_meeting_summary)

        # Account creation events
        async def _on_account_created(event: Event):
            account = event.data.get("account_name")
            if account:
                self.check_stage_triggers(account, "account.created")

        self.event_bus.subscribe("account.created", _on_account_created)
        self.event_bus.subscribe("account.folder.created", _on_account_created)

        # Skill completion events
        async def _on_skill_completed(event: Event):
            account = event.data.get("account_name")
            skill_name = event.data.get("skill_name", "")
            if account:
                if "discovery" in skill_name:
                    self.check_stage_triggers(account, "skill.discovery.completed")
                elif "demo" in skill_name:
                    self.check_stage_triggers(account, "skill.demo.completed")

        self.event_bus.subscribe("skill.completed", _on_skill_completed)

        # MEDDPICC threshold events
        async def _on_meddpicc_scored(event: Event):
            account = event.data.get("account_name")
            score = event.data.get("total_score", 0)
            if account and score >= 60:
                self.check_stage_triggers(
                    account, "playbook.meddpicc.above_threshold"
                )

        self.event_bus.subscribe("meddpicc.scored", _on_meddpicc_scored)

        # Manual deal close events
        async def _on_deal_won(event: Event):
            account = event.data.get("account_name")
            if account:
                self.advance_stage(
                    account, DealStage.CLOSED_WON, "Deal manually marked as won"
                )

        self.event_bus.subscribe("deal.closed_won", _on_deal_won)

        async def _on_deal_lost(event: Event):
            account = event.data.get("account_name")
            if account:
                self.advance_stage(
                    account, DealStage.CLOSED_LOST,
                    event.data.get("reason", "Deal manually marked as lost"),
                )

        self.event_bus.subscribe("deal.closed_lost", _on_deal_lost)
        self.event_bus.subscribe("deal.abandoned", _on_deal_lost)

        # Proposal sent
        async def _on_proposal_sent(event: Event):
            account = event.data.get("account_name")
            if account:
                self.check_stage_triggers(account, "proposal.sent")

        self.event_bus.subscribe("proposal.sent", _on_proposal_sent)
        self.event_bus.subscribe("email.proposal.delivered", _on_proposal_sent)

        self.logger.info("Subscribed to playbook trigger events")

    async def _stale_check_loop(self):
        """Periodically check for stale deals."""
        while self._running:
            try:
                await asyncio.sleep(6 * 3600)  # Every 6 hours
                await self.check_stale_deals()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Stale deal check failed", error=str(e))

    def _get_stage_file(self, account_name: str) -> Path:
        """Get the path to the deal_stage.json file for an account."""
        workspace_root = Path(self.config.workspace_root)
        return workspace_root / "ACCOUNTS" / account_name / "deal_stage.json"

    def _get_meddpicc_score(self, account_name: str) -> Optional[int]:
        """Read the current MEDDPICC score for an account."""
        workspace_root = Path(self.config.workspace_root)
        meddpicc_file = (
            workspace_root / "ACCOUNTS" / account_name / "meddpicc.json"
        )
        if not meddpicc_file.exists():
            return None

        try:
            data = json.loads(meddpicc_file.read_text(encoding="utf-8"))
            return data.get("total_score", 0)
        except (json.JSONDecodeError, ValueError):
            return None

    def _get_last_activity(self, account_dir: Path) -> Optional[datetime]:
        """
        Determine the last activity timestamp for an account by checking
        the most recently modified file in the account directory.
        """
        latest_mtime = 0.0

        try:
            for item in account_dir.rglob("*"):
                if item.is_file():
                    mtime = item.stat().st_mtime
                    if mtime > latest_mtime:
                        latest_mtime = mtime
        except OSError:
            return None

        if latest_mtime == 0.0:
            return None

        return datetime.utcfromtimestamp(latest_mtime)
