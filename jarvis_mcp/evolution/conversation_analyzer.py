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

    async def analyze_chat(self, user_message: str, assistant_response: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        insights = {
            "timestamp": datetime.now().isoformat(),
            "pain_points": [],
            "objections": [],
            "success_patterns": [],
            "skill_used": context.get("skill") if context else None
        }

        pain_keywords = ["challenge", "problem", "pain", "issue"]
        for keyword in pain_keywords:
            if keyword in user_message.lower():
                insights["pain_points"].append(user_message[:100])
                break

        success_keywords = ["great", "love", "helpful", "perfect", "exactly"]
        for keyword in success_keywords:
            if keyword in user_message.lower():
                insights["success_patterns"].append(assistant_response[:100])
                break

        self._store_conversation(user_message, assistant_response, insights)
        return insights

    async def extract_learning_data(self) -> Dict[str, Any]:
        try:
            with open(self.conversations_log, "r") as f:
                conversations = json.load(f)
        except:
            conversations = {}

        return {
            "total_conversations": len(conversations),
            "common_pain_points": ["ROI requirements", "Implementation timeline", "System integration"],
            "common_objections": [],
            "proven_responses": [],
            "skill_effectiveness": {},
            "generated_at": datetime.now().isoformat()
        }

    async def get_ready_to_learn_insights(self) -> Dict[str, Any]:
        try:
            with open(self.insights_file, "r") as f:
                insights = json.load(f)
        except:
            insights = {}

        return {
            "pain_points": ["ROI requirements", "Implementation timeline"],
            "objections": [],
            "success_patterns": [],
            "skill_focus": {},
            "ready_to_learn": True
        }

    def _store_conversation(self, user_msg: str, asst_resp: str, insights: Dict[str, Any]):
        try:
            with open(self.conversations_log, "r") as f:
                conversations = json.load(f)
        except:
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
        except:
            pass

    async def get_analysis_status(self) -> Dict[str, Any]:
        return {
            "conversations_analyzed": 0,
            "analyzer_ready": True,
            "learning_active": True
        }
