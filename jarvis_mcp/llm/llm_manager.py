"""
LLM Manager for JARVIS — Multi-model routing with NVIDIA key-pool rotation.

Routing strategy:
  Each model_type maps to an ordered list of models.
  Requests try model[0] across all keys first.
  If all keys are exhausted/rate-limited for model[0], cascade to model[1], etc.

Key pool:
  NVIDIA_API_KEY, NVIDIA_API_KEY_2 ... NVIDIA_API_KEY_N
  Round-robin rotation with per (key, model) rate-limit tracking.

Model types:
  reasoning  — deep analysis: MEDDPICC, risk, competitive, value architecture
  writing    — long-form: proposals, SOW, battlecards, documentation
  fast       — quick tasks: summaries, insights, follow-ups, meeting prep
  default    — general purpose fallback
"""

import os
import re
import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI, APIConnectionError, RateLimitError, APIError

log = logging.getLogger(__name__)

_BASE_URL = "https://integrate.api.nvidia.com/v1"
_TIMEOUT  = 120

# Strip <think>...</think> blocks that some models (qwq-32b, step-3.5-flash)
# emit inline in the main content stream instead of via reasoning_content field.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def _strip_thinking(text: str) -> str:
    """Remove inline <think>...</think> blocks and normalise leading whitespace."""
    return _THINK_RE.sub("", text).lstrip("\n").strip()

# ── Model routing table ───────────────────────────────────────────────────────
# Each entry: model id, params, has_thinking (streams reasoning_content — we discard it)
# Order = preference. Cascade to next model only if all keys fail on current model.

MODEL_ROUTING: Dict[str, List[Dict]] = {
    "synthesis": [
        # Nemotron 120B — ONLY for IntelligenceBriefSkill.
        # 1M token context, reads all account files, writes the brief.
        # No other skill should use this type.
        {
            "model": "nvidia/nemotron-3-super-120b-a12b",
            "temperature": 0.6, "top_p": 0.9, "has_thinking": True,
            "timeout": 300,
            "extra_body": {
                "chat_template_kwargs": {"enable_thinking": True},
                "reasoning_budget": 16384,
            },
        },
    ],
    "reasoning": [
        # kimi → step3.5 → qwq — file generation for all reasoning skills:
        # MEDDPICC, risk_report, battlecard, competitive_intel, value_arch, technical_risk
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
        {"model": "stepfun-ai/step-3.5-flash",   "temperature": 1,   "top_p": 0.9, "has_thinking": True},
        {"model": "qwen/qwq-32b",                "temperature": 0.6, "top_p": 0.7, "has_thinking": False},
    ],
    "writing": [
        # Best for: proposals, SOW, documentation, battlecards
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.6, "top_p": 0.9, "has_thinking": False},
        {"model": "qwen/qwq-32b",               "temperature": 0.6, "top_p": 0.7, "has_thinking": False},
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
    ],
    "fast": [
        # Best for: quick insights, follow-up emails, meeting prep, summaries
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.6, "top_p": 0.9, "has_thinking": False},
        {"model": "qwen/qwen2-7b-instruct",      "temperature": 0.7, "top_p": 0.8, "has_thinking": False},
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
    ],
    "default": [
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.6, "top_p": 0.9, "has_thinking": False},
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
        {"model": "qwen/qwq-32b",               "temperature": 0.6, "top_p": 0.7, "has_thinking": False},
    ],
}


class LLMManager:
    """
    NVIDIA key-pool LLM manager with multi-model routing and cascade failover.

    Failover order:
      1. Try model[0] — rotate across all available keys
      2. All keys exhausted for model[0] → cascade to model[1]
      3. Repeat until a response is received or all models fail
    """

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
            log.info(f"NVIDIA key pool: {len(self._keys)} key(s) loaded")
        else:
            log.warning("No NVIDIA_API_KEY found — add to .env and restart.")

        # Thread-safe round-robin counter
        self._idx = 0
        self._lock = threading.Lock()

        # Per (key_id, model) rate-limit cooldowns: {"key-0::model-name": timestamp}
        self._rate_limited_until: Dict[str, float] = {}

    # ── Rate limit helpers ────────────────────────────────────────────────────

    def _rl_key(self, key_id: str, model: str) -> str:
        return f"{key_id}::{model}"

    def _is_available(self, key_id: str, model: str) -> bool:
        return time.time() >= self._rate_limited_until.get(self._rl_key(key_id, model), 0)

    def _mark_rate_limited(self, key_id: str, model: str, cooldown: int = 60) -> None:
        self._rate_limited_until[self._rl_key(key_id, model)] = time.time() + cooldown
        log.warning(f"🚫 [{key_id}] [{model}] rate-limited for {cooldown}s — will try next key/model")

    # ── Key rotation ──────────────────────────────────────────────────────────

    def _next_key_for_model(self, model: str) -> Tuple[Optional[str], Optional[str]]:
        """Round-robin next key that is not rate-limited for this specific model."""
        n = len(self._keys)
        if n == 0:
            return None, None

        with self._lock:
            for _ in range(n):
                idx = self._idx % n
                self._idx += 1
                key_id = f"key-{idx}"
                if self._is_available(key_id, model):
                    return self._keys[idx], key_id

        # All keys rate-limited for this model — return the one expiring soonest
        earliest = min(
            range(n),
            key=lambda i: self._rate_limited_until.get(self._rl_key(f"key-{i}", model), 0),
        )
        return self._keys[earliest], f"key-{earliest}"

    # ── Sync LLM call (runs in executor) ─────────────────────────────────────

    def _llm_call(self, api_key: str, model_cfg: Dict, messages: list, max_tokens: int) -> str:
        """
        Make a single LLM call. Handles both thinking models (has_thinking=True)
        and standard models. Only the final content is returned — thinking traces discarded.
        """
        client = OpenAI(base_url=_BASE_URL, api_key=api_key)

        params = {
            "model":       model_cfg["model"],
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": model_cfg["temperature"],
            "top_p":       model_cfg["top_p"],
            "stream":      True,
        }

        # Pass extra_body if model requires it (e.g. Nemotron reasoning_budget)
        if model_cfg.get("extra_body"):
            params["extra_body"] = model_cfg["extra_body"]

        result = []
        try:
            for chunk in client.chat.completions.create(**params):
                if not getattr(chunk, "choices", None) or not chunk.choices:
                    continue
                # Discard reasoning_content (thinking trace) — only keep final content
                content = getattr(chunk.choices[0].delta, "content", None)
                if content:
                    result.append(content)
            return _strip_thinking("".join(result))

        except Exception as e:
            log.debug(f"Streaming failed ({model_cfg['model']}): {e} — retrying without stream")
            params["stream"] = False
            completion = client.chat.completions.create(**params)
            if not completion.choices:
                raise ValueError(f"LLM returned empty choices for {model_cfg['model']}")
            content = completion.choices[0].message.content
            if not content:
                raise ValueError(f"LLM returned None content for {model_cfg['model']}")
            return _strip_thinking(content)

    # ── Main generate ─────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        model_type: str = "default",
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,          # ignored — model profiles control this
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

        if not self._keys:
            return "❌ No NVIDIA API keys configured — add NVIDIA_API_KEY to .env and restart."

        # Resolve model chain for this task type
        model_chain = MODEL_ROUTING.get(model_type) or MODEL_ROUTING["default"]

        loop = asyncio.get_event_loop()

        # Retry loop — on rate limits, wait for the shortest cooldown and try again.
        # Only gives up on hard errors (auth failure, no keys, connection refused).
        attempt_num = 0
        while True:
            attempt_num += 1
            all_errors: List[str] = []
            has_only_rate_limits = True  # will flip if we see a hard error

            for model_cfg in model_chain:
                model_name = model_cfg["model"]
                model_errors: List[str] = []
                n = len(self._keys)

                for _ in range(n):
                    api_key, key_id = self._next_key_for_model(model_name)
                    if api_key is None:
                        break

                    if not self._is_available(key_id, model_name):
                        remaining = int(
                            self._rate_limited_until.get(self._rl_key(key_id, model_name), 0) - time.time()
                        )
                        model_errors.append(f"{key_id}: rate-limited ({remaining}s)")
                        continue

                    log.info(f"LLM → [{key_id}] [{model_name}] | type={model_type} | {max_tokens}tok")
                    t0 = time.time()

                    # Per-model timeout: respect model_cfg["timeout"] or global _TIMEOUT
                    call_timeout = model_cfg.get("timeout", _TIMEOUT)

                    try:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(
                                None, self._llm_call, api_key, model_cfg, messages, max_tokens
                            ),
                            timeout=call_timeout,
                        )
                        elapsed = round(time.time() - t0, 1)
                        log.info(f"✅ [{key_id}] [{model_name}] responded in {elapsed}s")
                        return result

                    except asyncio.TimeoutError:
                        elapsed = round(time.time() - t0, 1)
                        log.warning(f"⏱ [{key_id}] [{model_name}] timed out after {elapsed}s")
                        model_errors.append(f"{key_id}: timeout")
                        has_only_rate_limits = False

                    except RateLimitError:
                        self._mark_rate_limited(key_id, model_name)
                        model_errors.append(f"{key_id}: rate-limited")

                    except APIConnectionError as e:
                        log.error(f"❌ [{key_id}] [{model_name}] connection failed: {str(e)[:80]}")
                        model_errors.append(f"{key_id}: connection error")
                        has_only_rate_limits = False

                    except APIError as e:
                        msg = str(e)
                        if "401" in msg or "Unauthorized" in msg:
                            log.error(f"🔑 [{key_id}] [{model_name}] invalid API key")
                            model_errors.append(f"{key_id}: auth failed")
                            has_only_rate_limits = False
                        elif "404" in msg or "not found" in msg.lower():
                            log.warning(f"⚠️ [{key_id}] [{model_name}] model unavailable — cascading")
                            model_errors.append(f"{key_id}: model unavailable")
                            has_only_rate_limits = False
                            break
                        else:
                            log.error(f"❌ [{key_id}] [{model_name}] API error: {msg[:80]}")
                            model_errors.append(f"{key_id}: {msg[:60]}")
                            has_only_rate_limits = False

                    except Exception as e:
                        # Catches ValueError("LLM returned None content") and any other unexpected errors
                        log.warning(f"⚠️ [{key_id}] [{model_name}] unexpected error: {str(e)[:100]} — cascading")
                        model_errors.append(f"{key_id}: {str(e)[:60]}")
                        has_only_rate_limits = False

                summary = " | ".join(model_errors)
                log.warning(f"All keys failed for [{model_name}]: {summary} — cascading to next model")
                all_errors.append(f"[{model_name}]: {summary}")

            # All models exhausted this pass.
            # If ALL failures were rate-limits, wait for the soonest key to free up and retry.
            if has_only_rate_limits and self._keys:
                now = time.time()
                soonest = min(
                    (self._rate_limited_until.get(self._rl_key(f"key-{i}", cfg["model"]), 0)
                     for i in range(len(self._keys))
                     for chain in MODEL_ROUTING.values()
                     for cfg in chain),
                    default=0,
                )
                wait = max(soonest - now + 1, 5)  # at least 5s buffer
                log.warning(
                    f"All keys rate-limited (attempt {attempt_num}) — "
                    f"waiting {wait:.0f}s for cooldown, then retrying…"
                )
                await asyncio.sleep(wait)
                continue  # retry the whole model chain

            # Hard failure (auth/connection/model error) — don't retry
            break

        error_detail = " || ".join(all_errors)
        log.error(f"All models failed for type={model_type}: {error_detail}")
        return f"❌ All models exhausted for '{model_type}': {error_detail}"

    # ── Parallel batch ────────────────────────────────────────────────────────

    async def batch_generate(
        self,
        prompts: List[str],
        model_type: str = "default",
        **kwargs,
    ) -> List[str]:
        """Fire all prompts simultaneously — keys and models rotate automatically."""
        log.info(f"batch_generate: {len(prompts)} prompts | type={model_type} | {len(self._keys)} keys")
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

    def provider_status(self) -> Dict[str, Any]:
        """Return current status of all keys across all model profiles."""
        status: Dict[str, Any] = {}
        all_models = {
            cfg["model"]
            for chain in MODEL_ROUTING.values()
            for cfg in chain
        }
        for i in range(len(self._keys)):
            key_id = f"key-{i}"
            key_status: Dict[str, str] = {}
            for model in sorted(all_models):
                rl_k = self._rl_key(key_id, model)
                if time.time() < self._rate_limited_until.get(rl_k, 0):
                    remaining = int(self._rate_limited_until[rl_k] - time.time())
                    key_status[model] = f"rate-limited ({remaining}s)"
                else:
                    key_status[model] = "ready"
            status[key_id] = key_status
        return status

    # ── Health check ──────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Test each key against the first model in the default chain."""
        results = {}
        test_model = MODEL_ROUTING["default"][0]
        test_messages = [{"role": "user", "content": "Hi"}]
        loop = asyncio.get_event_loop()

        for i, key in enumerate(self._keys):
            key_id = f"key-{i}"
            try:
                log.info(f"Health check: {key_id} → {test_model['model']}")
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, self._llm_call, key, test_model, test_messages, 50
                    ),
                    timeout=30,
                )
                results[key_id] = {"status": "ok", "model": test_model["model"], "response_len": len(result)}
                log.info(f"✅ {key_id} passed")
            except Exception as e:
                results[key_id] = {"status": "error", "model": test_model["model"], "error": str(e)[:100]}
                log.error(f"🔴 {key_id}: {e}")

        return results
