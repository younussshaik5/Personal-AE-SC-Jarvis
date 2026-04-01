import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class OutcomeRecorder:
    def __init__(self, account_path: str):
        self.account_path = Path(account_path)
        self.outcomes_file = self.account_path / ".skill_outcomes.json"
        self.effectiveness_file = self.account_path / ".skill_effectiveness.json"

        for file_path in [self.outcomes_file, self.effectiveness_file]:
            if not file_path.exists():
                with open(file_path, "w") as f:
                    json.dump({}, f, indent=2)

    async def record_outcome(self, skill_name: str, opportunity_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        outcome_entry = {
            "timestamp": datetime.now().isoformat(),
            "skill": skill_name,
            "opportunity_id": opportunity_id,
            "result": result.get("status", "unknown"),
            "quality_score": result.get("quality_score", 0),
            "impact": result.get("impact", "none")
        }

        try:
            with open(self.outcomes_file, "r") as f:
                outcomes = json.load(f)
        except:
            outcomes = {}

        outcome_id = f"{skill_name}_{opportunity_id}_{datetime.now().timestamp()}"
        outcomes[outcome_id] = outcome_entry

        if len(outcomes) > 1000:
            outcomes = dict(list(outcomes.items())[-1000:])

        try:
            with open(self.outcomes_file, "w") as f:
                json.dump(outcomes, f, indent=2)
        except:
            pass

        await self._update_effectiveness(skill_name, outcome_entry)
        return outcome_entry

    async def _update_effectiveness(self, skill_name: str, outcome: Dict[str, Any]):
        try:
            with open(self.effectiveness_file, "r") as f:
                effectiveness = json.load(f)
        except:
            effectiveness = {}

        if skill_name not in effectiveness:
            effectiveness[skill_name] = {"total_uses": 0, "successful_uses": 0, "avg_quality": 0, "history": []}

        skill_data = effectiveness[skill_name]
        skill_data["total_uses"] += 1
        if outcome["result"] in ["won", "successful"]:
            skill_data["successful_uses"] += 1

        skill_data["history"].append(outcome["quality_score"])
        skill_data["history"] = skill_data["history"][-100:]

        if skill_data["history"]:
            skill_data["avg_quality"] = sum(skill_data["history"]) / len(skill_data["history"])

        skill_data["win_rate"] = skill_data["successful_uses"] / max(skill_data["total_uses"], 1)
        skill_data["last_updated"] = datetime.now().isoformat()

        effectiveness[skill_name] = skill_data

        try:
            with open(self.effectiveness_file, "w") as f:
                json.dump(effectiveness, f, indent=2)
        except:
            pass

    async def get_effectiveness_report(self) -> Dict[str, Any]:
        try:
            with open(self.effectiveness_file, "r") as f:
                effectiveness = json.load(f)
        except:
            effectiveness = {}

        return {
            "total_skills_tracked": len(effectiveness),
            "skills": effectiveness,
            "top_performers": [],
            "needs_improvement": []
        }

    async def get_recorder_status(self) -> Dict[str, Any]:
        return {
            "recorder_ready": True,
            "total_outcomes_recorded": 0,
            "skills_tracked": 0
        }
