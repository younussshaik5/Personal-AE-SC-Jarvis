"""LLM Manager for JARVIS — calls NVIDIA NIM API (OpenAI-compatible)."""

import os
import json
import asyncio
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

log = logging.getLogger(__name__)


class LLMManager:
    """Manages LLM interactions with NVIDIA NIM (OpenAI-compatible endpoint)."""

    def __init__(self, config):
        self.config = config
        self.api_key = config.get_api_key("nvidia")
        self.base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1"
        ).rstrip("/")

        # Model assignments — override via env vars
        self.models = {
            "default":      os.getenv("NVIDIA_MODEL",           "meta/llama-3.3-70b-instruct"),
            "reasoning":    os.getenv("NVIDIA_REASONING_MODEL", "meta/llama-3.3-70b-instruct"),
            "fast":         os.getenv("NVIDIA_FAST_MODEL",      "meta/llama-3.1-8b-instruct"),
            "long_context": os.getenv("NVIDIA_LONG_MODEL",      "meta/llama-3.1-70b-instruct"),
            "text":         os.getenv("NVIDIA_TEXT_MODEL",      "meta/llama-3.3-70b-instruct"),
            "quick":        os.getenv("NVIDIA_FAST_MODEL",      "meta/llama-3.1-8b-instruct"),
        }

        if not self.api_key:
            log.warning("NVIDIA_API_KEY not set — LLM calls will fail. Run setup.sh and add your key to .env")

    def _call_api_sync(self, model: str, messages: list, max_tokens: int, temperature: float) -> str:
        """Make a synchronous HTTPS call to the NVIDIA NIM endpoint."""
        if not self.api_key:
            return "❌ NVIDIA_API_KEY not configured. Edit your .env file and add NVIDIA_API_KEY=nvapi-..."

        url = f"{self.base_url}/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            log.error(f"NVIDIA API HTTP {e.code}: {error_body}")
            if e.code == 401:
                return "❌ NVIDIA API key invalid or expired. Update NVIDIA_API_KEY in .env"
            if e.code == 429:
                return "❌ NVIDIA API rate limit hit. Wait a moment and retry."
            return f"❌ NVIDIA API error {e.code}: {error_body[:200]}"
        except Exception as e:
            log.error(f"NVIDIA API call failed: {e}")
            return f"❌ LLM call failed: {e}"

    async def generate(
        self,
        prompt: str,
        model_type: str = "default",
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: str = "You are JARVIS, an expert AI sales assistant specializing in enterprise B2B sales. Generate professional, detailed, actionable output in markdown format.",
        **kwargs
    ) -> str:
        """Generate text using NVIDIA NIM API."""
        model = self.models.get(model_type, self.models["default"])
        log.info(f"LLM generate: model={model} type={model_type} tokens={max_tokens}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]

        # Run blocking HTTP call in a thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._call_api_sync,
            model, messages, max_tokens, temperature
        )
        return result

    async def batch_generate(
        self,
        prompts: List[str],
        model_type: str = "default",
        **kwargs
    ) -> List[str]:
        """Generate multiple responses concurrently."""
        tasks = [self.generate(p, model_type=model_type, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)
