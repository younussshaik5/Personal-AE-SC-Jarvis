"""
LLM Manager for JARVIS — Kimi K2 Thinking via NVIDIA NIM with key-pool rotation.

Primary model: moonshotai/kimi-k2-thinking
  - Thinks natively: temperature=1, top_p=0.9, stream=True
  - No special reasoning params needed

Key pool: NVIDIA_API_KEY, NVIDIA_API_KEY_2, ..., NVIDIA_API_KEY_N
  - Round-robin across all keys
  - Per-key rate-limit tracking (60s cooldown)
  - Parallel sections spread automatically across keys
"""

import os
import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI, APIConnectionError, RateLimitError, APIError

log = logging.getLogger(__name__)

_BASE_URL = "https://integrate.api.nvidia.com/v1"
_MODEL    = "moonshotai/kimi-k2-thinking"
_TIMEOUT  = 120


class LLMManager:
    """NVIDIA key-pool LLM manager — round-robin rotation with per-key rate-limit tracking."""

    def __init__(self, config):
        self.config = config

        # ── Load NVIDIA key pool ─────────────────────────────────────────────
        self._keys: List[str] = []
        primary = os.getenv("NVIDIA_API_KEY", "")
        if primary:
            self._keys.append(primary)
        for i in range(2, 20):
            k = os.getenv(f"NVIDIA_API_KEY_{i}", "")
            if k:
                self._keys.append(k)

        if self._keys:
            log.info(f"NVIDIA key pool: {len(self._keys)} keys loaded")
        else:
            log.warning("No NVIDIA_API_KEY found — add to .env and restart.")

        # Thread-safe round-robin counter
        self._idx = 0
        self._lock = threading.Lock()

        # Per-key rate-limit cooldowns: {"key-0": timestamp, ...}
        self._rate_limited_until: Dict[str, float] = {}

    # ── Key rotation ─────────────────────────────────────────────────────────

    def _next_key(self) -> Tuple[Optional[str], Optional[str]]:
        """Round-robin next available key, skipping rate-limited ones."""
        n = len(self._keys)
        if n == 0:
            return None, None

        with self._lock:
            start = self._idx
            for _ in range(n):
                idx = self._idx % n
                self._idx += 1
                key_id = f"key-{idx}"
                if time.time() >= self._rate_limited_until.get(key_id, 0):
                    return self._keys[idx], key_id

        # All rate-limited — pick the one expiring soonest
        earliest = min(range(n), key=lambda i: self._rate_limited_until.get(f"key-{i}", 0))
        return self._keys[earliest], f"key-{earliest}"

    # ── Sync LLM call (runs in executor) ─────────────────────────────────────

    def _llm_call(self, api_key: str, messages: list, max_tokens: int) -> str:
        client = OpenAI(base_url=_BASE_URL, api_key=api_key)

        params = {
            "model": _MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 1,
            "top_p": 0.9,
            "stream": True,
        }

        result = []
        try:
            completion = client.chat.completions.create(**params)
            for chunk in completion:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
                # Only collect the final answer — discard reasoning_content (thinking trace)
                content = getattr(chunk.choices[0].delta, "content", None)
                if content:
                    result.append(content)
            return "".join(result)
        except Exception as e:
            log.debug(f"Streaming failed: {e}, retrying without stream")
            params["stream"] = False
            completion = client.chat.completions.create(**params)
            return completion.choices[0].message.content

    # ── Main generate ─────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        model_type: str = "default",
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: str = (
            "You are JARVIS, an expert AI sales assistant. "
            "Generate professional, detailed, actionable output in markdown format."
        ),
        **kwargs,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]

        n = len(self._keys)
        if n == 0:
            return "❌ No NVIDIA API keys configured — add NVIDIA_API_KEY to .env"

        errors = []
        loop = asyncio.get_event_loop()

        for attempt in range(n):
            api_key, key_id = self._next_key()
            if api_key is None:
                break

            # Skip if still cooling down
            cooldown = self._rate_limited_until.get(key_id, 0)
            if time.time() < cooldown:
                remaining = int(cooldown - time.time())
                errors.append(f"{key_id}: rate-limited ({remaining}s)")
                continue

            log.info(f"LLM → [{key_id}] | {_MODEL} | {model_type} | {max_tokens}tok")
            t0 = time.time()

            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, self._llm_call, api_key, messages, max_tokens,
                    ),
                    timeout=_TIMEOUT,
                )
                elapsed = round(time.time() - t0, 1)
                log.info(f"✅ [{key_id}] responded in {elapsed}s")
                return result

            except asyncio.TimeoutError:
                elapsed = round(time.time() - t0, 1)
                log.warning(f"⏱ [{key_id}] timed out after {elapsed}s — rotating")
                errors.append(f"{key_id}: timeout")
                continue

            except RateLimitError:
                self._rate_limited_until[key_id] = time.time() + 60
                log.warning(f"🚫 [{key_id}] rate-limited — rotating to next key")
                errors.append(f"{key_id}: rate-limited")
                continue

            except APIConnectionError as e:
                log.error(f"❌ [{key_id}] connection failed: {str(e)[:100]}")
                errors.append(f"{key_id}: connection error")
                continue

            except APIError as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    log.error(f"🔑 [{key_id}] invalid key")
                    errors.append(f"{key_id}: auth failed")
                    continue
                log.error(f"❌ [{key_id}] API error: {error_msg[:100]}")
                errors.append(f"{key_id}: API error")
                continue

        error_summary = " | ".join(errors)
        log.error(f"All {n} NVIDIA keys failed: {error_summary}")
        return f"❌ All NVIDIA keys exhausted: {error_summary}"

    # ── Parallel batch ─────────────────────────────────────────────────────────

    async def batch_generate(
        self,
        prompts: List[str],
        model_type: str = "default",
        **kwargs,
    ) -> List[str]:
        """Fire ALL prompts simultaneously — round-robin spreads across keys."""
        log.info(f"batch_generate: {len(prompts)} prompts across {len(self._keys)} keys")
        tasks = [
            asyncio.ensure_future(self.generate(p, model_type=model_type, **kwargs))
            for p in prompts
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if not isinstance(r, Exception) else f"❌ Generation failed: {r}"
            for r in results
        ]

    # ── Status ────────────────────────────────────────────────────────────────

    def provider_status(self) -> Dict[str, str]:
        status = {}
        for i in range(len(self._keys)):
            key_id = f"key-{i}"
            if time.time() < self._rate_limited_until.get(key_id, 0):
                remaining = int(self._rate_limited_until[key_id] - time.time())
                status[key_id] = f"rate-limited ({remaining}s)"
            else:
                status[key_id] = "ready"
        return status

    # ── Health check ──────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Test each NVIDIA key."""
        results = {}
        test_messages = [{"role": "user", "content": "Hi"}]

        for i, key in enumerate(self._keys):
            key_id = f"key-{i}"
            try:
                log.info(f"Health check: {key_id}")
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self._llm_call, key, test_messages, 50,
                    ),
                    timeout=30,
                )
                results[key_id] = {"status": "ok", "response_len": len(result)}
                log.info(f"✅ {key_id} passed")
            except Exception as e:
                results[key_id] = {"status": "error", "error": str(e)[:100]}
                log.error(f"🔴 {key_id}: {e}")

        return results
