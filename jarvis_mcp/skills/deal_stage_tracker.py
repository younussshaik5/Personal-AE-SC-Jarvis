"""Deal Stage Management Skill — updates deal_stage.json + generates analysis"""
import json
from datetime import datetime
from jarvis_mcp.skills.base_skill import BaseSkill


class DealStageTrackerSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        new_stage = kwargs.get("stage", "")
        notes     = kwargs.get("notes", "")

        # ── Write deal_stage.json FIRST ───────────────────────────────────────
        if new_stage or notes:
            await self._update_deal_stage_json(account_name, new_stage, notes)

        # ── Then generate the analysis ────────────────────────────────────────
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        extra = ""
        if new_stage:
            extra += f"\nREQUESTED STAGE CHANGE: {new_stage}"
        if notes:
            extra += f"\nNOTES: {notes}"

        base = f"For {account_name}.{extra}\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Current Stage Assessment",
                "prompt": (
                    f"{base} assess the current deal stage:\n"
                    "1. Current stage and evidence supporting it\n"
                    "2. Stage progression history from activities\n"
                    "3. Whether the requested stage change (if any) is justified by the data\n\n"
                    "Generate ONLY this section."
                ),
                "model_type": "fast",
                "max_tokens": 800,
            },
            {
                "name": "Stage Readiness & Blockers",
                "prompt": (
                    f"{base} analyze:\n"
                    "1. What criteria are met for the current/next stage\n"
                    "2. What's blocking advancement to the next stage\n"
                    "3. Specific actions needed to advance, with owners and dates\n\n"
                    "Generate ONLY this section."
                ),
                "model_type": "fast",
                "max_tokens": 800,
            },
        ]

        return await self.parallel_sections(sections)

    async def _update_deal_stage_json(
        self, account_name: str, new_stage: str, notes: str
    ) -> None:
        """Write stage change + activity entry to deal_stage.json."""
        account_path = self.config.get_account_path(account_name)
        deal_stage_path = account_path / "deal_stage.json"
        try:
            if deal_stage_path.exists():
                with open(deal_stage_path, "r", encoding="utf-8") as f:
                    deal = json.load(f)
            else:
                deal = {"account_name": account_name, "stakeholders": [], "activities": []}

            old_stage = deal.get("stage", "Unknown")
            if new_stage:
                deal["stage"] = new_stage
            deal["last_updated"] = datetime.now().isoformat()

            # Append an activity record
            activity_note = (
                f"Stage changed: {old_stage} → {new_stage}" if new_stage else "Notes updated"
            )
            if notes:
                activity_note += f". {notes}"
            deal.setdefault("activities", []).append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "Stage Update",
                "notes": activity_note,
            })

            with open(deal_stage_path, "w", encoding="utf-8") as f:
                json.dump(deal, f, indent=2)

            self.logger.info(
                f"deal_stage.json updated: {account_name} → stage={new_stage or old_stage}"
            )
        except Exception as e:
            self.logger.error(f"Failed to update deal_stage.json for {account_name}: {e}")
