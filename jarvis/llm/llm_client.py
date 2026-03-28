"""LLM client for JARVIS natural conversation."""

import os
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from jarvis.utils.logger import JARVISLogger


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str = "openai"  # openai, anthropic, nvidia, local, mock
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    top_p: Optional[float] = None  # Optional nucleus sampling
    max_tokens: int = 500
    context_window: int = 4096
    base_url: Optional[str] = None
    system_prompt_override: str = ""
    extra_body: Optional[Dict[str, Any]] = None  # Provider-specific additional fields
    task_type: str = "text"  # "text", "video", "audio"


@dataclass
class Message:
    """Single chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def validate_config(self, config: LLMConfig) -> bool:
        """Check if the configuration is valid."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (works with OpenAI, NVIDIA, local vLLM, Ollama, etc.)."""

    def __init__(self):
        self.logger = JARVISLogger("llm.openai")
        self._client = None
        self._last_base_url: Optional[str] = None

    def _get_client(self, config: LLMConfig):
        base_url = config.base_url or "https://api.openai.com/v1"
        # Recreate client if base_url changed (e.g., switching between NVIDIA text and video endpoints)
        if self._client is not None and self._last_base_url != base_url:
            self.logger.info("Base URL changed, recreating client", old=self._last_base_url, new=base_url)
            self._client = None

        if self._client is None:
            try:
                from openai import AsyncOpenAI
                # Get API key from config or environment (NVIDIA_API_KEY or OPENAI_API_KEY)
                api_key = config.api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
                if not api_key:
                    self.logger.error("No API key provided for LLM. Set api_key in config or NVIDIA_API_KEY env var.")
                    raise ValueError("Missing API key")
                self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                self._last_base_url = base_url
            except ImportError as e:
                self.logger.error("openai package not installed. Run: pip install openai")
                raise e
        return self._client

    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        try:
            client = self._get_client(config)
            msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

            # Build kwargs, including optional parameters
            kwargs = {
                "model": config.model,
                "messages": msg_dicts,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": 30,
            }
            # Add optional top_p if provided and not None
            if hasattr(config, 'top_p') and config.top_p is not None:
                kwargs["top_p"] = config.top_p
            # Add extra_body (for provider-specific fields like NVIDIA's chat_template_kwargs)
            if hasattr(config, 'extra_body') and config.extra_body:
                kwargs["extra_body"] = config.extra_body
            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}

            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            self.logger.error("OpenAI-compatible generation failed", error=str(e))
            return f"[LLM Error: {str(e)}]"

    async def validate_config(self, config: LLMConfig) -> bool:
        # For OpenAI-compatible endpoints, require either config.api_key or env var
        if not config.api_key and not os.getenv("OPENAI_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
            self.logger.warning("No API key provided")
            return False
        return True


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self):
        self.logger = JARVISLogger("llm.anthropic")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except ImportError:
                self.logger.error("anthropic package not installed. Run: pip install anthropic")
                raise
        return self._client

    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        try:
            client = self._get_client()
            system_msg = next((m.content for m in messages if m.role == "system"), None)
            user_msgs = [m for m in messages if m.role != "system"]

            response = await client.messages.create(
                model=config.model,
                system=system_msg or config.system_prompt_override,
                messages=[{"role": m.role, "content": m.content} for m in user_msgs],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=30
            )
            return response.content[0].text if response.content else ""
        except Exception as e:
            self.logger.error("Anthropic generation failed", error=str(e))
            return f"[LLM Error: {str(e)}]"

    async def validate_config(self, config: LLMConfig) -> bool:
        if not config.api_key and not os.getenv("ANTHROPIC_API_KEY"):
            self.logger.warning("No API key provided")
            return False
        return True


class MockProvider(LLMProvider):
    """Mock provider for testing."""

    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[Mock LLM] You said: '{last_user[:50]}...' \n\nPlease configure an LLM provider (OpenAI/Anthropic) in jarvis/config/jarvis.yaml for intelligent responses."

    async def validate_config(self, config: LLMConfig) -> bool:
        return True


class LLMManager:
    """Manages LLM provider selection with fallback chain."""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock": MockProvider,
        "none": MockProvider,
    }

    # Fallback models — NVIDIA only (background tasks should never use Claude tokens)
    FALLBACK_MODELS = [
        "nvidia/llama-3.3-nemotron-super-49b-v1",       # Primary
        "nvidia/llama-3.1-nemotron-ultra-253b-v1",      # Fallback 1
        "nvidia/mistral-nemo-minitron-8b-8k-instruct",  # Fallback 2
    ]

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = JARVISLogger("llm.manager")
        self._provider: Optional[LLMProvider] = None
        self._config: Optional[LLMConfig] = None
        self._fallback_configs: List[LLMConfig] = []
        self._active_model_index: int = 0
        self._video_config: Optional[LLMConfig] = None
        self._anthropic_fallback_config: Optional[LLMConfig] = None

    def get_config(self) -> LLMConfig:
        """Read LLM configuration from main config."""
        cfg = self.config_manager.config
        llm_cfg = getattr(cfg, 'llm', {})
        return LLMConfig(
            provider=llm_cfg.get('provider', 'none'),
            api_key=llm_cfg.get('api_key', ''),
            model=llm_cfg.get('model', 'gpt-3.5-turbo'),
            temperature=llm_cfg.get('temperature', 0.7),
            top_p=llm_cfg.get('top_p'),
            max_tokens=llm_cfg.get('max_tokens', 500),
            context_window=llm_cfg.get('context_window', 4096),
            base_url=llm_cfg.get('base_url'),
            system_prompt_override=llm_cfg.get('system_prompt', ''),
            extra_body=llm_cfg.get('extra_body'),
            task_type=llm_cfg.get('task_type', 'text')
        )

    def get_video_config(self) -> LLMConfig:
        """Read video LLM configuration from llm_video section in yaml config."""
        cfg = self.config_manager.config
        video_cfg = getattr(cfg, 'llm_video', {})
        if not video_cfg:
            # Sensible defaults for NVIDIA Cosmos video reasoning
            api_key = os.getenv("NVIDIA_API_KEY") or ""
            return LLMConfig(
                provider="openai",
                api_key=api_key,
                model="nvidia/cosmos-reason2-8b",
                temperature=0.5,
                max_tokens=1024,
                context_window=8192,
                base_url="https://integrate.api.nvidia.com/v1",
                task_type="video"
            )
        return LLMConfig(
            provider=video_cfg.get('provider', 'openai'),
            api_key=video_cfg.get('api_key', os.getenv("NVIDIA_API_KEY") or ''),
            model=video_cfg.get('model', 'nvidia/cosmos-reason2-8b'),
            temperature=video_cfg.get('temperature', 0.5),
            top_p=video_cfg.get('top_p'),
            max_tokens=video_cfg.get('max_tokens', 1024),
            context_window=video_cfg.get('context_window', 8192),
            base_url=video_cfg.get('base_url', 'https://integrate.api.nvidia.com/v1'),
            system_prompt_override=video_cfg.get('system_prompt', ''),
            extra_body=video_cfg.get('extra_body'),
            task_type="video"
        )

    def get_anthropic_fallback_config(self) -> LLMConfig:
        """Read Anthropic fallback configuration from llm_fallback section in yaml config."""
        cfg = self.config_manager.config
        fallback_cfg = getattr(cfg, 'llm_fallback', {})
        if not fallback_cfg:
            # Sensible defaults for Claude as final fallback
            api_key = os.getenv("ANTHROPIC_API_KEY") or ""
            return LLMConfig(
                provider="anthropic",
                api_key=api_key,
                model="claude-sonnet-4-20250514",
                temperature=0.7,
                max_tokens=500,
                context_window=200000,
                task_type="text"
            )
        return LLMConfig(
            provider=fallback_cfg.get('provider', 'anthropic'),
            api_key=fallback_cfg.get('api_key', os.getenv("ANTHROPIC_API_KEY") or ''),
            model=fallback_cfg.get('model', 'claude-sonnet-4-20250514'),
            temperature=fallback_cfg.get('temperature', 0.7),
            top_p=fallback_cfg.get('top_p'),
            max_tokens=fallback_cfg.get('max_tokens', 500),
            context_window=fallback_cfg.get('context_window', 200000),
            base_url=fallback_cfg.get('base_url'),
            system_prompt_override=fallback_cfg.get('system_prompt', ''),
            extra_body=fallback_cfg.get('extra_body'),
            task_type="text"
        )

    def _build_fallback_configs(self) -> List[LLMConfig]:
        """Build a list of fallback LLM configs — NVIDIA only, no Anthropic.
        Background tasks should never use Claude tokens."""
        primary = self._config
        configs = [primary]

        # Get API key and base_url from primary config
        api_key = primary.api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        base_url = primary.base_url or "https://integrate.api.nvidia.com/v1"

        # Add NVIDIA fallback models only (no Anthropic)
        for model in self.FALLBACK_MODELS:
            if model != primary.model:
                fallback = LLMConfig(
                    provider=primary.provider,
                    api_key=api_key,
                    model=model,
                    temperature=primary.temperature,
                    top_p=primary.top_p,
                    max_tokens=primary.max_tokens,
                    context_window=primary.context_window,
                    base_url=base_url,
                    system_prompt_override=primary.system_prompt_override,
                    extra_body=primary.extra_body,
                    task_type=primary.task_type
                )
                configs.append(fallback)

        return configs

    async def initialize(self) -> bool:
        """Initialize the configured LLM provider with fallback chain."""
        self._config = self.get_config()
        provider_class = self.PROVIDERS.get(self._config.provider, MockProvider)

        try:
            self._provider = provider_class()
            valid = await self._provider.validate_config(self._config)
            if valid:
                self.logger.info("LLM provider initialized", provider=self._config.provider, model=self._config.model)
                # Build fallback configs
                self._fallback_configs = self._build_fallback_configs()
                self.logger.info(f"Fallback chain: {[c.model for c in self._fallback_configs]}")
                # Load video and anthropic fallback configs
                self._video_config = self.get_video_config()
                self._anthropic_fallback_config = self.get_anthropic_fallback_config()
                self.logger.info(f"Video config: {self._video_config.model}, Anthropic fallback: {self._anthropic_fallback_config.model}")
                return True
            else:
                self.logger.warning("LLM provider config invalid, falling back to mock", provider=self._config.provider)
                self._provider = MockProvider()
                return False
        except Exception as e:
            self.logger.error("Failed to initialize LLM provider", error=str(e))
            self._provider = MockProvider()
            return False

    async def generate(self, messages: List[Message]) -> str:
        """Generate a response using the configured LLM with fallback chain.
        Backwards compatible — defaults to background NVIDIA only."""
        if not self._provider:
            await self.initialize()

        # If no fallback configs, use provider directly
        if not self._fallback_configs:
            return await self._provider.generate(messages, self._config)

        # Try each config in the fallback chain
        last_error = None
        for i, config in enumerate(self._fallback_configs):
            try:
                result = await self._provider.generate(messages, config)
                # Check if result indicates an error (e.g., 429 rate limit)
                if result.startswith("[LLM Error:"):
                    raise Exception(result)
                # Success! Log if we had to fallback
                if i > 0:
                    self.logger.info(f"LLM fallback successful", model=config.model, attempts=i+1)
                    self._active_model_index = i
                return result
            except Exception as e:
                last_error = e
                error_str = str(e)
                # Only fallback on rate limit (429) or model not found (404)
                if "429" in error_str or "Too Many Requests" in error_str:
                    self.logger.warning(f"Model {config.model} rate limited, trying next fallback", error=error_str)
                    continue
                elif "404" in error_str or "not found" in error_str.lower():
                    self.logger.warning(f"Model {config.model} not found, trying next fallback", error=error_str)
                    continue
                else:
                    # Non-retryable error, break immediately
                    self.logger.error(f"Non-retryable LLM error with {config.model}", error=error_str)
                    break

        # All fallbacks exhausted
        self.logger.error(f"All LLM models failed, last error: {last_error}")
        return f"[LLM Error: {last_error}]"

    async def generate_with_routing(self, messages: List[Message], task_type: str = "text", source: str = "background") -> str:
        """Generate a response with task-type routing and source-aware fallback.

        Args:
            messages: List of Message objects for the conversation.
            task_type: "text", "video", or "audio" — determines which config/model to use.
            source: "background" (never use Claude) or "user_request" (Claude as final fallback).

        Returns:
            Generated response string.
        """
        if not self._provider:
            await self.initialize()

        # --- Video task routing ---
        if task_type == "video":
            video_config = self._video_config or self.get_video_config()
            openai_provider = OpenAIProvider()
            try:
                result = await openai_provider.generate(messages, video_config)
                if not result.startswith("[LLM Error:"):
                    return result
                raise Exception(result)
            except Exception as e:
                self.logger.error(f"Video generation failed", model=video_config.model, error=str(e))
                return f"[LLM Error: Video generation failed: {str(e)}]"

        # --- Text (or audio) task routing ---
        # Build the NVIDIA-only fallback chain
        nvidia_configs = self._fallback_configs if self._fallback_configs else self._build_fallback_configs()

        last_error = None
        for i, config in enumerate(nvidia_configs):
            try:
                result = await self._provider.generate(messages, config)
                if result.startswith("[LLM Error:"):
                    raise Exception(result)
                if i > 0:
                    self.logger.info(f"Routed fallback successful", model=config.model, attempts=i+1, source=source)
                    self._active_model_index = i
                return result
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    self.logger.warning(f"Model {config.model} rate limited, trying next fallback", error=error_str)
                    continue
                elif "404" in error_str or "not found" in error_str.lower():
                    self.logger.warning(f"Model {config.model} not found, trying next fallback", error=error_str)
                    continue
                else:
                    self.logger.error(f"Non-retryable LLM error with {config.model}", error=error_str)
                    break

        # --- Claude as final fallback (only for user_request, never background) ---
        if source == "user_request":
            self.logger.warning("All NVIDIA models failed, falling back to Anthropic Claude for user request")
            anthropic_config = self._anthropic_fallback_config or self.get_anthropic_fallback_config()
            anthropic_provider = AnthropicProvider()
            try:
                result = await anthropic_provider.generate(messages, anthropic_config)
                if not result.startswith("[LLM Error:"):
                    self.logger.info(f"Anthropic fallback successful", model=anthropic_config.model)
                    return result
                raise Exception(result)
            except Exception as e:
                self.logger.error(f"Anthropic fallback also failed", error=str(e))
                last_error = e

        # All fallbacks exhausted
        self.logger.error(f"All LLM models failed (source={source}), last error: {last_error}")
        return f"[LLM Error: {last_error}]"


class ContextBuilder:
    """Builds conversation context from JARVIS knowledge base."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = JARVISLogger("llm.context")

    def build_context(self, user_message: str = "", conversation_history: List[Dict] = None) -> List[Message]:
        """Build a list of messages for LLM context."""
        messages = []

        # System prompt
        system_prompt = self._get_system_prompt()
        messages.append(Message(role="system", content=system_prompt))

        # Add conversation history (if provided)
        if conversation_history:
            for entry in conversation_history[-10:]:  # last 10 messages
                messages.append(Message(
                    role=entry.get("role", "user"),
                    content=entry.get("content", "")
                ))

        # Add current user message
        if user_message:
            messages.append(Message(role="user", content=user_message))

        return messages

    def _get_system_prompt(self) -> str:
        """Generate the system prompt for the LLM."""
        try:
            active_persona = "solution_consultant"
            try:
                with open('MEMORY/active_persona.json') as f:
                    data = json.load(f)
                    active_persona = data.get('current_persona', active_persona)
            except:
                pass

            persona_desc = {
                "solution_consultant": "You are a Solution Consultant focused on technical architecture, demos, and integration planning. You are analytical, detail-oriented, and help design solutions.",
                "account_executive": "You are an Account Executive focused on business development, negotiations, and deal strategy. You are persuasive, strategic, and relationship-focused."
            }.get(active_persona, "You are an AI assistant.")

            workspace = self.config.config.workspace_root
            workspace_name = workspace.name if hasattr(workspace, 'name') else str(workspace)

            # Gather rich workspace knowledge
            patterns_summary = "No patterns learned yet."
            recent_patterns = []
            try:
                patterns_file = Path('MEMORY/patterns') / f'{active_persona}_patterns.json'
                if patterns_file.exists():
                    with open(patterns_file) as f:
                        data = json.load(f)
                        stats = data.get('statistics', {})
                        patterns_count = stats.get('patterns_discovered', 0)
                        files_observed = stats.get('total_files_observed', 0)
                        patterns = data.get('interaction_patterns', {})
                        patterns_summary = f"Learned {patterns_count} patterns from {files_observed} files."
                        # Get top 5 recent patterns
                        for key in list(patterns.keys())[:5]:
                            count = patterns[key].get('count', 0) if isinstance(patterns[key], dict) else patterns[key]
                            recent_patterns.append(f"- {key} (observed {count} times)")
            except:
                pass

            competitors_summary = "No competitors detected."
            competitor_details = []
            try:
                # Check for detailed competitor profiles
                competitors_dir = Path('MEMORY/competitors')
                if competitors_dir.exists():
                    profile_files = list(competitors_dir.glob('*.json'))
                    if profile_files:
                        # Load top 3 competitors by mention count
                        profiles = []
                        for pf in profile_files:
                            try:
                                with open(pf) as f:
                                    prof = json.load(f)
                                    profiles.append(prof)
                            except:
                                continue

                        # Sort by mentions_count descending
                        profiles.sort(key=lambda x: x.get('mentions_count', 0), reverse=True)

                        for prof in profiles[:3]:
                            name = prof.get('name', 'Unknown')
                            mentions = prof.get('mentions_count', 0)
                            diff = prof.get('differentiators', [])[:2]  # top 2
                            weak = prof.get('their_weaknesses', [])[:2]  # top 2
                            detail_line = f"- **{name}** ({mentions} mentions)"
                            if diff:
                                detail_line += f"\n  • Advantages: {'; '.join(diff)}"
                            if weak:
                                detail_line += f"\n  • Weaknesses: {'; '.join(weak)}"
                            competitor_details.append(detail_line)

                        competitors_summary = f"Detailed intelligence on {len(profiles)} competitors."
            except:
                pass

            # Get active deals summary
            deals_summary = "No active deals."
            deals_info = []
            try:
                deals_file = Path('jarvis/data/personas/deals.json')
                if deals_file.exists():
                    with open(deals_file) as f:
                        data = json.load(f)
                        deals = data.get('deals', [])
                        if deals:
                            total_value = sum(d.get('budget', 0) for d in deals)
                            deals_summary = f"Managing {len(deals)} active deals with total value ${total_value:,}"
                            # Show top 3 deals by budget
                            sorted_deals = sorted(deals, key=lambda x: x.get('budget', 0), reverse=True)[:3]
                            for deal in sorted_deals:
                                deals_info.append(f"- {deal.get('title', 'Untitled')} ({deal.get('client', 'N/A')}): ${deal.get('budget', 0):,}")
            except:
                pass

            # Recent modifications/approvals
            changes_summary = "No recent approvals."
            try:
                changes_file = Path('MEMORY/approved_changes.json')
                if changes_file.exists():
                    with open(changes_file) as f:
                        data = json.load(f)
                        count = data.get('count', 0)
                        changes_summary = f"System has approved {count}/50 modifications autonomously."
            except:
                pass

            # Important notes/facts (from notes.json)
            notes_summary = "No critical notes."
            notes_details = []
            try:
                notes_file = Path('MEMORY/notes.json')
                if notes_file.exists():
                    with open(notes_file) as f:
                        notes_data = json.load(f)
                        # Get recent facts (last 5)
                        facts = notes_data.get('facts', [])
                        if facts:
                            for fact_entry in facts[-5:]:
                                content = fact_entry.get('content', '')
                                if content:
                                    notes_details.append(f"- {content}")
                            notes_summary = f"Recent facts ({len(facts)} total stored)"
            except:
                pass

            system_prompt = f"""You are JARVIS, an autonomous AI employee working in '{workspace_name}'.

Current Role: {active_persona.replace('_', ' ').title()}
{persona_desc}

Your Knowledge (Real-time workspace data):
*Workspace Overview:*
- {patterns_summary}
{chr(10).join(recent_patterns) if recent_patterns else ''}

*Competitor Intelligence:*
- {competitors_summary}
{chr(10).join(competitor_details) if competitor_details else ''}

*Active Deals:*
- {deals_summary}
{chr(10).join(deals_info) if deals_info else ''}

*System Status:*
- {changes_summary}

*Recent Critical Facts:*
- {notes_summary}
{chr(10).join(notes_details) if notes_details else ''}

*Your Capabilities:*
1. **Query Information**: Answer questions about deals, patterns, competitors, workspace activity
2. **Execute Commands**: Run /scan (analyze workspace), /archive (create snapshot), /status (system health)
3. **Manage Persona**: Switch between personas (solution_consultant, account_executive)
4. **Provide Insights**: Analyze patterns, suggest optimizations, identify opportunities
5. **Natural Conversation**: Contextual dialogue that remembers previous exchanges

*Important Notes:*
- You have access to the user's conversation history (last 10 messages)
- You respond in Markdown for formatting
- Be concise but informative
- If you need to perform an action, confirm it and note that it will be executed
- If you don't know something, say so honestly
- Remember context across messages - build on previous conversations
- When asked about a specific entity (company, product, deal), check your knowledge first before saying you don't know. The information may be in your notes or competitor intelligence.
- **If a competitor profile exists but lacks details** (no differentiators, weaknesses, or advantages mentioned), acknowledge the gap and **ask the user to provide key information** so you can build a complete battle card. For example: "I have ACME profiled as a competitor but I'm missing details on their strengths, weaknesses, and how we compete. Could you share what you know so I can build a complete battle card?"

*Tools:*
You have access to the following tools. To use one, output a line starting with `!` followed by the command.

**Workspace Commands** (execute in the local workspace):
```
! ls -la
! grep -r "pattern" path
! find . -name "*.py"
! cat filename
! head -n 50 file
! tail -n 50 file
! wc -l file
! pwd
! du -sh dir
! df -h
! file filename
! stat filename
```

**Web Search** (gather current info from the internet):
```
!web_search <query>
```
Example: `!web_search "Kambaa pricing for ACME"`

The command output will be returned to you. Use tools when:
- Internal knowledge is insufficient
- You need up-to-date information
- You need official docs or articles
- User asks for something you don't have in memory

Use relative paths from workspace root. Do not use `!` in normal conversation.

Now, respond to the user's message naturally and intelligently based on your knowledge and their conversation history."""
            return system_prompt

        except Exception as e:
            self.logger.error("Error building system prompt", error=str(e))
            return "You are JARVIS, an AI assistant for OpenCode."
