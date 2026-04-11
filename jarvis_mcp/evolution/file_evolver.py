"""FileEvolver - Autonomously modifies files based on learnings."""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

log = logging.getLogger(__name__)

class FileEvolver:
    """Evolves account files based on learning."""

    def __init__(self, account_path: str):
        self.account_path = Path(account_path)
        self.claude_md = self.account_path / "CLAUDE.md"
        self.discovery_md = self.account_path / "discovery.md"
        self.deal_stage_file = self.account_path / "deal_stage.json"
        self.evolution_log = self.account_path / ".evolution_changes.json"

        if not self.evolution_log.exists():
            with open(self.evolution_log, "w") as f:
                json.dump({"evolutions": []}, f, indent=2)

    async def evolve_from_outcomes(self, outcomes: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve files based on outcomes."""
        changes = {
            "timestamp": datetime.now().isoformat(),
            "type": "outcome_learning",
            "files_modified": [],
            "changes": []
        }

        if outcomes.get("closure_probability", 0) > 0.8:
            await self._update_claude_md("proposal", "Strong ROI focus with detailed analysis")
            changes["files_modified"].append("CLAUDE.md")
            changes["changes"].append("Added proposal best practice")

        await self._update_deal_stage(outcomes)
        changes["files_modified"].append("deal_stage.json")
        self._log_evolution(changes)
        return changes

    async def evolve_from_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve files based on conversation."""
        changes = {
            "timestamp": datetime.now().isoformat(),
            "type": "conversation_learning",
            "files_modified": [],
            "changes": []
        }

        if "pain_points" in conversation_data:
            for pain_point in conversation_data["pain_points"]:
                await self._add_discovery_question(pain_point)
                changes["files_modified"].append("discovery.md")
                changes["changes"].append(f"Added: {pain_point}")

        if "objections" in conversation_data:
            for obj in conversation_data["objections"]:
                changes["files_modified"].append("battlecard.md")
                changes["changes"].append(f"Objection handling: {obj}")

        self._log_evolution(changes)
        return changes

    async def _update_claude_md(self, skill: str, preference: str):
        """Update CLAUDE.md."""
        if not self.claude_md.exists():
            return

        try:
            with open(self.claude_md, "r", encoding="utf-8") as f:
                content = f.read()

            if preference not in content:
                if "## Skill Preferences" not in content:
                    content += "\n## Skill Preferences\n"
                content += f"\n- **{skill}**: {preference}"
                with open(self.claude_md, "w", encoding="utf-8") as f:
                    f.write(content)
        except FileNotFoundError as e:
            log.error(f"CLAUDE.md not found during update: {self.claude_md}", exc_info=True)
        except IOError as e:
            log.error(f"Disk I/O error updating CLAUDE.md: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Unexpected error updating CLAUDE.md: {e}", exc_info=True)

    async def _add_discovery_question(self, question: str):
        """Add discovery question."""
        if not self.discovery_md.exists():
            try:
                self.discovery_md.write_text("# Discovery Patterns\n\n", encoding="utf-8")
            except IOError as e:
                log.error(f"Failed to create discovery.md: {self.discovery_md}", exc_info=True)
                return

        try:
            with open(self.discovery_md, "r", encoding="utf-8") as f:
                content = f.read()

            if question not in content:
                content += f"\n- {question}"
                with open(self.discovery_md, "w", encoding="utf-8") as f:
                    f.write(content)
        except FileNotFoundError as e:
            log.error(f"discovery.md not found during update: {self.discovery_md}", exc_info=True)
        except IOError as e:
            log.error(f"Disk I/O error updating discovery.md: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Unexpected error updating discovery.md: {e}", exc_info=True)

    async def _update_deal_stage(self, deal_data: Dict[str, Any]):
        """Update deal tracking."""
        try:
            if self.deal_stage_file.exists():
                with open(self.deal_stage_file, "r", encoding="utf-8") as f:
                    stages = json.load(f)
            else:
                stages = {"deals": []}

            deal_id = deal_data.get("opportunity_id", "unknown")
            stages["deals"].append({
                "id": deal_id,
                "status": deal_data.get("status", "discovery"),
                "updated_at": datetime.now().isoformat()
            })
            stages["updated_at"] = datetime.now().isoformat()

            with open(self.deal_stage_file, "w", encoding="utf-8") as f:
                json.dump(stages, f, indent=2)
        except FileNotFoundError as e:
            log.error(f"deal_stage.json not found during update: {self.deal_stage_file}", exc_info=True)
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in deal_stage.json: {e}", exc_info=True)
        except IOError as e:
            log.error(f"Disk I/O error updating deal_stage.json: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Unexpected error updating deal_stage.json: {e}", exc_info=True)

    def _log_evolution(self, changes: Dict[str, Any]):
        """Log evolution."""
        try:
            with open(self.evolution_log, "r", encoding="utf-8") as f:
                evolution_log = json.load(f)
        except FileNotFoundError:
            evolution_log = {"evolutions": []}
        except json.JSONDecodeError as e:
            log.warning(f"Invalid JSON in evolution log, resetting: {e}", exc_info=True)
            evolution_log = {"evolutions": []}
        except IOError as e:
            log.error(f"Disk I/O error reading evolution log: {e}", exc_info=True)
            return

        evolution_log["evolutions"].append(changes)
        evolution_log["evolutions"] = evolution_log["evolutions"][-100:]
        evolution_log["last_evolution"] = datetime.now().isoformat()

        try:
            with open(self.evolution_log, "w", encoding="utf-8") as f:
                json.dump(evolution_log, f, indent=2)
        except IOError as e:
            log.error(f"Disk I/O error writing evolution log: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Unexpected error writing evolution log: {e}", exc_info=True)

    async def get_evolution_history(self) -> List[Dict[str, Any]]:
        try:
            with open(self.evolution_log, "r", encoding="utf-8") as f:
                evolution_log = json.load(f)
                return evolution_log.get("evolutions", [])
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            log.warning(f"Invalid JSON in evolution log: {e}")
            return []
        except IOError as e:
            log.warning(f"Disk I/O error reading evolution log: {e}")
            return []
        except Exception as e:
            log.warning(f"Unexpected error reading evolution log: {e}")
            return []
