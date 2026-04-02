"""
LLM Manager for JARVIS — nemotron with thinking mode for all tasks.

Primary model: nvidia/nemotron-3-nano-30b-a3b
  - reasoning_budget: 16384 (full thinking)
  - chat_template_kwargs: {"enable_thinking": true}
  - stream: true, temperature: 1, top_p: 1, max_tokens: 16384

Used for BOTH text generation and reasoning tasks.
Fallback: groq → together (optional, if keys set).

Parallel: batch_generate fires ALL prompts simultaneously via asyncio.gather.
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI, APIConnectionError, RateLimitError, APIError

log = logging.getLogger(__name__)

# ── Provider definitions ──────────────────────────────────────────────────────
# optional=True → silently skipped if key not set (no error logged)
_PROVIDERS = [
    {
        "name":     "nvidia-nemotron",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env":  "NVIDIA_API_KEY",
        "optional": False,
        "models": {
            "default":   "nvidia/nemotron-3-nano-30b-a3b",
            "reasoning": "nvidia/nemotron-3-nano-30b-a3b",
            "text":      "nvidia/nemotron-3-nano-30b-a3b",
            "summary":   "nvidia/nemotron-3-nano-30b-a3b",
            "fast":      "nvidia/nemotron-3-nano-30b-a3b",
            "quick":     "nvidia/nemotron-3-nano-30b-a3b",
        },
        "timeout": 60,  # thinking mode needs more time
    },
    {
        "name":     "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "key_env":  "GROQ_API_KEY",
        "optional": True,   # skipped silently if no GROQ_API_KEY
        "models": {
            "default":   "llama-3.3-70b-versatile",
            "reasoning": "llama-3.3-70b-versatile",
            "text":      "llama-3.3-70b-versatile",
            "summary":   "llama-3.3-70b-versatile",
            "fast":      "llama-3.1-8b-instant",
            "quick":     "llama-3.1-8b-instant",
        },
        "timeout": 30,
    },
    {
        "name":     "together",
        "base_url": "https://api.together.xyz/v1",
        "key_env":  "TOGETHER_API_KEY",
        "optional": True,   # skipped silently if no TOGETHER_API_KEY
        "models": {
            "default":   "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "reasoning": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "text":      "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "summary":   "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "fast":      "meta-llama/Llama-3.1-8B-Instruct-Turbo",
            "quick":     "meta-llama/Llama-3.1-8B-Instruct-Turbo",
        },
        "timeout": 30,
    },
]

# nemotron for everything — groq/together as fallback only
_ORDER_TEXT      = ["nvidia-nemotron", "groq", "together"]
_ORDER_REASONING = ["nvidia-nemotron", "groq", "together"]

_PROVIDER_MAP = {p["name"]: p for p in _PROVIDERS}


class LLMManager:
    """NVIDIA-first multi-model LLM manager with automatic timeout/rate-limit fallback."""

    def __init__(self, config):
        self.config = config
        # Rate-limit cooldown: {provider_name: until_timestamp}
        self._rate_limited_until: Dict[str, float] = {}
        # Cache resolved API keys
        self._keys: Dict[str, str] = {}
        for p in _PROVIDERS:
            self._keys[p["name"]] = os.getenv(p["key_env"], "")

        # Warn if NVIDIA key missing (required)
        if not self._keys.get("nvidia-llama70b"):
            log.warning("NVIDIA_API_KEY not set — add to .env and restart Claude Desktop.")

        # Info log which optional providers are active
        for name in ("groq", "together"):
            if self._keys.get(name):
                log.info(f"Optional provider '{name}' is active (key found).")

    # ── Internal LLM call (sync, runs in executor) using OpenAI SDK ───────────

    def _llm_call(self, base_url: str, api_key: str, model: str,
                  messages: list, max_tokens: int, temperature: float,
                  is_reasoning: bool = False) -> str:
        """Call NVIDIA LLM via OpenAI SDK with streaming."""
        client = OpenAI(base_url=base_url, api_key=api_key)

        # Build request params — exact working config for nemotron thinking mode
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 1,
            "top_p": 1,
            "stream": True,
        }

        # Enable thinking mode for nemotron
        if "nemotron" in model.lower():
            params["reasoning_budget"] = 16384
            params["chat_template_kwargs"] = {"enable_thinking": True}

        # Stream and collect response
        result = []
        try:
            completion = client.chat.completions.create(**params)
            for chunk in completion:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
                # Extract reasoning if present
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    result.append(reasoning)
                # Extract content
                content = getattr(chunk.choices[0].delta, "content", None)
                if content:
                    result.append(content)
            return "".join(result)
        except Exception as e:
            log.debug(f"Streaming failed: {e}, retrying without stream")
            params["stream"] = False
            completion = client.chat.completions.create(**params)
            return completion.choices[0].message.content

    # ── Try one provider ──────────────────────────────────────────────────────

    async def _try_provider(self, provider: dict, model_type: str,
                             messages: list, max_tokens: int,
                             temperature: float) -> Tuple[str, str]:
        """
        Try a single provider. Returns (result, provider_name).
        Raises:
          - asyncio.TimeoutError  → caller should try next
          - RuntimeError("skip")  → optional provider has no key, skip silently
          - RuntimeError(...)     → rate limit / auth / HTTP error
        """
        name    = provider["name"]
        api_key = self._keys.get(name, "")

        # Optional providers: skip silently if key not set
        if not api_key:
            if provider.get("optional"):
                raise RuntimeError(f"skip:{name}")
            raise RuntimeError(f"No API key for {name} — add {provider['key_env']} to .env")

        # Rate-limit cooldown
        cooldown = self._rate_limited_until.get(name, 0)
        if time.time() < cooldown:
            remaining = int(cooldown - time.time())
            raise RuntimeError(f"{name} rate-limited for {remaining}s more")

        model   = provider["models"].get(model_type, provider["models"]["default"])
        timeout = provider["timeout"]

        log.info(f"LLM → {name} | {model} | {model_type} | {max_tokens}tok | timeout={timeout}s")
        t0 = time.time()

        loop = asyncio.get_event_loop()
        is_reasoning = model_type in ("default", "reasoning")
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._llm_call,
                    provider["base_url"], api_key, model,
                    messages, max_tokens, temperature,
                    is_reasoning,
                ),
                timeout=timeout,
            )
            elapsed = round(time.time() - t0, 1)
            log.info(f"✅ {name} responded in {elapsed}s")
            return result, name

        except asyncio.TimeoutError:
            elapsed = round(time.time() - t0, 1)
            log.warning(f"⏱ {name} timed out after {elapsed}s — switching provider")
            raise

        except RateLimitError:
            self._rate_limited_until[name] = time.time() + 60
            log.warning(f"🚫 {name} rate limited — cooling down 60s, switching provider")
            raise RuntimeError(f"{name} rate limited")

        except APIConnectionError as e:
            log.error(f"❌ {name} connection failed: {str(e)[:100]}")
            raise RuntimeError(f"{name} connection error")

        except APIError as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                log.error(f"🔑 {name} API key invalid — check {provider['key_env']}")
                raise RuntimeError(f"{name} auth failed")
            if "404" in error_msg or "not found" in error_msg.lower():
                log.error(f"❌ {name} model '{model}' not found")
                raise RuntimeError(f"{name} model not found")
            log.error(f"❌ {name} API error: {error_msg[:100]}")
            raise RuntimeError(f"{name} API error")

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

        # reasoning only → llama70b first; everything else → flash first
        if model_type == "reasoning":
            order = _ORDER_REASONING
        else:
            order = _ORDER_TEXT

        errors = []

        for provider_name in order:
            provider = _PROVIDER_MAP.get(provider_name)
            if not provider:
                continue
            try:
                result, used = await self._try_provider(
                    provider, model_type, messages, max_tokens, temperature
                )
                if used != order[0]:
                    log.info(f"ℹ️  Used fallback provider: {used}")
                return result

            except RuntimeError as e:
                err_str = str(e)
                if err_str.startswith("skip:"):
                    # Optional provider with no key — silently skip
                    continue
                errors.append(f"{provider_name}: {err_str}")
                continue

            except (asyncio.TimeoutError, Exception) as e:
                errors.append(f"{provider_name}: {e}")
                continue

        error_summary = " | ".join(errors)
        log.error(f"All providers failed: {error_summary}")
        return f"❌ All LLM providers unavailable: {error_summary}"

    # ── Parallel batch ─────────────────────────────────────────────────────────

    async def batch_generate(
        self,
        prompts: List[str],
        model_type: str = "default",
        **kwargs,
    ) -> List[str]:
        """Fire ALL prompts simultaneously in parallel — each gets its own LLM call."""
        log.info(f"batch_generate: {len(prompts)} prompts in parallel")
        tasks = [
            asyncio.ensure_future(self.generate(p, model_type=model_type, **kwargs))
            for p in prompts
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Replace any exception with an error string so callers don't crash
        return [
            r if not isinstance(r, Exception) else f"❌ Generation failed: {r}"
            for r in results
        ]

    # ── Status ────────────────────────────────────────────────────────────────

    def provider_status(self) -> Dict[str, str]:
        status = {}
        for p in _PROVIDERS:
            name = p["name"]
            key  = self._keys.get(name, "")
            if not key:
                status[name] = "no key (optional)" if p.get("optional") else "no key ⚠️"
            elif time.time() < self._rate_limited_until.get(name, 0):
                remaining = int(self._rate_limited_until[name] - time.time())
                status[name] = f"rate-limited ({remaining}s)"
            else:
                status[name] = "ready"
        return status

    # ── Health check ──────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Test each provider with a minimal request. Returns status for all models."""
        results = {}
        test_prompt = "Hi"
        test_messages = [{"role": "user", "content": test_prompt}]

        for p in _PROVIDERS:
            name = p["name"]
            key = self._keys.get(name, "")

            if not key:
                results[name] = {"status": "skip", "reason": "no api key"}
                continue

            # Test default model
            model = p["models"].get("default", "unknown")
            try:
                log.info(f"Health check: {name} + {model}")
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        self._http_call,
                        p["base_url"], key, model,
                        test_messages, 50, 0.7,
                    ),
                    timeout=p["timeout"],
                )
                results[name] = {
                    "status": "ok",
                    "model": model,
                    "response_len": len(result),
                }
                log.info(f"✅ {name} health check passed")
            except asyncio.TimeoutError:
                results[name] = {
                    "status": "timeout",
                    "model": model,
                    "timeout_s": p["timeout"],
                }
                log.warning(f"⏱ {name} timed out ({p['timeout']}s)")
            except urllib.error.HTTPError as e:
                results[name] = {
                    "status": "http_error",
                    "model": model,
                    "code": e.code,
                    "error": str(e)[:100],
                }
                log.error(f"🔴 {name} HTTP {e.code}")
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "model": model,
                    "error": str(e)[:100],
                }
                log.error(f"🔴 {name} error: {e}")

        return results
