"""Claude Sync Manager - manages notifications and sync state between JARVIS and Claude Desktop."""

import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class ClaudeSyncManager:
    """Manages notifications and sync state for Claude Desktop/OpenCode integration."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("sync.claude")
        self._running = False
        self._notifications_file = None

    async def start(self):
        self._running = True
        data_dir = Path(str(getattr(self.config.config, 'data_dir', 'data')))
        data_dir.mkdir(parents=True, exist_ok=True)
        self._notifications_file = data_dir / "notifications.json"

        if not self._notifications_file.exists():
            self._save_notifications({"notifications": [], "last_updated": ""})

        self._subscribe_to_events()
        self.logger.info("Claude Sync Manager started", notifications_file=str(self._notifications_file))

    async def stop(self):
        self._running = False
        self.logger.info("Claude Sync Manager stopped")

    def _subscribe_to_events(self):
        self.event_bus.subscribe("meeting.summary.ready", self._on_meeting_summary)
        self.event_bus.subscribe("meeting.ended", self._on_meeting_ended)
        self.event_bus.subscribe("playbook.stage.advanced", self._on_stage_advanced)
        self.event_bus.subscribe("skill.triggered", self._on_skill_triggered)
        self.event_bus.subscribe("deal.stale", self._on_deal_stale)

    async def _on_meeting_summary(self, event: Event):
        account = event.data.get("account", "Unknown")
        title = event.data.get("title", "Meeting")
        self.add_notification(
            title=f"Meeting Summary Ready: {title}",
            body=f"Meeting summary for {account} has been processed and is ready for review.",
            priority="high",
            category="meeting",
            metadata={"account": account, "title": title}
        )

    async def _on_meeting_ended(self, event: Event):
        account = event.data.get("account", "Unknown")
        self.add_notification(
            title=f"Meeting Recorded: {account}",
            body=f"Meeting recording for {account} is being processed.",
            priority="normal",
            category="meeting",
            metadata=event.data
        )

    async def _on_stage_advanced(self, event: Event):
        account = event.data.get("account", "Unknown")
        new_stage = event.data.get("new_stage", "unknown")
        self.add_notification(
            title=f"Deal Stage Advanced: {account}",
            body=f"{account} moved to {new_stage} stage. New automated actions triggered.",
            priority="high",
            category="playbook",
            metadata=event.data
        )

    async def _on_skill_triggered(self, event: Event):
        skill = event.data.get("skill", "unknown")
        account = event.data.get("account", "")
        output = event.data.get("output_file", "")
        self.add_notification(
            title=f"Skill Output: {skill}",
            body=f"New {skill} output generated{' for ' + account if account else ''}. File: {output}",
            priority="normal",
            category="skill",
            metadata=event.data
        )

    async def _on_deal_stale(self, event: Event):
        account = event.data.get("account", "Unknown")
        days = event.data.get("days_inactive", 0)
        self.add_notification(
            title=f"Stale Deal Alert: {account}",
            body=f"{account} has had no activity for {days} days. Consider reaching out.",
            priority="high",
            category="alert",
            metadata=event.data
        )

    def add_notification(self, title: str, body: str, priority: str = "normal",
                         category: str = "general", metadata: Optional[Dict] = None):
        data = self._load_notifications()
        notification = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "body": body,
            "priority": priority,
            "category": category,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "read": False,
            "metadata": metadata or {}
        }
        data["notifications"].append(notification)
        # Keep last 100 notifications
        if len(data["notifications"]) > 100:
            data["notifications"] = data["notifications"][-100:]
        data["last_updated"] = notification["timestamp"]
        self._save_notifications(data)
        self.logger.info("Notification added", title=title, priority=priority)

    def get_pending_notifications(self) -> List[Dict]:
        data = self._load_notifications()
        return [n for n in data["notifications"] if not n.get("read", False)]

    def mark_notifications_read(self, ids: List[str]):
        data = self._load_notifications()
        for n in data["notifications"]:
            if n["id"] in ids:
                n["read"] = True
        self._save_notifications(data)

    def _load_notifications(self) -> Dict:
        try:
            if self._notifications_file and self._notifications_file.exists():
                return json.loads(self._notifications_file.read_text())
        except Exception:
            pass
        return {"notifications": [], "last_updated": ""}

    def _save_notifications(self, data: Dict):
        try:
            if self._notifications_file:
                self._notifications_file.parent.mkdir(parents=True, exist_ok=True)
                self._notifications_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self.logger.error("Failed to save notifications", error=str(e))
