"""
NVIDIAModelDiscovery - Dynamically discovers and routes models based on file format.
Supports 15+ file formats with intelligent model selection.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging


class NVIDIAModelDiscovery:
    """
    Dynamically discovers NVIDIA models and routes to best model per file type.
    - Detects file formats
    - Maps formats to required capabilities
    - Selects best model for task
    - Caches model list locally
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize model discovery system."""
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.cache_file = self.cache_dir / ".nvidia_models_cache.json" if cache_dir else None

        # NVIDIA models with detailed metadata
        self.nvidia_models = {
            "text": {
                "meta-llama/llama-3.1-70b-instruct": {
                    "name": "Llama 3.1 70B",
                    "provider": "Meta",
                    "supports_formats": ["pdf", "doc", "docx", "txt", "md", "code"],
                    "capabilities": ["text", "long_context"],
                    "context_window": 131072,
                    "quality": 4.7,
                },
                "mistralai/mistral-large": {
                    "name": "Mistral Large",
                    "provider": "Mistral",
                    "supports_formats": ["pdf", "doc", "docx", "txt", "md"],
                    "capabilities": ["text"],
                    "context_window": 32000,
                    "quality": 4.6,
                },
                "nvidia/nemotron-4-340b-instruct": {
                    "name": "Nemotron 340B",
                    "provider": "NVIDIA",
                    "supports_formats": ["pdf", "doc", "docx", "txt", "md", "code", "json"],
                    "capabilities": ["text", "reasoning"],
                    "context_window": 4096,
                    "quality": 4.8,
                },
            },
            "multimodal": {
                "nvidia/llava-nv": {
                    "name": "LLaVA NV",
                    "provider": "NVIDIA",
                    "supports_formats": ["jpg", "jpeg", "png", "gif", "bmp"],
                    "capabilities": ["vision", "text"],
                    "quality": 4.5,
                },
                "nvidia/whisper-large-v3": {
                    "name": "Whisper Large V3",
                    "provider": "OpenAI",
                    "supports_formats": ["mp3", "wav", "m4a", "flac"],
                    "capabilities": ["audio"],
                    "quality": 4.9,
                },
                "nvidia/nv-embedqa-e5-v5": {
                    "name": "NV-EmbedQA E5",
                    "provider": "NVIDIA",
                    "supports_formats": ["mp4", "avi", "mov", "mkv"],
                    "capabilities": ["video"],
                    "quality": 4.5,
                },
            }
        }

        # Format to model type mapping
        self.format_mapping = {
            # Documents
            ".pdf": ("text", "document"),
            ".doc": ("text", "document"),
            ".docx": ("text", "document"),
            ".txt": ("text", "document"),
            ".md": ("text", "document"),
            ".rtf": ("text", "document"),

            # Spreadsheets
            ".xlsx": ("text", "data"),
            ".xls": ("text", "data"),
            ".csv": ("text", "data"),

            # Presentations
            ".pptx": ("multimodal", "presentation"),
            ".ppt": ("multimodal", "presentation"),
            ".odp": ("multimodal", "presentation"),

            # Images
            ".jpg": ("multimodal", "image"),
            ".jpeg": ("multimodal", "image"),
            ".png": ("multimodal", "image"),
            ".gif": ("multimodal", "image"),
            ".bmp": ("multimodal", "image"),

            # Audio
            ".mp3": ("multimodal", "audio"),
            ".wav": ("multimodal", "audio"),
            ".m4a": ("multimodal", "audio"),
            ".flac": ("multimodal", "audio"),
            ".aac": ("multimodal", "audio"),

            # Video
            ".mp4": ("multimodal", "video"),
            ".avi": ("multimodal", "video"),
            ".mov": ("multimodal", "video"),
            ".mkv": ("multimodal", "video"),
            ".webm": ("multimodal", "video"),

            # Code
            ".py": ("text", "code"),
            ".js": ("text", "code"),
            ".ts": ("text", "code"),
            ".java": ("text", "code"),
            ".cpp": ("text", "code"),
            ".c": ("text", "code"),
            ".cs": ("text", "code"),
            ".go": ("text", "code"),
            ".rs": ("text", "code"),

            # Data/Config
            ".json": ("text", "data"),
            ".yaml": ("text", "data"),
            ".yml": ("text", "data"),
            ".xml": ("text", "data"),
            ".sql": ("text", "data"),
            ".toml": ("text", "data"),
        }

        self.discovered_models = {}
        self.last_discovery = None
        self.discovery_interval = timedelta(hours=24)
        
        self._load_cache()

    def _load_cache(self):
        """Load cached model list."""
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.discovered_models = data.get('models', self.nvidia_models)
                    self.last_discovery = data.get('last_discovery')
                    self.logger.info(f"Loaded {len(data.get('models', {}))} cached models")
            except Exception as e:
                self.logger.warning(f"Could not load model cache: {e}")
                self.discovered_models = self.nvidia_models

    def _save_cache(self):
        """Save discovered models to cache."""
        if not self.cache_file:
            return

        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'models': self.discovered_models,
                    'last_discovery': self.last_discovery,
                    'saved_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save model cache: {e}")

    async def discover_models(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discover available models from NVIDIA (or use cache).
        
        In production, this would query https://build.nvidia.com/models
        For now, uses pre-configured list.
        """
        # Check if refresh needed
        if not force_refresh and self.last_discovery:
            last_time = datetime.fromisoformat(self.last_discovery)
            if datetime.now() - last_time < self.discovery_interval:
                self.logger.debug("Using cached models (refresh not due)")
                return self.discovered_models

        self.logger.info("Discovering models from NVIDIA...")
        
        # In production, would query NVIDIA API here
        # For now, use hardcoded list
        self.discovered_models = self.nvidia_models
        self.last_discovery = datetime.now().isoformat()
        self._save_cache()
        
        self.logger.info(f"Discovered {len(self.discovered_models)} model categories")
        return self.discovered_models

    async def get_model_for_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Automatically select best model for a file.
        
        Returns model info with capabilities and format support.
        """
        file_ext = file_path.suffix.lower()
        
        # Get model category and task type
        model_type, task_type = self.format_mapping.get(file_ext, ("text", "document"))
        
        # Get all models of this type
        models = self.discovered_models.get(model_type, {})
        
        if not models:
            # Fallback to text model
            models = self.discovered_models.get("text", {})
            model_type = "text"

        # Find best match based on format support
        best_model = None
        best_score = -1

        for model_id, model_info in models.items():
            supports = model_info.get('supports_formats', [])
            
            # Score based on format match
            if file_ext.lstrip('.') in supports:
                score = 10  # Exact match
            elif task_type in supports:
                score = 5  # Type match
            else:
                score = 1  # Generic support

            # Boost score for higher quality models
            score += model_info.get('quality', 4.0)

            if score > best_score:
                best_score = score
                best_model = {
                    'id': model_id,
                    'name': model_info.get('name'),
                    'provider': model_info.get('provider'),
                    'capabilities': model_info.get('capabilities'),
                    'supports_formats': supports,
                    'best_for': [task_type],
                    'quality': model_info.get('quality')
                }

        # Fallback if no match
        if not best_model:
            model_id = list(models.keys())[0]
            model_info = models[model_id]
            best_model = {
                'id': model_id,
                'name': model_info.get('name'),
                'provider': model_info.get('provider'),
                'capabilities': model_info.get('capabilities'),
                'supports_formats': model_info.get('supports_formats'),
                'best_for': [task_type],
                'quality': model_info.get('quality')
            }

        self.logger.debug(f"Selected {best_model.get('name')} for {file_ext}")
        return best_model

    async def get_discovery_stats(self) -> Dict[str, Any]:
        """Get model discovery statistics."""
        total_models = sum(len(m) for m in self.discovered_models.values())
        all_formats = set()
        all_capabilities = set()

        for category_models in self.discovered_models.values():
            for model_info in category_models.values():
                all_formats.update(model_info.get('supports_formats', []))
                all_capabilities.update(model_info.get('capabilities', []))

        return {
            'total_models': total_models,
            'categories': list(self.discovered_models.keys()),
            'capabilities': list(all_capabilities),
            'supported_formats': list(all_formats),
            'last_discovery': self.last_discovery,
            'cache_valid': self.last_discovery is not None,
        }

    async def refresh_models(self) -> Dict[str, Any]:
        """Force refresh model discovery."""
        self.logger.info("Force refreshing model discovery...")
        return await self.discover_models(force_refresh=True)

    def get_available_models(self, model_type: str) -> List[str]:
        """Get all models of a specific type."""
        return list(self.discovered_models.get(model_type, {}).keys())
