"""LLM client for JARVIS natural conversation."""

import os
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from jarvis.utils.logger import JARVISLogger


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str = "openai"  # openai, anthropic, local, none
    api_key: str = ""
    model: str = "gpt-3.5-turbo"  # or gpt-4, claude-3-opus, etc.
    temperature: float = 0.7
    max_tokens: int = 500
    context_window: int = 4096
    base_url: Optional[str] = None  # For local/custom endpoints
    system_prompt: str = ""  # Optional custom system prompt


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
        """Check if the configuration is valid (API key, connectivity)."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self):
        self.logger = JARVISLogger("llm.openai")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI()
            except ImportError:
                self.logger.error("openai package not installed. Run: pip install openai")
                raise
        return self._client

    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        try:
            client = self._get_client()
            msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

            response = await client.chat.completions.create(
                model=config.model,
                messages=msg_dicts,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=30
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            self.logger.error("OpenAI generation failed", error=str(e))
            return f"[LLM Error: {str(e)}]"

    async def validate_config(self, config: LLMConfig) -> bool:
        if not config.api_key:
            self.logger.warning("No API key provided")
            return False
        try:
            client = self._get_client()
            # Simple test: list models (or just attempt a tiny completion)
            return True
        except Exception as e:
            self.logger.error("OpenAI config validation failed", error=str(e))
            return False


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self):
        self.logger = JARVISLogger("llm.anthropic")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic()
            except ImportError:
                self.logger.error("anthropic package not installed. Run: pip install anthropic")
                raise
        return self._client

    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        try:
            client = self._get_client()
            # Anthropic requires system message separate
            system_msg = next((m.content for m in messages if m.role == "system"), None)
            user_msgs = [m for m in messages if m.role != "system"]

            response = await client.messages.create(
                model=config.model,
                system=system_msg or config.system_prompt,
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
        if not config.api_key:
            self.logger.warning("No API key provided")
            return False
        # Could do a simple test call
        return True


class MockProvider(LLMProvider):
    """Mock provider for testing without API calls."""

    async def generate(self, messages: List[Message], config: LLMConfig) -> str:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[Mock LLM] You said: '{last_user[:50]}...' - Configure a real LLM provider for intelligent responses."

    async def validate_config(self, config: LLMConfig) -> bool:
        return True


class LLMManager:
    """Manages LLM provider selection and usage."""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock": MockProvider,
        "none": MockProvider,
    }

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = JARVISLogger("llm.manager")
        self._provider: Optional[LLMProvider] = None
        self._config: Optional[LLMConfig] = None

    def get_config(self) -> LLMConfig:
        """Read LLM configuration from main config."""
        cfg = self.config_manager.config
        llm_cfg = getattr(cfg, 'llm', {})
        return LLMConfig(
            provider=llm_cfg.get('provider', 'none'),
            api_key=llm_cfg.get('api_key', ''),
            model=llm_cfg.get('model', 'gpt-3.5-turbo'),
            temperature=llm_cfg.get('temperature', 0.7),
            max_tokens=llm_cfg.get('max_tokens', 500),
            context_window=llm_cfg.get('context_window', 4096),
            base_url=llm_cfg.get('base_url'),
            system_prompt=llm_cfg.get('system_prompt', '')
        )

    async def initialize(self) -> bool:
        """Initialize the configured LLM provider."""
        self._config = self.get_config()
        provider_class = self.PROVIDERS.get(self._config.provider, MockProvider)
        
        try:
            self._provider = provider_class()
            valid = await self._provider.validate_config(self._config)
            if valid:
                self.logger.info("LLM provider initialized", provider=self._config.provider, model=self._config.model)
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
        """Generate a response using the configured LLM."""
        if not self._provider:
            await self.initialize()
        return await self._provider.generate(messages, self._config)


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
        # Get current JARVIS state
        try:
            active_persona = "solution_consultant"
            try:
                import json
                with open('MEMORY/active_persona.json') as f:
                    data = json.load(f)
                    active_persona = data.get('current_persona', active_persona)
            except:
                pass

            # Build persona description
            persona_desc = {
                "solution_consultant": "You are a Solution Consultant focused on technical architecture, demos, and integration planning. You are analytical, detail-oriented, and help design solutions.",
                "account_executive": "You are an Account Executive focused on business development, negotiations, and deal strategy. You are persuasive, strategic, and relationship-focused."
            }.get(active_persona, "You are an AI assistant.")

            # Get workspace info
            workspace = self.config.config.workspace_root
            workspace_name = workspace.name if hasattr(workspace, 'name') else str(workspace)

            # Get patterns summary
            patterns_summary = "No patterns learned yet."
            try:
                patterns_file = Path('MEMORY/patterns') / f'{active_persona}_patterns.json'
                if patterns_file.exists():
                    import json
                    with open(patterns_file) as f:
                        data = json.load(f)
                        stats = data.get('statistics', {})
                        patterns_count = stats.get('patterns_discovered', 0)
                        files_observed = stats.get('total_files_observed', 0)
                        patterns_summary = f"Learned {patterns_count} patterns from {files_observed} files."
            except:
                pass

            # Get competitor info
            competitors_summary = "No competitors detected."
            try:
                comp_file = Path('MEMORY/competitor_mentions.json')
                if comp_file.exists():
                    import json
                    with open(comp_file) as f:
                        data = json.load(f)
                        mentions = data.get('mentions', [])
                        if mentions:
                            from collections import Counter
                            counts = Counter(m.get('competitor', 'unknown') for m in mentions)
                            top = counts.most_common(3)
                            competitors_summary = f"Competitors detected: {', '.join(c for c,_ in top)}"
            except:
                pass

            system_prompt = f"""You are JARVIS, an autonomous AI employee working in '{workspace_name}'.

Current Role: {active_persona.replace('_', ' ').title()}
{persona_desc}

Your Knowledge:
- {patterns_summary}
- {competitors_summary}

Your capabilities:
- Answer questions about your work, patterns, deals, and workspace
- Help with technical consulting, sales strategy, and deal management
- Trigger actions like /scan, /archive, /status
- Provide insights from your learned patterns

Persona: You are concise, direct, and professional. You speak like a highly capable assistant who is always watching and learning.

If a user asks to perform an action (like scanning, archiving, checking status, listing patterns or deals), provide a brief confirmation and execute via the appropriate internal command structure.

Respond in Markdown format when appropriate."""
            return system_prompt

        except Exception as e:
            self.logger.error("Error building system prompt", error=str(e))
            return "You are JARVIS, an AI assistant for OpenCode."
