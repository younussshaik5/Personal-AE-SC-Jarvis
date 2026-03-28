"""Deal Stage Tracker Skill - tracks and manages deal progression through playbook stages."""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class DealStageTrackerSkill:
    """Tracks deal stages across all accounts and manages progression."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.deal_stage_tracker")

    async def start(self):
        self.event_bus.subscribe("account.created", self._on_account_created)
        self.logger.info("DealStageTrackerSkill started")

    async def stop(self):
        self.logger.info("DealStageTrackerSkill stopped")

    async def _on_account_created(self, event: Event):
        account = event.data.get("account", "")
        if account:
            self.initialize_deal(account)

    def initialize_deal(self, account: str, stage: str = "new_account"):
        workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
        stage_file = workspace / "ACCOUNTS" / account / "deal_stage.json"
        stage_file.parent.mkdir(parents=True, exist_ok=True)

        if stage_file.exists():
            return  # Don't overwrite existing stage

        data = {
            "account": account,
            "stage": stage,
            "stage_history": [{
                "stage": stage,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": "Account created"
            }],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_activity": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "meddpicc_score": 0,
            "health": "new"
        }
        stage_file.write_text(json.dumps(data, indent=2))
        self.logger.info("Deal initialized", account=account, stage=stage)

    def get_stage(self, account: str) -> Optional[Dict]:
        workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
        stage_file = workspace / "ACCOUNTS" / account / "deal_stage.json"
        if stage_file.exists():
            try:
                return json.loads(stage_file.read_text())
            except Exception:
                pass
        return None

    def advance_stage(self, account: str, new_stage: str, reason: str = ""):
        workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
        stage_file = workspace / "ACCOUNTS" / account / "deal_stage.json"

        data = self.get_stage(account)
        if not data:
            self.initialize_deal(account, new_stage)
            data = self.get_stage(account)

        old_stage = data.get("stage", "unknown")
        data["stage"] = new_stage
        data["last_activity"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        data["stage_history"].append({
            "stage": new_stage,
            "from_stage": old_stage,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reason": reason
        })

        # Update health based on stage
        if new_stage in ("closed_won", "closed_lost"):
            data["health"] = new_stage
        else:
            data["health"] = "active"

        stage_file.write_text(json.dumps(data, indent=2))
        self.logger.info("Deal stage advanced", account=account, old=old_stage, new=new_stage)

        self.event_bus.publish(Event(
            type="playbook.stage.advanced",
            source="deal_stage_tracker",
            data={"account": account, "old_stage": old_stage, "new_stage": new_stage, "reason": reason}
        ))

    def record_activity(self, account: str):
        data = self.get_stage(account)
        if data:
            workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
            stage_file = workspace / "ACCOUNTS" / account / "deal_stage.json"
            data["last_activity"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            stage_file.write_text(json.dumps(data, indent=2))

    def get_pipeline(self) -> List[Dict]:
        workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
        accounts_dir = workspace / "ACCOUNTS"
        pipeline = []

        if not accounts_dir.exists():
            return pipeline

        for account_dir in accounts_dir.iterdir():
            if account_dir.is_dir() and not account_dir.name.startswith("."):
                stage_data = self.get_stage(account_dir.name)
                if stage_data:
                    pipeline.append(stage_data)
                else:
                    pipeline.append({
                        "account": account_dir.name,
                        "stage": "unknown",
                        "health": "unknown",
                        "last_activity": ""
                    })

        return pipeline

    def get_stale_deals(self, days_threshold: int = 7) -> List[Dict]:
        pipeline = self.get_pipeline()
        stale = []
        now = time.time()

        for deal in pipeline:
            if deal.get("stage") in ("closed_won", "closed_lost", "unknown"):
                continue
            last = deal.get("last_activity", "")
            if last:
                try:
                    last_ts = time.mktime(time.strptime(last, "%Y-%m-%dT%H:%M:%SZ"))
                    days_inactive = (now - last_ts) / 86400
                    if days_inactive >= days_threshold:
                        deal["days_inactive"] = int(days_inactive)
                        stale.append(deal)
                except Exception:
                    pass

        return stale
