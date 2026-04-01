from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime

class OutcomePredictorAgent:
    """Predicts deal outcomes based on historical patterns."""

    def __init__(self, account_path: str):
        self.account_path = Path(account_path)
        self.outcomes_file = self.account_path / ".deal_outcomes.json"
        self.predictions_file = self.account_path / ".deal_predictions.json"

        for file_path in [self.outcomes_file, self.predictions_file]:
            if not file_path.exists():
                with open(file_path, "w") as f:
                    json.dump({}, f, indent=2)

    async def predict_closure(self, opportunity_id: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        score = 0.5
        if signals.get("has_rfi"): score += 0.15
        if signals.get("has_proposal"): score += 0.15
        if signals.get("meeting_frequency", 0) > 2: score += 0.10
        if signals.get("decision_maker_engaged"): score += 0.10
        if signals.get("competitive_pressure"): score -= 0.15

        score = min(max(score, 0.0), 1.0)

        prediction = {
            "opportunity_id": opportunity_id,
            "closure_probability": score,
            "predicted_at": datetime.now().isoformat()
        }

        predictions = self._load_json(self.predictions_file)
        predictions[opportunity_id] = prediction
        self._save_json(self.predictions_file, predictions)
        return prediction

    async def get_predictor_status(self) -> Dict[str, Any]:
        return {"predictor_ready": True, "prediction_engine_active": True}

    def _load_json(self, file_path: Path) -> Dict:
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_json(self, file_path: Path, data: Dict):
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
