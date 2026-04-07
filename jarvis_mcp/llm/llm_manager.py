"""
LLM Manager for JARVIS — Swarm routing with NVIDIA key-pool rotation.

Architecture: Swarm race (not sequential failover)
  For each generate() call, all available (model, key) workers fire in parallel.
  The first worker to return a valid response wins — all others are cancelled.
  This means rate-limits on one model never block another model from responding.

Key pool:
  NVIDIA_API_KEY, NVIDIA_API_KEY_2 ... NVIDIA_API_KEY_N (up to 20)
  Round-robin key selection distributes load across parallel section calls.

Model types:
  synthesis  — 1M context: intelligence_brief synthesis (Nemotron 120B only, single call)
  reasoning  — deep analysis: MEDDPICC, risk, competitive, value architecture
  writing    — long-form: proposals, SOW, battlecards, documentation
  fast       — quick tasks: summaries, insights, follow-ups, meeting prep
  autonomous — background queue worker tasks
  default    — general purpose fallback

Swarm behaviour:
  1. Build worker list: one (model, key) per model in chain — best available key,
     skip entirely if all keys for that model are rate-limited.
  2. Fire all workers simultaneously.
  3. First valid response wins — cancel remaining tasks.
  4. If all fail with only rate-limits → wait for soonest cooldown → retry.
  5. If any hard error (auth/connection) → return error immediately.
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

# Strip thinking blocks that models emit inline in the content stream.
# Handles: <think>, <thinking>, unclosed blocks (truncated responses).
_THINK_RE         = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK_RE = re.compile(r"<think(?:ing)?>.*$",                re.DOTALL | re.IGNORECASE)

class _EmptyResponseError(Exception):
    """Raised when a model returns a successful but empty response."""

def _strip_thinking(text: str) -> str:
    """
    Remove all thinking/reasoning blocks from model output:
      1. Complete  <think>...</think>  and  <thinking>...</thinking>  blocks
      2. Unclosed  <think>...  blocks (response truncated mid-think)
    """
    text = _THINK_RE.sub("", text)          # complete blocks
    text = _UNCLOSED_THINK_RE.sub("", text) # unclosed / truncated blocks
    return text.lstrip("\n").strip()

# ── Model routing table ───────────────────────────────────────────────────────
# Each entry: model id, params, has_thinking (streams reasoning_content — we discard it)
# Order = preference for swarm race (first in list gets best available key).
# All models in the list fire simultaneously — first valid response wins.

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
        # Swarm: kimi + qwq fire simultaneously — first valid response wins.
        # Skills: MEDDPICC, risk_report, battlecard, competitive_intel, value_arch, technical_risk
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
        {"model": "qwen/qwq-32b",                "temperature": 0.6, "top_p": 0.7, "has_thinking": False},
    ],
    "writing": [
        # Swarm: kimi-instruct preferred (fast, clean prose), qwq as parallel fallback.
        # Skills: proposals, SOW, documentation, battlecards
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.6, "top_p": 0.9, "has_thinking": False},
        {"model": "qwen/qwq-32b",                "temperature": 0.6, "top_p": 0.7, "has_thinking": False},
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
    ],
    "fast": [
        # Swarm: kimi-instruct + qwen2-7b fire simultaneously.
        # Skills: quick insights, follow-up emails, meeting prep, summaries
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.6, "top_p": 0.9, "has_thinking": False},
        {"model": "qwen/qwen2-7b-instruct",      "temperature": 0.7, "top_p": 0.8, "has_thinking": False},
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
    ],
    "default": [
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.6, "top_p": 0.9, "has_thinking": False},
        {"model": "moonshotai/kimi-k2-thinking", "temperature": 1,   "top_p": 0.9, "has_thinking": True},
        {"model": "qwen/qwq-32b",                "temperature": 0.6, "top_p": 0.7, "has_thinking": False},
    ],
    "autonomous": [
        # Background queue worker — kimi-instruct is fast and reliable
        {"model": "moonshotai/kimi-k2-instruct", "temperature": 0.3, "top_p": 0.9, "has_thinking": False},
        {"model": "qwen/qwq-32b",                "temperature": 0.3, "top_p": 0.7, "has_thinking": False},
    ],
}


class LLMManager:
    """
    NVIDIA key-pool LLM manager with swarm race routing.

    Swarm race:
      All models in the chain fire simultaneously (one best-available key each).
      First valid response wins — all others are cancelled.
      Rate-limits on one model never block another model from running.
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
        log.warning(f"🚫 [{key_id}] [{model}] rate-limited for {cooldown}s")

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

    # ── Swarm worker helpers ──────────────────────────────────────────────────

    def _build_swarm(self, model_chain: List[Dict]) -> List[Tuple[Dict, str, str]]:
        """
        Build the swarm worker list for a race.

        Returns one (model_cfg, api_key, key_id) per model in the chain,
        using the best available (non-rate-limited) key for each model.
        Models where ALL keys are rate-limited are excluded from the swarm.
        """
        swarm = []
        for model_cfg in model_chain:
            key, key_id = self._next_key_for_model(model_cfg["model"])
            if key is None:
                continue
            if not self._is_available(key_id, model_cfg["model"]):
                # All keys for this model are rate-limited — skip it
                continue
            swarm.append((model_cfg, key, key_id))
        return swarm

    def _soonest_available_wait(self, model_chain: List[Dict]) -> float:
        """Seconds until the soonest rate-limited worker becomes available."""
        now = time.time()
        soonest = min(
            (self._rate_limited_until.get(self._rl_key(f"key-{i}", cfg["model"]), 0)
             for i in range(len(self._keys))
             for cfg in model_chain),
            default=0,
        )
        return max(soonest - now + 1, 5)  # at least 5s buffer

    async def _run_worker(
        self,
        model_cfg: Dict,
        api_key: str,
        key_id: str,
        messages: list,
        max_tokens: int,
        loop: asyncio.AbstractEventLoop,
    ) -> str:
        """
        Run one swarm worker: single (model, key) attempt.
        Handles rate-limit marking and logging. Re-raises all exceptions
        so the swarm coordinator can decide what to do.
        """
        model_name = model_cfg["model"]
        call_timeout = model_cfg.get("timeout", _TIMEOUT)

        log.info(f"🐝 [{key_id}] [{model_name}] launching")
        t0 = time.time()

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
            raise

        except RateLimitError:
            self._mark_rate_limited(key_id, model_name)
            raise

        except APIConnectionError as e:
            log.error(f"❌ [{key_id}] [{model_name}] connection failed: {str(e)[:80]}")
            raise

        except APIError as e:
            msg = str(e)
            if "401" in msg or "Unauthorized" in msg:
                log.error(f"🔑 [{key_id}] [{model_name}] invalid API key")
            elif "404" in msg or "not found" in msg.lower():
                log.warning(f"⚠️ [{key_id}] [{model_name}] model unavailable")
            else:
                log.error(f"❌ [{key_id}] [{model_name}] API error: {msg[:80]}")
            raise

        except Exception as e:
            log.warning(f"⚠️ [{key_id}] [{model_name}] failed: {str(e)[:100]}")
            raise

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
            final = _strip_thinking("".join(result))
            if not final:
                raise _EmptyResponseError(f"empty stream from {model_cfg['model']}")
            return final

        except _EmptyResponseError:
            raise ValueError(f"LLM returned empty content for {model_cfg['model']}")

        except Exception as e:
            log.debug(f"Streaming failed ({model_cfg['model']}): {e} — retrying without stream")
            params["stream"] = False
            completion = client.chat.completions.create(**params)
            if not completion.choices:
                raise ValueError(f"LLM returned empty choices for {model_cfg['model']}")
            content = completion.choices[0].message.content
            if not content:
                raise ValueError(f"LLM returned None content for {model_cfg['model']}")
            final = _strip_thinking(content)
            if not final:
                raise ValueError(f"LLM returned empty content after stripping for {model_cfg['model']}")
            return final

    # ── Main generate — swarm race ────────────────────────────────────────────

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

        model_chain = MODEL_ROUTING.get(model_type) or MODEL_ROUTING["default"]
        loop = asyncio.get_event_loop()

        attempt_num = 0
        while True:
            attempt_num += 1

            # Build swarm: one available (model, key) worker per model in chain.
            # Models where all keys are rate-limited are excluded.
            swarm = self._build_swarm(model_chain)

            if not swarm:
                # Every model's keys are rate-limited — wait for soonest
                wait = self._soonest_available_wait(model_chain)
                log.warning(
                    f"All workers rate-limited (attempt {attempt_num}) — "
                    f"waiting {wait:.0f}s for cooldown…"
                )
                await asyncio.sleep(wait)
                continue

            model_labels = [
                f"[{kid}]{mc['model'].split('/')[-1]}"
                for mc, _, kid in swarm
            ]
            log.info(
                f"🐝 Swarm [{model_type}]: {len(swarm)} workers racing — "
                + ", ".join(model_labels)
            )

            # Fire all swarm workers simultaneously
            task_meta: Dict[asyncio.Task, Tuple[Dict, str]] = {}
            for mc, k, kid in swarm:
                t = asyncio.create_task(
                    self._run_worker(mc, k, kid, messages, max_tokens, loop)
                )
                task_meta[t] = (mc, kid)

            pending = set(task_meta.keys())
            errors: List[str] = []
            has_hard_error = False

            while pending:
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    try:
                        result = task.result()
                        # Winner — cancel remaining in-flight tasks
                        for t in pending:
                            t.cancel()
                        mc, kid = task_meta[task]
                        log.info(
                            f"🏁 [{kid}] [{mc['model']}] won the swarm race "
                            f"(type={model_type})"
                        )
                        return result

                    except asyncio.CancelledError:
                        pass  # expected: cancelled loser tasks

                    except RateLimitError as e:
                        mc, kid = task_meta[task]
                        errors.append(f"[{kid}][{mc['model']}]: rate-limited")
                        # has_hard_error stays False — rate limits are retryable

                    except Exception as e:
                        mc, kid = task_meta[task]
                        errors.append(f"[{kid}][{mc['model']}]: {str(e)[:60]}")
                        has_hard_error = True

            # All swarm workers finished without a valid response.
            if has_hard_error:
                break  # hard errors (auth, connection, empty) — don't retry

            # Only rate limits — wait for soonest key to free up, then retry
            wait = self._soonest_available_wait(model_chain)
            log.warning(
                f"Swarm rate-limited (attempt {attempt_num}) — "
                f"waiting {wait:.0f}s…"
            )
            await asyncio.sleep(wait)

        error_detail = " || ".join(errors)
        log.error(f"Swarm failed [{model_type}]: {error_detail}")
        return f"❌ All swarm workers failed for '{model_type}': {error_detail}"

    # ── Parallel batch ────────────────────────────────────────────────────────

    async def batch_generate(
        self,
        prompts: List[str],
        model_type: str = "default",
        **kwargs,
    ) -> List[str]:
        """Fire all prompts simultaneously — each prompt runs its own swarm race."""
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
