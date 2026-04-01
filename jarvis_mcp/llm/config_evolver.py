"""
ConfigEvolver - Auto-evolves CLAUDE.md based on actual model performance.
Reads fallback stats, generates suggestions, applies high-priority changes.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging


class ConfigEvolver:
    """
    Automatically evolves CLAUDE.md configuration.
    - Analyzes model performance
    - Suggests improvements
    - Auto-applies high-priority changes
    - Tracks evolution history
    """

    def __init__(self, account_path: Optional[str] = None):
        """Initialize config evolver."""
        self.logger = logging.getLogger(__name__)
        self.account_path = Path(account_path) if account_path else None
        self.config_file = account_path / ".config_evolution.json" if account_path else None
        self.evolution_history = []
        self._load_history()

    def _load_history(self):
        """Load previous evolution history."""
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.evolution_history = data.get('history', [])
            except Exception as e:
                self.logger.warning(f"Could not load evolution history: {e}")

    def _save_history(self):
        """Save evolution history to disk."""
        if not self.config_file:
            return

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({
                    'history': self.evolution_history[-100:],  # Keep last 100
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            self.logger.debug("Evolution history saved")
        except Exception as e:
            self.logger.warning(f"Could not save evolution history: {e}")

    async def analyze_and_suggest_improvements(
        self,
        fallback_stats: Dict[str, Any],
        current_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze fallback statistics and generate improvement suggestions.
        
        Returns list of suggestions with priority levels.
        """
        suggestions = []
        model_perf = fallback_stats.get('model_performance', {})

        if not model_perf:
            self.logger.debug("No model performance data to analyze")
            return suggestions

        for model_name, perf_data in model_perf.items():
            success_rate = perf_data.get('success_rate', 0)
            quality = perf_data.get('avg_quality', 0)
            failures = perf_data.get('failures', 0)
            response_time = perf_data.get('avg_response_time', 0)

            # CRITICAL: Model failing too often
            if failures > 20 or success_rate < 0.7:
                suggestions.append({
                    'type': 'remove_model',
                    'model': model_name,
                    'reason': f'Low success rate ({success_rate*100:.0f}%), {failures} failures',
                    'action': f'Remove {model_name} from primary models',
                    'priority': 'critical'
                })

            # WARNING: Model quality declining
            elif quality < 3.5:
                suggestions.append({
                    'type': 'deprecate_model',
                    'model': model_name,
                    'reason': f'Low quality score ({quality:.1f}/5)',
                    'action': f'Move {model_name} to fallback-only',
                    'priority': 'high'
                })

            # WARNING: Model getting slow
            elif response_time > 15:
                suggestions.append({
                    'type': 'slow_model',
                    'model': model_name,
                    'reason': f'Slow response time ({response_time:.1f}s)',
                    'action': f'Consider reducing usage of {model_name}',
                    'priority': 'medium'
                })

            # GOOD: Model performing excellently
            elif success_rate > 0.95 and quality > 4.5:
                suggestions.append({
                    'type': 'expand_model',
                    'model': model_name,
                    'reason': f'Excellent performance ({success_rate*100:.0f}% success, {quality:.1f} quality)',
                    'action': f'Expand usage of {model_name}',
                    'priority': 'low'
                })

        return suggestions

    async def auto_evolve_config(
        self,
        suggestions: List[Dict[str, Any]],
        claude_md_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Auto-apply high-priority suggestions to CLAUDE.md.
        
        Only applies CRITICAL and HIGH priority changes.
        """
        evolution_result = {
            'timestamp': datetime.now().isoformat(),
            'suggestions_processed': len(suggestions),
            'changes_made': [],
            'changes_skipped': [],
        }

        if not claude_md_path or not claude_md_path.exists():
            self.logger.info("No CLAUDE.md found for evolution")
            return evolution_result

        try:
            with open(claude_md_path, 'r') as f:
                claude_md = f.read()
        except Exception as e:
            self.logger.error(f"Could not read CLAUDE.md: {e}")
            return evolution_result

        # Filter for high-priority suggestions
        high_priority = [s for s in suggestions if s.get('priority') in ['critical', 'high']]

        for suggestion in high_priority:
            model = suggestion.get('model')
            action_type = suggestion.get('type')

            if action_type == 'remove_model':
                # Mark model as deprecated in CLAUDE.md
                if f'- {model}' in claude_md:
                    claude_md = claude_md.replace(
                        f'- {model}',
                        f'- ~~{model}~~ [DEPRECATED: {suggestion.get("reason")}]'
                    )
                    evolution_result['changes_made'].append({
                        'action': 'remove',
                        'model': model,
                        'reason': suggestion.get('reason')
                    })
                    self.logger.info(f"Marked {model} as deprecated")

            elif action_type == 'deprecate_model':
                # Add warning comment
                if model in claude_md:
                    claude_md += f"\n\n⚠️ Note: {model} quality declining ({suggestion.get('reason')})"
                    evolution_result['changes_made'].append({
                        'action': 'deprecate',
                        'model': model,
                        'reason': suggestion.get('reason')
                    })
                    self.logger.info(f"Added deprecation notice for {model}")

        # Save evolved CLAUDE.md
        if evolution_result['changes_made']:
            try:
                with open(claude_md_path, 'w') as f:
                    f.write(claude_md)
                self.logger.info(f"CLAUDE.md evolved with {len(evolution_result['changes_made'])} changes")
            except Exception as e:
                self.logger.error(f"Could not save evolved CLAUDE.md: {e}")
                evolution_result['changes_made'] = []

        # Record in history
        self.evolution_history.append(evolution_result)
        self._save_history()

        return evolution_result

    async def get_evolution_report(self) -> Dict[str, Any]:
        """Get complete evolution history and statistics."""
        total_changes = sum(len(e.get('changes_made', [])) for e in self.evolution_history)
        
        return {
            'total_evolutions': len(self.evolution_history),
            'recent_evolutions': self.evolution_history[-10:],
            'total_changes': total_changes,
            'last_evolution': self.evolution_history[-1] if self.evolution_history else None,
            'evolution_timeline': [
                {
                    'timestamp': e.get('timestamp'),
                    'changes': len(e.get('changes_made', []))
                }
                for e in self.evolution_history
            ]
        }

    async def generate_config_recommendations(
        self,
        fallback_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive configuration recommendations.
        """
        model_perf = fallback_stats.get('model_performance', {})
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'primary_models': {},
            'fallback_models': {},
            'models_to_avoid': [],
            'optimization_opportunities': []
        }

        # Sort by performance
        sorted_models = sorted(
            model_perf.items(),
            key=lambda x: (
                x[1].get('success_rate', 0),
                x[1].get('avg_quality', 0)
            ),
            reverse=True
        )

        # Categorize models
        for model_name, perf_data in sorted_models:
            success_rate = perf_data.get('success_rate', 0)
            quality = perf_data.get('avg_quality', 0)
            failures = perf_data.get('failures', 0)

            if success_rate >= 0.9 and quality >= 4.5:
                recommendations['primary_models'][model_name] = {
                    'success_rate': f"{success_rate*100:.0f}%",
                    'quality': f"{quality:.1f}/5",
                    'priority': len(recommendations['primary_models']) + 1
                }
            elif success_rate >= 0.7 and quality >= 4.0:
                recommendations['fallback_models'][model_name] = {
                    'success_rate': f"{success_rate*100:.0f}%",
                    'quality': f"{quality:.1f}/5",
                    'priority': len(recommendations['fallback_models']) + 1
                }
            else:
                recommendations['models_to_avoid'].append({
                    'model': model_name,
                    'reason': f'Success {success_rate*100:.0f}%, Quality {quality:.1f}, Failures {failures}'
                })

        return recommendations
