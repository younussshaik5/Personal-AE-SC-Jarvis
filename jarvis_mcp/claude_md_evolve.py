"""CLAUDE.md Evolution - Auto-learns and evolves CLAUDE.md based on interactions"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class ClaudeMdEvolution:
    """Auto-evolves CLAUDE.md based on learned interaction patterns"""

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

        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "interactions": [],
            "learned_preferences": [],
        }

    def record_interaction(
        self,
        skill: str,
        model_type: str,
        quality: float,
        feedback: str = "",
    ):
        """
        Record a skill interaction and auto-evolve if patterns detected.
        Autonomous: automatically applies learned preferences to CLAUDE.md.
        """
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

        # Analyze patterns and auto-apply improvements every 5 interactions
        if len(self.metadata["interactions"]) % 5 == 0:
            self.auto_evolve()

    def auto_evolve(self):
        """
        AUTONOMOUS: Automatically analyze patterns and apply to CLAUDE.md.
        No user approval needed. Changes apply immediately.
        """
        if len(self.metadata["interactions"]) < 3:
            return

        improvements = self._analyze_and_apply_improvements()

        if improvements:
            logger.info(
                f"Auto-evolved CLAUDE.md: Applied {len(improvements)} improvements"
            )
            for improvement in improvements:
                logger.info(f"  ✓ {improvement}")

    def _analyze_and_apply_improvements(self) -> List[str]:
        """
        Analyze patterns and AUTOMATICALLY apply to CLAUDE.md.
        Returns list of improvements applied.
        """
        improvements = []

        # Analyze skill usage
        skills = [i["skill"] for i in self.metadata["interactions"]]
        skill_counts = Counter(skills)

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

        # Generate and apply improvements
        for skill, models in skill_models.items():
            model_counts = Counter(models)
            best_model = model_counts.most_common(1)[0][0]
            avg_quality = sum(skill_quality[skill]) / len(skill_quality[skill])

            # Check if pattern is consistent (used same model 60%+ of time)
            model_consistency = model_counts[best_model] / len(models)

            if model_consistency >= 0.6 and avg_quality >= 4.0:
                # High quality, consistent usage - auto-apply
                pref_line = f"- **{skill}**: {best_model} (quality: {avg_quality:.1f}/5)"
                self._add_learned_preference(skill, pref_line)
                improvements.append(f"Enabled {skill} with {best_model} ({avg_quality:.1f}/5)")

        # Apply most-used skills as auto-enabled
        if skill_counts:
            most_used_skill = skill_counts.most_common(1)[0][0]
            most_used_count = skill_counts.most_common(1)[0][1]

            if most_used_count >= 3:  # Used 3+ times
                enable_line = f"- **{most_used_skill}**: Auto-enabled (used {most_used_count} times)"
                self._add_learned_enhancement(most_used_skill, enable_line)
                improvements.append(f"Auto-enabled {most_used_skill}")

        return improvements

    def _add_learned_preference(self, skill: str, preference_line: str):
        """Add learned model preference to CLAUDE.md"""
        claude_md_content = self._read_claude_md()

        # Create section if doesn't exist
        if "## Learned Preferences" not in claude_md_content:
            claude_md_content += "\n\n## Learned Preferences\nAuto-learned from interaction patterns.\n"

        # Check if preference already exists
        if preference_line not in claude_md_content:
            # Insert after "## Learned Preferences"
            parts = claude_md_content.split("## Learned Preferences")
            if len(parts) == 2:
                header, rest = parts
                claude_md_content = (
                    header
                    + "## Learned Preferences\n"
                    + preference_line
                    + "\n"
                    + rest
                )

        self._write_claude_md(claude_md_content)

    def _add_learned_enhancement(self, skill: str, enhancement_line: str):
        """Add learned skill enhancement to CLAUDE.md"""
        claude_md_content = self._read_claude_md()

        # Create section if doesn't exist
        if "## Learned Enhancements" not in claude_md_content:
            claude_md_content += "\n\n## Learned Enhancements\nAuto-discovered optimizations.\n"

        # Check if enhancement already exists
        if enhancement_line not in claude_md_content:
            # Insert after "## Learned Enhancements"
            parts = claude_md_content.split("## Learned Enhancements")
            if len(parts) == 2:
                header, rest = parts
                claude_md_content = (
                    header
                    + "## Learned Enhancements\n"
                    + enhancement_line
                    + "\n"
                    + rest
                )

        self._write_claude_md(claude_md_content)

    def _read_claude_md(self) -> str:
        """Read CLAUDE.md content"""
        if self.claude_md_file.exists():
            return self.claude_md_file.read_text()
        return f"# CLAUDE.md - {self.account_path.name}\n\n"

    def _write_claude_md(self, content: str):
        """Write CLAUDE.md content"""
        self.claude_md_file.write_text(content)
        logger.info(f"Auto-evolved: Updated CLAUDE.md for {self.account_path.name}")

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            self.metadata_file.write_text(
                json.dumps(self.metadata, indent=2)
            )
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def get_interaction_summary(self) -> str:
        """Get summary of interactions and auto-evolved settings"""
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

        # Show what was learned
        learned = self.metadata.get("learned_preferences", [])
        if learned:
            summary += f"\nAuto-learned preferences: {len(learned)}\n"
            for pref in learned[:3]:
                summary += f"  • {pref}\n"

        return summary
