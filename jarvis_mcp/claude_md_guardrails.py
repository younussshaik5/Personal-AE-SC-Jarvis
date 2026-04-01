"""Guardrails for self-evolution - Safety constraints and validation"""

import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class EvolutionGuardrails:
    """Safety guardrails to constrain self-evolution and prevent breaking changes"""

    # Rules that self-evolution must follow
    GUARDRAILS = {
        # 1. Quality threshold - only learn from high-quality interactions
        "min_quality_for_learning": 4.0,  # Only learn from 4.0+ quality
        "min_interactions_before_learning": 3,  # Need 3+ interactions to suggest
        
        # 2. Interaction threshold - need enough data
        "min_consistent_usage": 0.60,  # 60% consistency before auto-apply
        "min_usage_count": 3,  # Used at least 3 times
        
        # 3. What can be evolved
        "allowed_learned_sections": [
            "Learned Preferences",
            "Learned Enhancements",
        ],
        
        # 4. What CANNOT be changed
        "protected_sections": [
            "Cascade Rules",
            "Model Preferences",  # Core preferences must stay
            "Skill Preferences",   # Core preferences must stay
            "Routing Rules",       # Core rules must stay
        ],
        
        # 5. Skill safety - safe to auto-enable
        "auto_enable_whitelist": [
            "discovery",
            "battlecard",
            "proposal",
            "meeting_prep",
            "demo_strategy",
            "risk_report",
        ],
        
        # 6. Skills that should NOT auto-enable (too risky)
        "auto_enable_blacklist": [
            "scaffold_account",  # Never auto-enable account creation
        ],
        
        # 7. Changes must not exceed these limits
        "max_changes_per_evolution": 3,  # Max 3 changes per evolution
        "max_sections_to_add": 2,  # Max 2 new sections
    }

    def __init__(self):
        self.violations = []
        self.approved_changes = []

    def validate_evolution(
        self,
        skill: str,
        action: str,
        quality: float,
        consistency: float,
        usage_count: int,
    ) -> bool:
        """
        Validate if proposed evolution is safe.
        Returns True if change is approved, False if blocked.
        """
        self.violations = []

        # Rule 1: Quality threshold
        if quality < self.GUARDRAILS["min_quality_for_learning"]:
            self.violations.append(
                f"Quality {quality:.1f} below threshold {self.GUARDRAILS['min_quality_for_learning']}"
            )
            return False

        # Rule 2: Minimum interactions
        if usage_count < self.GUARDRAILS["min_usage_count"]:
            self.violations.append(
                f"Only {usage_count} uses, need {self.GUARDRAILS['min_usage_count']}+"
            )
            return False

        # Rule 3: Consistency
        if consistency < self.GUARDRAILS["min_consistent_usage"]:
            self.violations.append(
                f"Consistency {consistency:.0%} below {self.GUARDRAILS['min_consistent_usage']:.0%}"
            )
            return False

        # Rule 4: Skill whitelist check
        if "enable" in action.lower() or "auto" in action.lower():
            if skill in self.GUARDRAILS["auto_enable_blacklist"]:
                self.violations.append(
                    f"Skill {skill} is blacklisted (too risky to auto-enable)"
                )
                return False

            if skill not in self.GUARDRAILS["auto_enable_whitelist"]:
                self.violations.append(
                    f"Skill {skill} not in whitelist for auto-enable"
                )
                return False

        # Rule 5: Protected sections - never modify
        for protected in self.GUARDRAILS["protected_sections"]:
            if protected in action:
                self.violations.append(
                    f"Cannot modify protected section: {protected}"
                )
                return False

        # If all rules pass
        logger.info(f"✓ Evolution guardrail passed: {skill} - {action}")
        self.approved_changes.append(
            {
                "skill": skill,
                "action": action,
                "quality": quality,
                "consistency": consistency,
            }
        )
        return True

    def validate_claude_md_change(self, new_content: str, old_content: str) -> bool:
        """
        Validate that CLAUDE.md changes don't break the file.
        """
        # Rule 1: Must still be valid markdown
        if not self._is_valid_markdown(new_content):
            self.violations.append("New CLAUDE.md is not valid markdown")
            return False

        # Rule 2: Protected sections must exist
        for protected in self.GUARDRAILS["protected_sections"]:
            if f"## {protected}" in old_content:
                if f"## {protected}" not in new_content:
                    self.violations.append(
                        f"Protected section removed: {protected}"
                    )
                    return False

        # Rule 3: Only allowed sections added
        new_sections = self._extract_sections(new_content)
        old_sections = self._extract_sections(old_content)
        added_sections = set(new_sections) - set(old_sections)

        for section in added_sections:
            if section not in self.GUARDRAILS["allowed_learned_sections"]:
                self.violations.append(
                    f"Disallowed section added: {section}"
                )
                return False

        # Rule 4: Not too many changes
        if len(added_sections) > self.GUARDRAILS["max_sections_to_add"]:
            self.violations.append(
                f"Too many new sections ({len(added_sections)})"
            )
            return False

        logger.info("✓ CLAUDE.md validation passed")
        return True

    def _is_valid_markdown(self, content: str) -> bool:
        """Check basic markdown validity"""
        # Must have title
        if not content.startswith("#"):
            return False

        # Must not be empty
        if len(content.strip()) < 10:
            return False

        return True

    def _extract_sections(self, content: str) -> List[str]:
        """Extract section names from markdown"""
        sections = []
        for line in content.split("\n"):
            if line.startswith("## "):
                section = line.replace("## ", "").strip()
                sections.append(section)
        return sections

    def get_guardrail_report(self) -> str:
        """Get report on guardrail violations and approvals"""
        report = "Evolution Guardrail Report\n"
        report += "=" * 40 + "\n\n"

        if self.violations:
            report += f"❌ Violations ({len(self.violations)}):\n"
            for v in self.violations:
                report += f"  • {v}\n"
        else:
            report += "✓ No violations detected\n"

        if self.approved_changes:
            report += f"\n✓ Approved changes ({len(self.approved_changes)}):\n"
            for change in self.approved_changes:
                report += f"  • {change['skill']}: {change['action']}\n"

        return report
