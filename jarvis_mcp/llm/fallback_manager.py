"""
FallbackManager - Production-ready fallback system with queue monitoring.
Handles model selection, fallback routing, quality evaluation, and performance tracking.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging


class FallbackManager:
    """
    Manages dynamic fallback to alternative NVIDIA models.
    - Monitors queue times (switches if >10s)
    - Evaluates result quality
    - Tracks model performance
    - Auto-selects best model
    """

    def __init__(self, account_path: Optional[str] = None):
        """Initialize fallback manager with NVIDIA models and tracking."""
        self.logger = logging.getLogger(__name__)
        self.account_path = Path(account_path) if account_path else None
        self.config_file = account_path / ".fallback_config.json" if account_path else None

        # NVIDIA models by category with metadata
        self.nvidia_models = {
            "text": {
                "meta-llama/llama-3.1-70b-instruct": {
                    "name": "Llama 3.1 70B",
                    "quality": 4.7,
                    "speed": "medium",
                    "context": 131072,
                },
                "mistralai/mistral-large": {
                    "name": "Mistral Large",
                    "quality": 4.6,
                    "speed": "medium",
                    "context": 32000,
                },
                "nvidia/nemotron-4-340b-instruct": {
                    "name": "Nemotron 340B",
                    "quality": 4.8,
                    "speed": "slow",
                    "context": 4096,
                },
                "mistralai/mistral-7b-instruct-v0.3": {
                    "name": "Mistral 7B",
                    "quality": 4.2,
                    "speed": "fast",
                    "context": 32000,
                },
            },
            "long_context": {
                "meta-llama/llama-3.1-70b-instruct": {
                    "name": "Llama 3.1 70B",
                    "quality": 4.7,
                    "speed": "medium",
                    "context": 131072,
                },
                "mistralai/mistral-large": {
                    "name": "Mistral Large",
                    "quality": 4.6,
                    "speed": "medium",
                    "context": 32000,
                },
            },
            "reasoning": {
                "nvidia/nemotron-4-340b-instruct": {
                    "name": "Nemotron 340B",
                    "quality": 4.8,
                    "speed": "slow",
                    "context": 4096,
                },
                "meta-llama/llama-3.1-70b-instruct": {
                    "name": "Llama 3.1 70B",
                    "quality": 4.7,
                    "speed": "medium",
                    "context": 131072,
                },
            },
            "audio": {
                "nvidia/whisper-large-v3": {
                    "name": "Whisper Large V3",
                    "quality": 4.9,
                    "speed": "medium",
                    "context": 0,
                },
            },
            "video": {
                "nvidia/nv-embedqa-e5-v5": {
                    "name": "NV-EmbedQA E5",
                    "quality": 4.5,
                    "speed": "medium",
                    "context": 0,
                },
            },
            "quick": {
                "mistralai/mistral-7b-instruct-v0.3": {
                    "name": "Mistral 7B",
                    "quality": 4.2,
                    "speed": "fast",
                    "context": 32000,
                },
            },
        }

        # Performance tracking
        self.model_stats = {}
        self.queue_times = {}
        self.failure_counts = {}
        self.response_times = {}
        
        self._load_config()

    def _load_config(self):
        """Load previously saved performance data."""
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.model_stats = data.get('model_stats', {})
                    self.failure_counts = data.get('failure_counts', {})
                    self.logger.info(f"Loaded fallback config for {len(self.model_stats)} models")
            except Exception as e:
                self.logger.warning(f"Could not load fallback config: {e}")

    def _save_config(self):
        """Save performance data for next session."""
        if not self.config_file:
            return

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({
                    'model_stats': self.model_stats,
                    'failure_counts': self.failure_counts,
                    'updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save fallback config: {e}")

    async def get_best_model(
        self,
        model_type: str,
        preferred_model: Optional[str] = None,
        queue_timeout: float = 10.0
    ) -> Tuple[str, bool]:
        """
        Get best available model with fallback logic.
        
        Priority:
        1. If preferred_model is responsive (<10s queue), use it
        2. Otherwise, find best candidate by success rate + quality
        3. Fallback to most reliable model
        
        Returns: (model_id, was_fallback_used)
        """
        candidates = list(self.nvidia_models.get(model_type, {}).keys())
        
        if not candidates:
            self.logger.error(f"No models available for type: {model_type}")
            return "meta-llama/llama-3.1-70b-instruct", True

        # Check if preferred model is responsive
        if preferred_model and preferred_model in candidates:
            queue_time = self._get_avg_queue_time(preferred_model)
            if queue_time < queue_timeout:
                self.logger.debug(f"Using preferred model {preferred_model} (queue: {queue_time:.1f}s)")
                return preferred_model, False

        # Select best candidate by performance
        best_model = self._select_best_candidate(candidates, model_type)
        
        if best_model != preferred_model:
            self.logger.info(f"Fallback: {preferred_model} → {best_model}")
            return best_model, True

        return best_model, False

    def _get_avg_queue_time(self, model: str) -> float:
        """Get average queue time for model (last 10 requests)."""
        if model not in self.queue_times or not self.queue_times[model]:
            return 0.0
        
        recent = self.queue_times[model][-10:]
        return sum(recent) / len(recent)

    def _select_best_candidate(self, candidates: List[str], model_type: str) -> str:
        """
        Score models by:
        - Success rate (weight: 0.5)
        - Average quality (weight: 0.3)
        - Queue time (weight: 0.2)
        """
        best_score = -1
        best_model = candidates[0]

        for model in candidates:
            stats = self.model_stats.get(model, {})
            
            # Success rate (0-1)
            uses = stats.get('total_uses', 0)
            successes = stats.get('successful_uses', 0)
            success_rate = (successes / uses) if uses > 0 else 0.5
            
            # Quality (0-5)
            quality_scores = stats.get('quality_scores', [4.0])
            avg_quality = sum(quality_scores[-20:]) / len(quality_scores[-20:]) if quality_scores else 4.0
            
            # Queue time (lower is better)
            queue_time = self._get_avg_queue_time(model)
            queue_score = max(0, 1.0 - (queue_time / 10.0))  # Penalize if >10s
            
            # Combine scores
            score = (success_rate * 0.5) + ((avg_quality / 5.0) * 0.3) + (queue_score * 0.2)
            score -= (self.failure_counts.get(model, 0) * 0.05)  # Penalize failures
            
            if score > best_score:
                best_score = score
                best_model = model

        return best_model

    async def record_model_usage(
        self,
        model: str,
        queue_time: float,
        response_time: float,
        success: bool,
        quality_score: float = 4.0
    ):
        """
        Record comprehensive model performance metrics.
        """
        # Track queue time
        if model not in self.queue_times:
            self.queue_times[model] = []
        self.queue_times[model].append(queue_time)
        self.queue_times[model] = self.queue_times[model][-100:]

        # Track response time
        if model not in self.response_times:
            self.response_times[model] = []
        self.response_times[model].append(response_time)
        self.response_times[model] = self.response_times[model][-100:]

        # Track failures
        if not success:
            self.failure_counts[model] = self.failure_counts.get(model, 0) + 1

        # Update statistics
        if model not in self.model_stats:
            self.model_stats[model] = {
                'total_uses': 0,
                'successful_uses': 0,
                'quality_scores': [],
                'success_rate': 0.0,
                'avg_quality': 0.0,
                'avg_response_time': 0.0,
            }

        stats = self.model_stats[model]
        stats['total_uses'] += 1
        
        if success:
            stats['successful_uses'] += 1

        stats['quality_scores'].append(quality_score)
        stats['quality_scores'] = stats['quality_scores'][-100:]

        # Calculate metrics
        stats['success_rate'] = stats['successful_uses'] / max(stats['total_uses'], 1)
        stats['avg_quality'] = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0.0
        stats['avg_response_time'] = sum(self.response_times[model]) / len(self.response_times[model]) if self.response_times[model] else 0.0

        # Save periodically
        if stats['total_uses'] % 10 == 0:
            self._save_config()

    async def evaluate_result(self, result: str) -> Tuple[bool, float, str]:
        """
        Evaluate result quality.
        - Non-empty: +1.0
        - No errors: +1.0
        - Good length: +1.0
        - Meaningful content: +1.5
        
        Returns: (is_valid, quality_score 0-5, feedback)
        """
        score = 0.0
        issues = []

        # Check 1: Non-empty
        if not result or len(result.strip()) == 0:
            return False, 0.0, "Empty result"
        score += 1.0

        # Check 2: No error prefix
        if result.startswith("ERROR") or result.startswith("ERRO"):
            return False, 1.0, "Error response"
        score += 1.0

        # Check 3: Reasonable length
        if len(result) < 20:
            issues.append("very short")
        elif len(result) > 50000:
            issues.append("very long")
        else:
            score += 1.0

        # Check 4: Has meaningful content (not just whitespace/punctuation)
        meaningful = sum(1 for c in result if c.isalnum())
        if meaningful > len(result) * 0.1:
            score += 1.5
        else:
            issues.append("low content density")

        # Final score
        final_score = min(score, 5.0)
        
        if issues:
            feedback = f"Valid but with issues: {', '.join(issues)}"
            return final_score > 2.0, final_score, feedback
        
        return True, final_score, "Valid result"

    async def handle_model_failure(
        self,
        failed_model: str,
        model_type: str,
        error: str
    ) -> Tuple[str, bool]:
        """
        Handle model failure - record and suggest fallback.
        
        Returns: (fallback_model, should_retry)
        """
        self.logger.error(f"Model {failed_model} failed: {error}")
        
        # Record failure
        self.failure_counts[failed_model] = self.failure_counts.get(failed_model, 0) + 1
        
        # Get fallback
        fallback, _ = await self.get_best_model(model_type, preferred_model=None)
        self.logger.info(f"Switching to fallback: {fallback}")
        
        return fallback, True

    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get comprehensive fallback statistics."""
        total_requests = sum(s.get('total_uses', 0) for s in self.model_stats.values())
        total_failures = sum(self.failure_counts.values())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'models_tracked': len(self.model_stats),
            'total_requests': total_requests,
            'total_failures': total_failures,
            'failure_rate': (total_failures / max(total_requests, 1)) * 100,
            'model_performance': {
                model: {
                    'uses': self.model_stats[model]['total_uses'],
                    'success_rate': self.model_stats[model]['success_rate'],
                    'avg_quality': self.model_stats[model]['avg_quality'],
                    'avg_response_time': self.model_stats[model]['avg_response_time'],
                    'failures': self.failure_counts.get(model, 0)
                }
                for model in self.model_stats.keys()
            }
        }

    def get_available_models(self, model_type: str) -> List[str]:
        """Get all models available for a type."""
        return list(self.nvidia_models.get(model_type, {}).keys())

    def get_recommended_model(self, model_type: str) -> str:
        """Get currently best-performing model for type."""
        candidates = self.get_available_models(model_type)
        if not candidates:
            return ""
        return self._select_best_candidate(candidates, model_type)
