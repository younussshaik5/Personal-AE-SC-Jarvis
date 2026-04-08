import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class ConversationAnalyzer:
    def __init__(self, account_path: str):
        self.account_path = Path(account_path)
        self.conversations_log = self.account_path / ".conversation_learnings.json"
        self.insights_file = self.account_path / ".conversation_insights.json"

        for file_path in [self.conversations_log, self.insights_file]:
            if not file_path.exists():
                with open(file_path, "w") as f:
                    json.dump({} if "learnings" in str(file_path) else {"total_conversations": 0}, f, indent=2)

    def _load_conversations(self) -> Dict[str, Any]:
        try:
            with open(self.conversations_log, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    async def analyze_chat(self, user_message: str, assistant_response: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        insights = {
            "timestamp": datetime.now().isoformat(),
            "pain_points": [],
            "objections": [],
            "success_patterns": [],
            "skill_used": context.get("skill") if context else None
        }

        pain_keywords = ["challenge", "problem", "pain", "issue", "struggle", "blocker", "concern", "risk"]
        for keyword in pain_keywords:
            if keyword in user_message.lower():
                insights["pain_points"].append(user_message[:150])
                break

        objection_keywords = ["too expensive", "not a priority", "already have", "competitor", "too complex", "not sure"]
        for keyword in objection_keywords:
            if keyword in user_message.lower():
                insights["objections"].append(user_message[:150])
                break

        success_keywords = ["great", "love", "helpful", "perfect", "exactly", "yes", "approved", "champion", "signed"]
        for keyword in success_keywords:
            if keyword in user_message.lower():
                insights["success_patterns"].append(assistant_response[:150])
                break

        self._store_conversation(user_message, assistant_response, insights)
        return insights

    async def extract_learning_data(self) -> Dict[str, Any]:
        """Aggregate real data from stored conversations — not hardcoded."""
        conversations = self._load_conversations()

        pain_points: List[str] = []
        objections: List[str] = []
        success_patterns: List[str] = []
        skill_counts: Dict[str, int] = {}

        for conv in conversations.values():
            insights = conv.get("insights", {})
            pain_points.extend(insights.get("pain_points", []))
            objections.extend(insights.get("objections", []))
            success_patterns.extend(insights.get("success_patterns", []))
            skill = insights.get("skill_used")
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        def dedup(lst: List[str]) -> List[str]:
            seen = set()
            result = []
            for item in lst:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

        return {
            "total_conversations": len(conversations),
            "common_pain_points": dedup(pain_points)[:10],
            "common_objections": dedup(objections)[:10],
            "proven_responses": dedup(success_patterns)[:10],
            "skill_effectiveness": skill_counts,
            "generated_at": datetime.now().isoformat(),
        }

    async def get_ready_to_learn_insights(self) -> Dict[str, Any]:
        """Return real insights from stored data. Only ready=True when real data exists."""
        data = await self.extract_learning_data()

        pain_points = data["common_pain_points"]
        objections = data["common_objections"]
        success_patterns = data["proven_responses"]

        ready = len(pain_points) > 0 or len(objections) > 0 or len(success_patterns) > 0

        return {
            "pain_points": pain_points,
            "objections": objections,
            "success_patterns": success_patterns,
            "skill_focus": data["skill_effectiveness"],
            "ready_to_learn": ready,
        }

    def _store_conversation(self, user_msg: str, asst_resp: str, insights: Dict[str, Any]):
        try:
            with open(self.conversations_log, "r") as f:
                conversations = json.load(f)
        except Exception:
            conversations = {}

        conv_id = f"conv_{datetime.now().timestamp()}"
        conversations[conv_id] = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_msg[:200],
            "assistant_response": asst_resp[:200],
            "insights": insights
        }

        if len(conversations) > 1000:
            conversations = dict(list(conversations.items())[-1000:])

        try:
            with open(self.conversations_log, "w") as f:
                json.dump(conversations, f, indent=2)
        except Exception:
            pass

    async def get_analysis_status(self) -> Dict[str, Any]:
        conversations = self._load_conversations()
        return {
            "conversations_analyzed": len(conversations),
            "analyzer_ready": True,
            "learning_active": True,
        }
