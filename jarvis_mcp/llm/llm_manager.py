"""
LLM Manager for JARVIS — NVIDIA-first multi-model with automatic fallback.

NVIDIA Model Chain (per call):
  1. nvidia-llama70b   meta/llama-3.3-70b-instruct        (12s — best reasoning)
  2. nvidia-nemotron   nvidia/llama-3.1-nemotron-70b-instruct      (15s — long context, text gen/summary)
  3. nvidia-8b         meta/llama-3.1-8b-instruct          (12s — fastest)
  4. groq              llama-3.3-70b-versatile             (30s — optional, if GROQ_API_KEY set)
  5. together          Llama-3.3-70B-Instruct-Turbo        (30s — optional, if TOGETHER_API_KEY set)

Model type routing:
  - default / reasoning → start from nvidia-llama70b (strongest)
  - text / summary      → start from nvidia-nemotron (long context, no hallucination)
  - fast / quick        → start from nvidia-8b (lowest latency)

Rules:
  - Timeout  → immediately try next provider (no waiting)
  - 429      → mark provider as rate-limited for 60s, try next
  - 401      → log error, skip provider (bad key)
  - optional providers (groq, together) → silently skipped if no key set
"""

import os
import json
import asyncio
import logging
import ssl
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Tuple

log = logging.getLogger(__name__)

# ── SSL context ───────────────────────────────────────────────────────────────
def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()

_SSL_CTX = _ssl_ctx()

# ── Provider definitions ──────────────────────────────────────────────────────
# optional=True → silently skipped if key not set (no error logged)
_PROVIDERS = [
    {
        "name":     "nvidia-llama70b",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env":  "NVIDIA_API_KEY",
        "optional": False,
        "models": {
            "default":   "meta/llama-3.3-70b-instruct",
            "reasoning": "meta/llama-3.3-70b-instruct",
            "text":      "meta/llama-3.3-70b-instruct",
            "summary":   "meta/llama-3.3-70b-instruct",
            "fast":      "stepfun-ai/step-3.5-flash",
            "quick":     "stepfun-ai/step-3.5-flash",
        },
        "timeout": 12,
    },
    {
        "name":     "nvidia-nemotron",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env":  "NVIDIA_API_KEY",
        "optional": False,
        # nemotron-3-nano-30b: long context, great for text gen / summary / rephrase
        # nemotron-70b: NVIDIA-tuned reasoning model for complex analysis
        "models": {
            "default":   "nvidia/nemotron-3-nano-30b-a3b",
            "reasoning": "nvidia/llama-3.1-nemotron-70b-instruct",
            "text":      "nvidia/nemotron-3-nano-30b-a3b",
            "summary":   "nvidia/nemotron-3-nano-30b-a3b",
            "fast":      "stepfun-ai/step-3.5-flash",
            "quick":     "stepfun-ai/step-3.5-flash",
        },
        "timeout": 20,
    },
    {
        "name":     "nvidia-flash",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env":  "NVIDIA_API_KEY",
        "optional": False,
        # step-3.5-flash: fast, low-latency — default for all fast/quick tasks
        "models": {
            "default":   "stepfun-ai/step-3.5-flash",
            "reasoning": "stepfun-ai/step-3.5-flash",
            "text":      "stepfun-ai/step-3.5-flash",
            "summary":   "stepfun-ai/step-3.5-flash",
            "fast":      "stepfun-ai/step-3.5-flash",
            "quick":     "stepfun-ai/step-3.5-flash",
        },
        "timeout": 10,
    },
    {
        "name":     "nvidia-8b",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env":  "NVIDIA_API_KEY",
        "optional": False,
        "models": {
            "default":   "meta/llama-3.1-8b-instruct",
            "reasoning": "meta/llama-3.1-8b-instruct",
            "text":      "meta/llama-3.1-8b-instruct",
            "summary":   "meta/llama-3.1-8b-instruct",
            "fast":      "meta/llama-3.1-8b-instruct",
            "quick":     "meta/llama-3.1-8b-instruct",
        },
        "timeout": 12,
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

# Provider order by model_type
# NVIDIA models first — groq/together are just safety nets if all NVIDIA is down
_ORDER_DEFAULT  = ["nvidia-llama70b", "nvidia-nemotron", "nvidia-flash", "nvidia-8b", "groq", "together"]
_ORDER_TEXT     = ["nvidia-nemotron",  "nvidia-llama70b", "nvidia-flash", "nvidia-8b", "groq", "together"]
_ORDER_FAST     = ["nvidia-flash",     "nvidia-8b", "nvidia-llama70b", "nvidia-nemotron", "groq", "together"]

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

    # ── Internal HTTP call (sync, runs in executor) ───────────────────────────

    def _http_call(self, base_url: str, api_key: str, model: str,
                   messages: list, max_tokens: int, temperature: float) -> str:
        url = f"{base_url}/chat/completions"
        payload = json.dumps({
            "model":       model,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temperature,
            "stream":      False,
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120, context=_SSL_CTX) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]

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
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._http_call,
                    provider["base_url"], api_key, model,
                    messages, max_tokens, temperature,
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

        except urllib.error.HTTPError as e:
            if e.code == 429:
                self._rate_limited_until[name] = time.time() + 60
                log.warning(f"🚫 {name} rate limited — cooling down 60s, switching provider")
                raise RuntimeError(f"{name} rate limited")
            if e.code == 401:
                log.error(f"🔑 {name} API key invalid — check {provider['key_env']}")
                raise RuntimeError(f"{name} auth failed")
            if e.code == 404:
                log.error(f"❌ {name} model '{model}' not found (404)")
                raise RuntimeError(f"{name} model not found")
            body = e.read().decode("utf-8") if e.fp else str(e)
            err_msg = body[:150] if body else f"HTTP {e.code}"
            log.error(f"❌ {name} HTTP {e.code}: {err_msg}")
            raise RuntimeError(f"{name} HTTP {e.code}")

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

        if model_type in ("fast", "quick"):
            order = _ORDER_FAST
        elif model_type in ("text", "summary"):
            order = _ORDER_TEXT
        else:
            order = _ORDER_DEFAULT

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

    # ── Parallel batch ────────────────────────────────────────────────────────

    async def batch_generate(
        self,
        prompts: List[str],
        model_type: str = "default",
        **kwargs,
    ) -> List[str]:
        """Run multiple prompts in parallel."""
        tasks = [self.generate(p, model_type=model_type, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)

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
