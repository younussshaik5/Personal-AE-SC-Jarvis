"""CLAUDE.md Evolution - Auto-learns and evolves CLAUDE.md based on interactions"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class ClaudeMdEvolution:
    """Tracks interactions and auto-evolves CLAUDE.md with learned preferences"""

    def __init__(self, account_path: Path):
        self.account_path = Path(account_path)
        self.metadata_file = account_path / ".claude_metadata.json"
        self.claude_md_file = account_path / "CLAUDE.md"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load interaction metadata"""
        if self.metadata_file.exists():
            try:
                return json.loads(self.metadata_file.read_text())
            except Exception as e:
                logger.warning(f"Error loading metadata: {e}")

        # Initialize default metadata
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "interactions": [],
            "suggestions": [],
        }

    def record_interaction(
        self,
        skill: str,
        model_type: str,
        quality: float,
        feedback: str = "",
    ):
        """Record a skill interaction for learning"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "skill": skill,
            "model_type": model_type,
            "quality": quality,
            "feedback": feedback,
        }

        self.metadata["interactions"].append(interaction)
        self._save_metadata()

        logger.info(
            f"Recorded interaction: {skill} with {model_type} (quality: {quality})"
        )

    def analyze_patterns(self) -> List[Dict[str, Any]]:
        """Analyze interaction patterns to suggest improvements"""
        if len(self.metadata["interactions"]) < 3:
            return []  # Need at least 3 interactions to suggest

        suggestions = []

        # Analyze skill usage
        skills = [i["skill"] for i in self.metadata["interactions"]]
        skill_counts = Counter(skills)
        most_used_skill = skill_counts.most_common(1)[0]

        # Analyze model preferences per skill
        skill_models = {}
        skill_quality = {}

        for interaction in self.metadata["interactions"]:
            skill = interaction["skill"]
            model = interaction["model_type"]
            quality = interaction["quality"]

            if skill not in skill_models:
                skill_models[skill] = []
                skill_quality[skill] = []

            skill_models[skill].append(model)
            skill_quality[skill].append(quality)

        # Generate suggestions based on patterns
        for skill, models in skill_models.items():
            model_counts = Counter(models)
            best_model = model_counts.most_common(1)[0][0]
            avg_quality = sum(skill_quality[skill]) / len(skill_quality[skill])

            # Check if pattern is consistent
            model_consistency = (
                model_counts[best_model]
                / len(models)
            )

            if model_consistency > 0.7 and avg_quality > 4.5:
                suggestion = {
                    "type": "model_preference",
                    "skill": skill,
                    "model": best_model,
                    "confidence": model_consistency,
                    "avg_quality": avg_quality,
                    "action": f"Always use {best_model} for {skill}?",
                    "status": "pending",
                }
                suggestions.append(suggestion)
                logger.info(f"Suggestion: {suggestion['action']}")

        # Analyze ROI pattern
        roi_requests = [
            i
            for i in self.metadata["interactions"]
            if "roi" in i.get("feedback", "").lower()
        ]
        if len(roi_requests) > 2:
            suggestion = {
                "type": "skill_enhancement",
                "skill": "proposal",
                "action": "Auto-include ROI analysis in all proposal generations?",
                "frequency": len(roi_requests),
                "status": "pending",
            }
            suggestions.append(suggestion)
            logger.info(f"Suggestion: {suggestion['action']}")

        self.metadata["suggestions"] = suggestions
        self._save_metadata()

        return suggestions

    def approve_suggestion(self, suggestion_index: int) -> bool:
        """Approve and apply a suggestion"""
        if (
            suggestion_index < 0
            or suggestion_index >= len(self.metadata["suggestions"])
        ):
            return False

        suggestion = self.metadata["suggestions"][suggestion_index]
        suggestion["status"] = "approved"
        suggestion["applied_at"] = datetime.now().isoformat()

        # Apply suggestion to CLAUDE.md
        if suggestion["type"] == "model_preference":
            self._add_model_preference_to_claude_md(suggestion)
        elif suggestion["type"] == "skill_enhancement":
            self._add_skill_enhancement_to_claude_md(suggestion)

        self._save_metadata()
        logger.info(f"Approved suggestion: {suggestion['action']}")
        return True

    def reject_suggestion(self, suggestion_index: int) -> bool:
        """Reject a suggestion"""
        if (
            suggestion_index < 0
            or suggestion_index >= len(self.metadata["suggestions"])
        ):
            return False

        self.metadata["suggestions"][suggestion_index]["status"] = "rejected"
        self._save_metadata()
        return True

    def _add_model_preference_to_claude_md(self, suggestion: Dict[str, Any]):
        """Add model preference to CLAUDE.md dynamic section"""
        skill = suggestion["skill"]
        model = suggestion["model"]

        claude_md_content = self._read_claude_md()

        # Find or create Learned Preferences section
        if "## Learned Preferences" not in claude_md_content:
            claude_md_content += (
                "\n\n## Learned Preferences\n"
                "Auto-updated based on interaction patterns.\n"
            )

        # Add model preference
        pref_line = f"- **{skill}**: Use {model} (quality: {suggestion['avg_quality']:.1f}/5)\n"

        if pref_line not in claude_md_content:
            # Find insertion point (after "## Learned Preferences")
            parts = claude_md_content.split("## Learned Preferences")
            if len(parts) == 2:
                claude_md_content = (
                    parts[0]
                    + "## Learned Preferences\n"
                    + pref_line
                    + parts[1]
                )

        self._write_claude_md(claude_md_content)

    def _add_skill_enhancement_to_claude_md(self, suggestion: Dict[str, Any]):
        """Add skill enhancement to CLAUDE.md dynamic section"""
        skill = suggestion["skill"]
        action = suggestion["action"]

        claude_md_content = self._read_claude_md()

        # Find or create Learned Enhancements section
        if "## Learned Enhancements" not in claude_md_content:
            claude_md_content += (
                "\n\n## Learned Enhancements\n"
                "Auto-discovered optimizations.\n"
            )

        # Add enhancement
        enhancement_line = f"- **{skill}**: {action}\n"

        if enhancement_line not in claude_md_content:
            parts = claude_md_content.split("## Learned Enhancements")
            if len(parts) == 2:
                claude_md_content = (
                    parts[0]
                    + "## Learned Enhancements\n"
                    + enhancement_line
                    + parts[1]
                )

        self._write_claude_md(claude_md_content)

    def _read_claude_md(self) -> str:
        """Read CLAUDE.md content"""
        if self.claude_md_file.exists():
            return self.claude_md_file.read_text()
        return "# CLAUDE.md - {}\n\n".format(self.account_path.name)

    def _write_claude_md(self, content: str):
        """Write CLAUDE.md content"""
        self.claude_md_file.write_text(content)
        logger.info(f"Updated CLAUDE.md for {self.account_path.name}")

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            self.metadata_file.write_text(
                json.dumps(self.metadata, indent=2)
            )
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def get_pending_suggestions(self) -> List[Dict[str, Any]]:
        """Get all pending suggestions"""
        return [
            s
            for s in self.metadata["suggestions"]
            if s.get("status") == "pending"
        ]

    def get_interaction_summary(self) -> str:
        """Get summary of interactions for user"""
        if not self.metadata["interactions"]:
            return "No interactions recorded yet."

        skill_counts = Counter(
            [i["skill"] for i in self.metadata["interactions"]]
        )
        avg_quality = sum(
            [i["quality"] for i in self.metadata["interactions"]]
        ) / len(self.metadata["interactions"])

        summary = (
            f"Total interactions: {len(self.metadata['interactions'])}\n"
            f"Average quality: {avg_quality:.1f}/5\n"
            f"Skills used: {dict(skill_counts)}\n"
        )

        pending = self.get_pending_suggestions()
        if pending:
            summary += f"\nPending suggestions: {len(pending)}\n"
            for i, suggestion in enumerate(pending):
                summary += f"  {i+1}. {suggestion.get('action', 'Unknown')}\n"

        return summary
