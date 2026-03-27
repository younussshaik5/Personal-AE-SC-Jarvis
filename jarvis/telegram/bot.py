#!/usr/bin/env python3
"""
Telegram Bot Interface - Full two-way chat with JARVIS AI.

This bot allows you to:
- Chat naturally with JARVIS about your work
- Issue commands to trigger actions (scan, archive, status, etc.)
- Query information (deals, patterns, persona status)
- Receive AI-powered responses based on your workspace context
"""

import asyncio
import json
import logging
import datetime
import re
import shlex
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
from pathlib import Path

# Check for python-telegram-bot availability
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Create dummy types for type checking when library is missing
    if TYPE_CHECKING:
        from telegram import Update, Bot
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    else:
        # At runtime, define minimal stubs
        class Update: pass
        class Bot: pass
        class Application: pass
        class CommandHandler: pass
        class MessageHandler: pass
        class ContextTypes: pass
        def filters(*args, **kwargs): return None

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.config import ConfigManager
from jarvis.llm.llm_client import LLMManager, ContextBuilder
from jarvis.tools.executor import ToolExecutor


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: str
    allowed_user_ids: List[int]  # Security: only these users can interact
    channel_id: Optional[str] = None  # Optional channel for broadcasts
    enabled: bool = True
    command_prefix: str = "/"
    # Feature toggles
    allow_conversational_chat: bool = True
    allow_commands: bool = True
    broadcast_events: bool = True
    # Rate limiting
    max_messages_per_minute: int = 30
    # Event subscriptions (which events to broadcast to Telegram)
    notify_persona_switch: bool = True
    notify_modification_approved: bool = True
    notify_errors: bool = True
    notify_patterns: bool = False
    notify_competitors: bool = True


class TelegramBotBridge:
    """
    Bridge between Telegram and JARVIS core.
    
    Architecture:
    1. Telegram messages → EventBus (telegram.message event)
    2. JARVIS processes → Publishes responses (telegram.response event)
    3. Bridge sends responses back to Telegram user
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("telegram_bot")
        self.config: Optional[TelegramConfig] = None
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self._running = False
        self._response_handlers: List[asyncio.Task] = []
        
        # Conversation context per user
        self._conversation_context: Dict[int, Dict[str, Any]] = {}
        
        # LLM components
        self.llm_manager = LLMManager(config_manager)
        self.context_builder = ContextBuilder(config_manager)
        
        # Load config first
        self._load_config()
        
        # Tool executor for workspace commands (after config for web_search)
        self.tool_executor = ToolExecutor(Path(config_manager.config.workspace_root))
        # Configure web search settings
        web_cfg = getattr(self.config_manager.config, 'web_search', {})
        if web_cfg.get('enabled', True):
            self.tool_executor.config_engine = web_cfg.get('engine', 'duckduckgo')
            self.tool_executor.config_max_results = web_cfg.get('max_results', 5)
            self.tool_executor.config_timeout = web_cfg.get('timeout', 10)
        
        if self.config and TELEGRAM_AVAILABLE:
            self._setup_handlers()

    def _load_config(self):
        """Load Telegram configuration from jarvis.yaml."""
        try:
            tg_cfg = getattr(self.config_manager.config, 'telegram', {})
            if not tg_cfg or not tg_cfg.get('enabled'):
                self.logger.info("Telegram bot disabled in config")
                return
                
            # Validate required fields
            if not tg_cfg.get('bot_token'):
                self.logger.error("Telegram bot_token missing, disabling")
                return
                
            self.config = TelegramConfig(
                bot_token=tg_cfg['bot_token'],
                allowed_user_ids=tg_cfg.get('allowed_user_ids', []),
                channel_id=tg_cfg.get('channel_id'),
                enabled=tg_cfg.get('enabled', True),
                command_prefix=tg_cfg.get('command_prefix', '/'),
                allow_conversational_chat=tg_cfg.get('allow_conversational_chat', True),
                allow_commands=tg_cfg.get('allow_commands', True),
                broadcast_events=tg_cfg.get('broadcast_events', True),
                max_messages_per_minute=tg_cfg.get('max_messages_per_minute', 30),
                notify_persona_switch=tg_cfg.get('notify_persona_switch', True),
                notify_modification_approved=tg_cfg.get('notify_modification_approved', True),
                notify_errors=tg_cfg.get('notify_errors', True),
                notify_patterns=tg_cfg.get('notify_patterns', False),
                notify_competitors=tg_cfg.get('notify_competitors', True)
            )
            self.logger.info("Telegram bot configured", 
                           allowed_users=len(self.config.allowed_user_ids))
        except Exception as e:
            self.logger.error("Failed to load Telegram config", error=str(e))

    def _setup_handlers(self):
        """Setup command and message handlers (python-telegram-bot)."""
        if not TELEGRAM_AVAILABLE:
            self.logger.warning("python-telegram-bot not installed, using raw API fallback")
            return
            
        # These will be set when we create the application
        self._command_handlers = {}
        self._message_handler = None

    async def start(self):
        """Start the Telegram bot."""
        if not self.config or not self.config.enabled:
            self.logger.info("Telegram bot not configured, skipping start")
            return
            
        if not TELEGRAM_AVAILABLE:
            self.logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
            self.logger.warning("Telegram bot will be disabled. To enable, install the dependency.")
            return
            
        self.logger.info("Starting Telegram bot")
        
        try:
            # Create bot and application
            self.bot = Bot(token=self.config.bot_token)
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # Register command handlers
            commands = [
                ('status', self._cmd_status),
                ('persona', self._cmd_persona),
                ('deals', self._cmd_deals),
                ('patterns', self._cmd_patterns),
                ('competitors', self._cmd_competitors),
                ('scan', self._cmd_scan),
                ('archive', self._cmd_archive),
                ('help', self._cmd_help),
                ('start', self._cmd_start),
            ]
            
            for cmd, handler in commands:
                self.application.add_handler(CommandHandler(cmd, handler))
            
            # Register message handler for natural language chat
            if self.config.allow_conversational_chat:
                self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            # Start bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            self._running = True
            self.logger.info("Telegram bot started and polling")
            
            # Subscribe to event bus for broadcasts
            if self.config.broadcast_events:
                self.event_bus.subscribe_all(self._handle_system_event)
                
        except Exception as e:
            self.logger.error("Failed to start Telegram bot", error=str(e))

    async def stop(self):
        """Stop the Telegram bot."""
        self._running = False
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        self.logger.info("Telegram bot stopped")

    def _check_authorization(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot."""
        if not self.config:
            return False
        if not self.config.allowed_user_ids:
            # If no list specified, allow all (not recommended for production)
            return True
        return user_id in self.config.allowed_user_ids

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages (natural language)."""
        user_id = update.effective_user.id
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized user.")
            return
            
        message_text = update.message.text
        self.logger.info("Received Telegram message", user_id=user_id, message=message_text[:50])
        
        # Publish to event bus for JARVIS to process
        event = Event("telegram.message", "telegram_bot", {
            "user_id": user_id,
            "username": update.effective_user.username,
            "message": message_text,
            "chat_type": update.effective_chat.type,
            "reply_to_message_id": update.message.reply_to_message.message_id if update.message.reply_to_message else None
        })
        self.event_bus.publish(event)
        
        # Send typing action to show bot is working
        try:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        except:
            pass
        
        # For immediate response, we'll process via AI agent
        response = await self._process_with_jarvis(message_text, user_id)
        if response:
            # Publish response event for conversation learner
            response_event = Event("telegram.response", "telegram_bot", {
                "user_id": user_id,
                "response": response,
                "original_message": message_text
            })
            self.event_bus.publish(response_event)
            
            # Split long responses to stay under Telegram's 4096 character limit
            await self._send_long_message(update, response, parse_mode='Markdown')

    async def _reply_and_publish(self, update: Update, response: str, command: str):
        """Helper to send reply and publish response event."""
        if response:
            # Publish response event
            event = Event("telegram.response", "telegram_bot", {
                "user_id": update.effective_user.id,
                "response": response,
                "command": command
            })
            self.event_bus.publish(event)
            
            await update.message.reply_text(response, parse_mode='Markdown')

    async def _send_long_message(self, update: Update, text: str, parse_mode: str = None, chunk_size: int = 4000):
        """Send a long message by splitting it into multiple parts if needed."""
        if TELEGRAM_AVAILABLE and len(text) > chunk_size:
            # Split into chunks, respecting line boundaries if possible
            parts = []
            while text:
                if len(text) <= chunk_size:
                    parts.append(text)
                    break
                # Try to split at a newline near the chunk boundary
                split_pos = text[:chunk_size].rfind('\n')
                if split_pos == -1 or split_pos < chunk_size // 2:
                    split_pos = chunk_size
                parts.append(text[:split_pos])
                text = text[split_pos:].lstrip()
            
            # Send first part as reply, subsequent parts as new messages
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(part, parse_mode=parse_mode)
                else:
                    await update.message.reply_text(part, parse_mode=parse_mode)
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
        else:
            await update.message.reply_text(text, parse_mode=parse_mode)

    async def _process_with_jarvis(self, message: str, user_id: int) -> str:
        """
        Process message through JARVIS AI brain.
        Intelligent routing using LLM to understand intent.
        """
        self.logger.info("Processing message", user_id=user_id, message_preview=message[:50])
        
        # Load or create conversation memory
        memory = self._load_user_memory(user_id)
        
        try:
            # Use LLM to understand intent and generate appropriate response
            response = await self._generate_intelligent_response(message, memory)
            
            # Update conversation history
            self._update_memory(user_id, message, response)
            
            self.logger.info("Generated response", response_preview=response[:200])
            return response
            
        except Exception as e:
            self.logger.error("Error processing message", error=str(e))
            return f"❌ Error: {str(e)}"

    def _load_user_memory(self, user_id: int) -> Dict:
        """Load conversation memory for user from file."""
        memory_file = Path(f'MEMORY/conversations/{user_id}.json')
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    return json.load(f)
            except:
                pass
        return {"history": [], "last_command": None, "preferences": {}}

    def _update_memory(self, user_id: int, user_message: str, assistant_response: str):
        """Update user conversation memory."""
        memory = self._load_user_memory(user_id)
        
        # Add to history (keep last 20 messages for context)
        memory['history'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.datetime.now().isoformat()
        })
        memory['history'].append({
            'role': 'assistant',
            'content': assistant_response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Keep only last 20 exchanges (40 messages)
        memory['history'] = memory['history'][-40:]
        
        # Save
        memory_file = Path(f'MEMORY/conversations/{user_id}.json')
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)

    def _extract_tool_command(self, text: str) -> Optional[str]:
        """Extract a tool command from LLM response (lines starting with '!')."""
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('!') and len(line) > 1:
                # Return the command without the '!'
                return line[1:].strip()
        return None

    def _extract_toolcall_xml(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a toolcall from LLM response (XML format)."""
        # Match <toolcall><invoke name="tool">...</invoke></toolcall>
        pattern = r'<toolcall>\s*<invoke name="([^"]+)".*?>(.*?)</invoke>\s*</toolcall>'
        m = re.search(pattern, text, re.DOTALL)
        if not m:
            return None
        tool = m.group(1)
        params_text = m.group(2)
        # Extract parameters as <param name="...">value</param>
        params = {}
        param_pattern = r'<param name="([^"]+)">(.*?)</param>'
        for pm in re.finditer(param_pattern, params_text, re.DOTALL):
            name = pm.group(1)
            value = pm.group(2).strip()
            params[name] = value
        return {"tool": tool, "params": params}

    async def _generate_intelligent_response(self, message: str, memory: Dict) -> str:
        """
        Generate response using LLM with full context and intent detection.
        The LLM decides whether to query data, execute commands, or chat.
        Supports tool execution via special syntax.
        """
        llm_cfg = getattr(self.config_manager.config, 'llm', {})
        provider = llm_cfg.get('provider', 'none')
        if provider and provider != 'mock' and provider != 'none':
            # Build context with history and JARVIS knowledge
            messages = self.context_builder.build_context(
                user_message=message,
                conversation_history=memory.get('history', [])
            )
            max_iterations = 3
            for i in range(max_iterations):
                response = await self.llm_manager.generate(messages)
                if not response or response.startswith('[Mock LLM]'):
                    break
                # Check for toolcall XML first (OpenCode native format)
                toolcall = self._extract_toolcall_xml(response)
                if toolcall:
                    tool = toolcall['tool']
                    params = toolcall['params']
                    # Build command string from params (ordered if needed)
                    # For now, assume single param 'command' or 'query'
                    if tool == 'web_search':
                        query = params.get('query', '')
                        if query:
                            tool_cmd = f"web_search {query}"
                        else:
                            tool_cmd = None
                    else:
                        # For workspace commands, param name is usually 'command'
                        cmd = params.get('command')
                        if cmd:
                            tool_cmd = f"{tool} {cmd}" if tool != cmd else cmd
                        else:
                            # If no command param, maybe the tool itself is the command
                            tool_cmd = tool
                    if tool_cmd:
                        self.logger.info("Executing tool from toolcall", command=tool_cmd)
                        result = self.tool_executor.execute(tool_cmd, event_bus=self.event_bus)
                        tool_output = f"Tool output:\n{result.get('output', '')}"
                        if result.get('error'):
                            tool_output += f"\nError: {result['error']}"
                        messages.append({"role": "system", "content": tool_output})
                        continue
                    else:
                        # Could not build command, return raw response
                        return response
                # Fallback: check for '!' command lines
                tool_cmd = self._extract_tool_command(response)
                if tool_cmd:
                    self.logger.info("Executing tool", command=tool_cmd)
                    result = self.tool_executor.execute(tool_cmd, event_bus=self.event_bus)
                    tool_output = f"Tool output:\n{result.get('output', '')}"
                    if result.get('error'):
                        tool_output += f"\nError: {result['error']}"
                    messages.append({"role": "system", "content": tool_output})
                    continue
                else:
                    return response
            # If we exit loop without a final response, use last if available
            if response and not response.startswith('[Mock LLM]'):
                return response
        
        # Fallback to rule-based if LLM fails
        return await self._rule_based_fallback(message, memory)

    async def _get_status(self) -> str:
        """Get JARVIS system status."""
        try:
            # Read from status file or memory
            import time
            uptime = "Unknown"
            # Could query JARVIS core via API or shared memory
            
            active_persona = "solution_consultant"  # default
            try:
                import json
                with open('MEMORY/active_persona.json') as f:
                    data = json.load(f)
                    active_persona = data.get('current_persona', active_persona)
            except:
                pass
                
            change_count = 0
            try:
                with open('MEMORY/approved_changes.json') as f:
                    data = json.load(f)
                    change_count = data.get('count', 0)
            except:
                pass
                
            return (
                "🤖 *JARVIS Status*\n\n"
                f"▶️ *State:* ONLINE\n"
                f"👤 *Active Persona:* `{active_persona}`\n"
                f"🔢 *Changes Approved:* {change_count}/50 (autonomy threshold)\n"
                f"⏱ *Uptime:* {uptime}\n"
                f"📡 *Telegram:* Connected\n\n"
                "_I'm ready to assist. Use commands or chat naturally!_"
            )
        except Exception as e:
            return f"❌ Could not fetch status: {e}"

    async def _get_persona_info(self) -> str:
        """Get current persona information."""
        try:
            import json
            active = "solution_consultant"
            personas = []
            try:
                with open('MEMORY/active_persona.json') as f:
                    data = json.load(f)
                    active = data.get('current_persona', active)
                    personas = data.get('personas_available', [])
            except:
                pass
                
            msg = f"👤 *Current Persona:* `{active}`\n\n"
            if personas:
                msg += "Available personas:\n"
                for p in personas:
                    msg += f"  • `{p}`\n"
                    
            return msg
        except Exception as e:
            return f"❌ Error: {e}"

    async def _list_deals(self) -> str:
        """List active deals."""
        try:
            import json
            deals_file = Path('jarvis/data/personas/deals.json')
            if deals_file.exists():
                with open(deals_file) as f:
                    data = json.load(f)
                    deals = data.get('deals', [])
                    
                if not deals:
                    return "📋 No active deals."
                    
                msg = "📋 *Active Deals:*\n\n"
                for i, deal in enumerate(deals[:5], 1):  # Limit to 5 for Telegram
                    msg += f"{i}. *{deal.get('title', 'Untitled')}*\n"
                    msg += f"   Client: {deal.get('client', 'N/A')}\n"
                    msg += f"   Status: {deal.get('status', 'open')}\n"
                    msg += f"   Budget: ${deal.get('budget', 0):,}\n\n"
                    
                if len(deals) > 5:
                    msg += f"_...and {len(deals)-5} more (check dashboard for full list)_\n"
                    
                return msg
            else:
                return "📋 No deals database found."
        except Exception as e:
            return f"❌ Error fetching deals: {e}"

    async def _list_patterns(self) -> str:
        """List learned patterns."""
        try:
            patterns_file = Path('MEMORY/patterns/solution_consultant_patterns.json')
            if patterns_file.exists():
                with open(patterns_file) as f:
                    data = json.load(f)
                    stats = data.get('statistics', {})
                    patterns = data.get('interaction_patterns', {})
                    
                msg = "🔍 *Learned Patterns*\n\n"
                msg += f"📊 Total patterns discovered: *{stats.get('patterns_discovered', 0)}*\n"
                msg += f"📁 Files observed: *{stats.get('total_files_observed', 0)}*\n"
                msg += f"📝 Edits tracked: *{stats.get('total_edits_observed', 0)}*\n\n"
                
                if patterns:
                    msg += "*Top patterns:*\n"
                    for key in list(patterns.keys())[:5]:
                        count = patterns[key].get('count', 0) if isinstance(patterns[key], dict) else patterns[key]
                        msg += f"  • `{key}`: {count}\n"
                        
                return msg
            else:
                return "🔍 No patterns learned yet. I'm still building my knowledge."
        except Exception as e:
            return f"❌ Error fetching patterns: {e}"

    async def _list_competitors(self) -> str:
        """List competitor mentions."""
        try:
            comp_file = Path('MEMORY/competitor_mentions.json')
            if comp_file.exists():
                with open(comp_file) as f:
                    data = json.load(f)
                    mentions = data.get('mentions', [])
                    
                if not mentions:
                    return "⚠️ No competitors detected yet."
                    
                # Count by competitor
                counts = {}
                for m in mentions:
                    comp = m.get('competitor', 'unknown')
                    counts[comp] = counts.get(comp, 0) + 1
                    
                msg = "⚠️ *Competitor Mentions*\n\n"
                for comp, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    msg += f"• *{comp}*: {count} mention{'s' if count != 1 else ''}\n"
                    
                return msg
            else:
                return "⚠️ No competitor tracking data."
        except Exception as e:
            return f"❌ Error: {e}"

    async def _generate_contextual_response(self, message: str, context: Dict) -> str:
        """
        Generate AI-powered contextual response using LLM.
        Falls back to rule-based if LLM unavailable.
        """
        # Try LLM first if configured
        try:
            llm_cfg = getattr(self.config_manager.config, 'llm', {})
            provider = llm_cfg.get('provider', 'none')
            if provider and provider != 'mock' and provider != 'none':
                # Build conversation context with recent history
                history = context.get('history', [])
                # Add the current message to history for context building
                messages = self.context_builder.build_context(
                    user_message=message,
                    conversation_history=history
                )
                response = await self.llm_manager.generate(messages)
                if response and not response.startswith('[Mock LLM]'):
                    return response
        except Exception as e:
            self.logger.error("LLM generation failed, falling back to rules", error=str(e))

        # Fallback to rule-based responses
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ['hello', 'hi', 'hey']):
            return "👋 *Hello!* I'm JARVIS, your AI assistant. I can help you with:\n• Status checks\n• Deal tracking\n• Pattern analysis\n• Workspace insights\n\nType `/help` for all commands, or ask me anything naturally!"
            
        elif 'how are you' in msg_lower:
            return "🤖 *I'm operational and learning continuously!*\n\nAll systems online. I've been monitoring your workspace and building knowledge. How can I assist you today?"
            
        elif 'thank' in msg_lower:
            return "👍 You're welcome! Anything else I can help with?"
            
        elif 'what' in msg_lower and 'doing' in msg_lower:
            return "📊 *Current Activities:*\n• Monitoring file changes\n• Learning your coding patterns\n• Tracking deals and personas\n• Watching for competitors\n• Archiving snapshots\n\nI'm always working in the background to understand your workflow."
            
        elif 'help' in msg_lower:
            return await self._get_help()
            
        else:
            return (
                "🤔 *I heard you, but I need more context.*\n\n"
                "I can answer questions about:\n"
                "• `status` - System health\n"
                "• `persona` - Current mode\n"
                "• `deals` - Active opportunities\n"
                "• `patterns` - Learned behaviors\n"
                "• `competitors` - Detected rivals\n"
                "• `scan` - Trigger workspace analysis\n"
                "• `archive` - Create snapshot\n\n"
                "Or chat naturally! What would you like to know?"
            )

    async def _get_help(self) -> str:
        """Return help message."""
        return (
            "🤖 *JARVIS Telegram Bot*\n\n"
            "*Commands:*\n"
            "/status - System status & uptime\n"
            "/persona - Current active persona\n"
            "/deals - List active deals\n"
            "/patterns - Show learned patterns\n"
            "/competitors - Detected competitors\n"
            "/scan - Trigger workspace scan\n"
            "/archive - Create snapshot\n"
            "/help - This message\n\n"
            "*Natural Chat:*\n"
            "You can also chat naturally! Ask me anything about your work, "
            "request status updates, or query my knowledge base.\n\n"
            "*Examples:*\n"
            "  \"What deals are active?\"\n"
            "  \"How many patterns have you learned?\"\n"
            "  \"Who are we competing against?\"\n"
            "  \"Switch to solution consultant mode\"\n\n"
            "_Powered by JARVIS AI Agent_"
        )

    async def _rule_based_fallback(self, message: str, memory: Dict) -> str:
        """Fallback responses when LLM is unavailable."""
        msg_lower = message.lower()
        
        # Check for greetings
        if any(word in msg_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "👋 *Hello!* I'm JARVIS. I can help you with workspace insights, deals, patterns, and more. How can I assist?"
        
        # Check for status inquiry
        if 'status' in msg_lower or 'health' in msg_lower or 'system' in msg_lower:
            return await self._get_status()
        
        # Check for deals
        if 'deal' in msg_lower or 'opportunit' in msg_lower or 'pipeline' in msg_lower:
            return await self._list_deals()
        
        # Check for patterns
        if 'pattern' in msg_lower or 'learn' in msg_lower or 'behavior' in msg_lower:
            return await self._list_patterns()
        
        # Check for competitors
        if 'competitor' in msg_lower or 'rival' in msg_lower or 'competition' in msg_lower:
            return await self._list_competitors()
        
        # Check for persona
        if 'persona' in msg_lower or 'mode' in msg_lower:
            return await self._get_persona_info()
        
        # Check for help
        if 'help' in msg_lower:
            return await self._get_help()
        
        # Default
        return (
            "🤔 I'm not sure how to respond to that in my current mode.\n\n"
            "I can help with:\n"
            "• System status and health\n"
            "• Active deals and opportunities\n"
            "• Learned patterns and behaviors\n"
            "• Competitor analysis\n"
            "• Workspace scans and snapshots\n\n"
            "Try asking something specific or type /help for guidance."
        )

    # Command handlers
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        response = await self._get_status()
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _cmd_persona(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /persona command."""
        response = await self._get_persona_info()
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _cmd_deals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deals command."""
        response = await self._list_deals()
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _cmd_patterns(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /patterns command."""
        response = await self._list_patterns()
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _cmd_competitors(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /competitors command."""
        response = await self._list_competitors()
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command."""
        # Trigger scan via event bus (would be handled by scanner component)
        scan_event = Event("scan.requested", "telegram_bot", {
            "user_id": update.effective_user.id,
            "reason": "telegram_command"
        })
        self.event_bus.publish(scan_event)
        await update.message.reply_text(
            "🔄 *Workspace scan initiated!*\n\nI'm analyzing your current workspace. "
            "This may take a moment. I'll notify you when complete.",
            parse_mode='Markdown'
        )

    async def _cmd_archive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /archive command."""
        # Trigger archive via event bus (archiver listens to "archive.request")
        archive_event = Event("archive.request", "telegram_bot", {
            "user_id": update.effective_user.id,
            "reason": "telegram_command"
        })
        self.event_bus.publish(archive_event)
        await update.message.reply_text(
            "📦 *Snapshot creation triggered!*\n\nI'm creating a compressed backup of your workspace. "
            "You'll find it in MEMORY/archives/ with a timestamp.",
            parse_mode='Markdown'
        )

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome = (
            "🚀 *JARVIS Online!*\n\n"
            "I'm your AI agent, fully integrated with your OpenCode workspace.\n\n"
            "I can:\n"
            "• Monitor your work automatically\n"
            "• Learn your patterns and preferences\n"
            "• Track deals and manage personas\n"
            "• Execute commands and take actions\n\n"
            "Chat with me naturally or use commands. Type /help anytime!\n\n"
            "_You're speaking directly to your AI employee._"
        )
        await update.message.reply_text(welcome, parse_mode='Markdown')

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = await self._get_help()
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def _handle_system_event(self, event: Event):
        """Handle system events that should be broadcasted to Telegram channel."""
        if not self.config or not self.config.broadcast_events or not self.config.channel_id:
            return
            
        # Check if this event type should be broadcast
        should_broadcast = False
        if event.type == "persona.switched" and self.config.notify_persona_switch:
            should_broadcast = True
        elif event.type == "modification.approved" and self.config.notify_modification_approved:
            should_broadcast = True
        elif event.type == "error.occurred" and self.config.notify_errors:
            should_broadcast = True
        elif event.type == "pattern.discovered" and self.config.notify_patterns:
            should_broadcast = True
        elif event.type == "competitor.detected" and self.config.notify_competitors:
            should_broadcast = True
            
        if should_broadcast:
            message = self._format_event_for_channel(event)
            await self._send_to_channel(message)

    def _format_event_for_channel(self, event: Event) -> str:
        """Format a system event as a broadcast message."""
        templates = {
            "persona.switched": "👤 *Persona Switched*\n{from_} → {to}\nReason: {reason}",
            "modification.approved": "✅ *Change Approved*\n{description}\nBy: {approved_by}",
            "error.occurred": "❌ *Error Report*\nComponent: {component}\nError: {error}",
            "pattern.discovered": "🔍 *New Pattern*\n{pattern}\nConfidence: {confidence:.1%}",
            "competitor.detected": "⚠️ *Competitor Alert*\nDetected: {competitor}\nContext: {context[:100]}..."
        }
        
        template = templates.get(event.type, "📢 *Event:* {event_type}\n{data}")
        data = event.data
        
        try:
            return template.format(
                from_=data.get('from', 'Unknown'),
                to=data.get('to', 'Unknown'),
                reason=data.get('reason', 'N/A'),
                description=data.get('description', 'No description'),
                approved_by=data.get('approved_by', 'System'),
                component=event.source,
                error=data.get('error', 'Unknown'),
                pattern=data.get('pattern', 'Unknown'),
                confidence=data.get('confidence', 0.0),
                competitor=data.get('competitor', 'Unknown'),
                context=str(data.get('context', '')),
                event_type=event.type,
                data=json.dumps(data, indent=2)
            )
        except:
            return f"📢 {event.type}: {json.dumps(data)}"

    async def _send_to_channel(self, message: str):
        """Send a broadcast message to the configured channel."""
        if not TELEGRAM_AVAILABLE or not self.bot or not self.config.channel_id:
            return
            
        try:
            await self.bot.send_message(
                chat_id=self.config.channel_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error("Failed to send broadcast", error=str(e))

    # Public API
    async def send_notification(self, message: str, parse_mode: str = 'Markdown'):
        """Send a notification to the channel (if configured)."""
        if self.config and self.config.channel_id and TELEGRAM_AVAILABLE and self.bot:
            try:
                await self.bot.send_message(
                    chat_id=self.config.channel_id,
                    text=message,
                    parse_mode=parse_mode
                )
                return True
            except Exception as e:
                self.logger.error("Failed to send notification", error=str(e))
                return False
        return False

    async def reply_to_user(self, user_id: int, message: str, parse_mode: str = 'Markdown'):
        """Reply directly to a user via Telegram API."""
        if not TELEGRAM_AVAILABLE or not self.bot:
            # Fallback: send to channel if user_id is in allowed list
            return await self.send_notification(message, parse_mode)
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            self.logger.error("Failed to reply to user", user_id=user_id, error=str(e))
            return False
