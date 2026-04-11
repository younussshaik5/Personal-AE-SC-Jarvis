"""
JARVIS MCP Server - Production-ready Model Context Protocol server.
Registers all 24 sales intelligence skills + onboarding wizard as MCP tools.
Integrates auto-scaffolding, context detection, and autonomous learning.
"""

import asyncio
import logging
import json
from typing import Any, Optional
from pathlib import Path

from .config.config_manager import ConfigManager
from .llm.llm_manager import LLMManager
from .skills import SKILL_REGISTRY
from .safety.guard import SafetyGuard
from .utils.logger import setup_logger
from .agents import AgentOrchestrator
from .context_detector import ContextDetector
from .account_hierarchy import AccountHierarchy
from .queue import SkillQueue, QueueWorker, FileWatcher, PRIORITY_HIGH, SKILL_OUTPUT_FILES
from .queue.coordinator import BriefCoordinator
from .learning import SelfLearner, IntelligenceExtractor, KnowledgeMerger
from .autonomous import AutonomousMemory, RetryEngine


# Setup logging
logger = setup_logger("jarvis_mcp")


class JarvisServer:
    """JARVIS MCP Server - Main entry point with multi-agent orchestration"""

    def __init__(self):
        """Initialize JARVIS server with orchestrator"""
        self.config = ConfigManager()
        self.llm = LLMManager(self.config)
        self.guard = SafetyGuard()
        self.logger = logger
        
        # Initialize context management
        self.context_detector = ContextDetector()
        self.account_hierarchy = AccountHierarchy()

        # Initialize skill instances
        self.skills = {}
        self._initialize_skills()

        # Initialize orchestrator for current account
        self.orchestrator = None
        self._initialize_orchestrator()

        # ── Queue bus + self-learning ────────────────────────────────────────
        self.learner     = SelfLearner(self.config.accounts_root)
        self.extractor   = IntelligenceExtractor(self.llm)
        self.merger      = KnowledgeMerger(self.config.accounts_root)
        self.coordinator = BriefCoordinator(self.config)
        self.skill_queue  = SkillQueue()
        self.queue_worker = QueueWorker(
            self.skill_queue, self.skills,
            learner=self.learner,
            extractor=self.extractor,
            merger=self.merger,
            coordinator=self.coordinator,
        )

        # ── Autonomous retry engine ─────────────────────────────────────────
        self.autonomous_memory = AutonomousMemory()
        self.retry_engine      = RetryEngine(self.llm, self.config, self.autonomous_memory)
        self.queue_worker.retry_engine = self.retry_engine

        self.file_watcher = FileWatcher(
            self.skill_queue, self.config.accounts_root,
            extractor=self.extractor,
            merger=self.merger,
        )

        # Wire skill_queue into SystemHealthSkill so it can report real queue depth
        sh = self.skills.get("system_health")
        if sh:
            sh.skill_queue = self.skill_queue

        # Agent background tasks
        self.agent_task = None
        self.orchestration_running = False

    def _initialize_skills(self):
        """Initialize all skill instances"""
        self.logger.info("Initializing JARVIS skills...")
        for skill_name, skill_class in SKILL_REGISTRY.items():
            try:
                self.skills[skill_name] = skill_class(self.llm, self.config)
                self.logger.info(f"✓ Initialized: {skill_name}")
            except Exception as e:
                self.logger.error(f"✗ Failed to initialize {skill_name}: {type(e).__name__}: {e}", exc_info=True)

        self.logger.info(f"✅ Initialized {len(self.skills)} skills")

    def _initialize_orchestrator(self):
        """Initialize multi-agent orchestrator for current account"""
        try:
            account_path = self.context_detector.get_current_account_path()
            if account_path:
                self.orchestrator = AgentOrchestrator(account_path)
                self.logger.info(f"✅ Orchestrator initialized for {account_path}")
            else:
                self.logger.warning("No account context detected - orchestrator disabled")
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {type(e).__name__}: {e}", exc_info=True)


    async def start_background_orchestration(self):
        """Start background orchestration with full autonomy and evolution."""
        # Always start queue bus regardless of orchestrator
        self.queue_worker.start()
        self.file_watcher.start()
        self.logger.info("⚡ Queue bus started — file watcher + cascade worker active")

        if not self.orchestrator:
            return

        self.orchestration_running = True
        self.logger.info("🤖 Starting autonomous AI employee system...")

        try:
            await self.orchestrator.start()

            while self.orchestration_running:
                # Run full cycle: file learning + document vectorization + evolution + outcome tracking
                cycle_result = await self.orchestrator.run_full_cycle()
                self.logger.debug(f"Orchestration cycle {cycle_result['cycle']} complete")

                # Run every 30 seconds
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            self.logger.info("Autonomous system stopped")
        except Exception as e:
            self.logger.error(f"Autonomous system error: {type(e).__name__}: {e}", exc_info=True)

    def _get_tool_list(self) -> list:
        """Get list of available tools"""
        return [
            # Onboarding
            "onboarding_start",
            "onboarding_next",
            
            # Account Management
            "scaffold_account",
            
            # Sales Skills
            "get_proposal",
            "get_battlecard",
            "get_demo_strategy",
            "get_risk_report",
            "get_value_architecture",
            "get_discovery",
            "get_competitive_intelligence",
            "get_meeting_prep",
            "process_meeting",
            "summarize_conversation",
            "track_meddpicc",
            "generate_sow",
            "generate_followup",
            "get_account_summary",
            "assess_technical_risk",
            "analyze_competitor_pricing",
            "update_deal_stage",
            "generate_architecture",
            "generate_documentation",
            "generate_html_report",
            "extract_intelligence",
            "build_knowledge_graph",
            "quick_insights",
            "generate_custom_template",

            # Autonomous system
            "get_jarvis_todos",
            "get_autonomous_status",
        ]


    async def handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Handle tool call with FULL autonomous evolution and learning."""
        # ── Validation ───────────────────────────────────────────────────────
        # Validate tool_name
        if not tool_name or not isinstance(tool_name, str):
            return {"error": "Invalid tool_name: must be a non-empty string"}

        # Validate arguments
        if not isinstance(arguments, dict):
            return {"error": "Invalid arguments: must be a dictionary"}

        # Safety check
        if not self.guard.is_safe():
            return {"error": "Safety check failed"}

        # Handle onboarding tools
        if tool_name.startswith("onboarding_"):
            return await self.handle_onboarding_tool(tool_name, arguments)

        # Handle autonomous system tools
        if tool_name == "get_jarvis_todos":
            return await self._handle_get_jarvis_todos(arguments)
        if tool_name == "get_autonomous_status":
            return await self._handle_get_autonomous_status(arguments)

        # Map tool names to skills (scaffold_account is handled directly via SKILL_REGISTRY)
        tool_to_skill = {
            "scaffold_account":             "scaffold_account",
            "get_proposal":                 "proposal",
            "get_battlecard":               "battlecard",
            "get_demo_strategy":            "demo_strategy",
            "get_risk_report":              "risk_report",
            "get_value_architecture":       "value_architecture",
            "get_discovery":                "discovery",
            "get_competitive_intelligence": "competitive_intelligence",
            "get_meeting_prep":             "meeting_prep",
            "process_meeting":              "meeting_summary",
            "summarize_conversation":       "conversation_summarizer",
            "track_meddpicc":               "meddpicc",
            "generate_sow":                 "sow",
            "generate_followup":            "followup_email",
            "get_account_summary":          "account_summary",
            "assess_technical_risk":        "technical_risk",
            "analyze_competitor_pricing":   "competitor_pricing",
            "update_deal_stage":            "deal_stage_tracker",
            "generate_architecture":        "architecture_diagram",
            "generate_documentation":       "documentation",
            "generate_html_report":         "html_generator",
            "extract_intelligence":         "conversation_extractor",
            "build_knowledge_graph":        "knowledge_builder",
            "quick_insights":               "quick_insights",
            "generate_custom_template":     "custom_template",
            "system_health":                "system_health",
        }

        skill_name = tool_to_skill.get(tool_name)
        if not skill_name or skill_name not in self.skills:
            return {"error": f"Unknown tool: {tool_name}"}

        # ── Validate account_name for account-based tools ───────────────────
        # account_name for logging / learning — skill.execute() extracts it from arguments itself
        account_name = arguments.get("account_name", "")

        # Tools that require account_name
        tools_requiring_account = {
            "get_proposal", "get_battlecard", "get_demo_strategy", "get_risk_report",
            "get_value_architecture", "get_discovery", "get_competitive_intelligence",
            "get_meeting_prep", "process_meeting", "summarize_conversation", "track_meddpicc",
            "generate_sow", "generate_followup", "get_account_summary", "assess_technical_risk",
            "analyze_competitor_pricing", "update_deal_stage", "generate_architecture",
            "generate_documentation", "generate_html_report", "extract_intelligence",
            "build_knowledge_graph", "quick_insights", "generate_custom_template",
            "system_health"
        }

        if tool_name in tools_requiring_account:
            if not account_name or not isinstance(account_name, str):
                return {"error": f"Tool '{tool_name}' requires a valid account_name"}

            # Sanitize account_name
            account_name = account_name.strip()
            if not account_name:
                return {"error": "account_name cannot be empty after trimming whitespace"}

            # Update arguments with sanitized account_name
            arguments = {**arguments, "account_name": account_name}

        try:
            skill = self.skills[skill_name]

            # Execute skill — execute() handles account_name extraction and generate() call
            result = await skill.execute(arguments)

            if result and not result.strip().startswith("❌"):
                # Persist output to disk so files are always populated
                output_file = SKILL_OUTPUT_FILES.get(skill_name)
                if output_file and account_name:
                    await skill.write_output(account_name, output_file, result)

                # Record in evolution log + skill timeline
                await self.learner.record(
                    account_name=account_name,
                    skill_name=skill_name,
                    trigger="user",
                    status="ok",
                )
                # Feedback loop — extract new intel from output, merge to discovery.md
                asyncio.ensure_future(
                    self.merger.merge_from_skill_output(
                        account_name, skill_name, result, self.extractor
                    )
                )
                # Fire cascade — queue downstream skills automatically
                await self.queue_worker.trigger_cascade(account_name, skill_name)

            return {"result": result}
        except Exception as e:
            self.logger.error(f"Error in {tool_name}: {type(e).__name__}: {e}", exc_info=True)
            return {"error": str(e)}

    async def handle_onboarding_tool(self, tool_name: str, arguments: dict) -> dict:
        """Handle onboarding flow"""
        try:
            onboarding_skill = self.skills.get('onboarding')
            if not onboarding_skill:
                return {"error": "Onboarding skill not initialized"}
            
            if tool_name == "onboarding_start":
                # Start onboarding
                result = await onboarding_skill.generate(action='start')
                return {"result": result}
            
            elif tool_name == "onboarding_next":
                # Process response and advance
                response = arguments.get('response', '')
                result = await onboarding_skill.generate(action='next', response=response)
                return {"result": result}
            
            return {"error": f"Unknown onboarding action: {tool_name}"}
        
        except Exception as e:
            self.logger.error(f"Onboarding error: {type(e).__name__}: {e}", exc_info=True)
            return {"error": str(e)}


    async def _handle_get_jarvis_todos(self, arguments: dict) -> dict:
        """Return open todos created by the autonomous retry engine."""
        try:
            todos = self.autonomous_memory.get_todos(resolved=False)
            if not todos:
                return {"result": "✅ No open todos — all skills resolving autonomously."}
            import datetime
            lines = ["## JARVIS Autonomous Todos\n"]
            for t in todos:
                created = datetime.datetime.fromtimestamp(t["created_at"]).strftime("%Y-%m-%d %H:%M")
                lines.append(
                    f"- **[{t['id']}]** `{t['skill']}` / `{t['account']}`\n"
                    f"  Reason: {t['reason']}\n"
                    f"  Strategies tried: {', '.join(t.get('strategies_tried', []))}\n"
                    f"  Created: {created}\n"
                )
            return {"result": "\n".join(lines)}
        except Exception as e:
            return {"error": str(e)}

    async def _handle_get_autonomous_status(self, arguments: dict) -> dict:
        """Return autonomous memory summary — attempt history, success rate, open todos."""
        try:
            s = self.autonomous_memory.summary()
            lines = [
                "## JARVIS Autonomous Status\n",
                f"- Skills tracked: {s['skills_tracked']}",
                f"- Skills with a success: {s['skills_successful']}",
                f"- Open todos (need human): {s['pending_todos']}",
                f"- Global insights accumulated: {s['global_insights']}",
            ]
            return {"result": "\n".join(lines)}
        except Exception as e:
            return {"error": str(e)}

    async def log_conversation(self, user_message: str, assistant_response: str, skill_used: str = None):
        """Log chat for learning - called by Claude after each interaction."""
        if self.orchestrator:
            await self.orchestrator.analyze_user_chat(user_message, assistant_response, skill_used)
            self.logger.debug("✓ Conversation logged for learning")

    async def process_cowork_file(self, file_path: str, file_name: str):
        """Process file from cowork upload - called when user drops file in chat."""
        if self.orchestrator:
            result = await self.orchestrator.process_cowork_upload(file_path, file_name)
            self.logger.info(f"✓ Cowork file processed: {result['action_taken']}")
            return result

    async def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        context = self.context_detector.detect_context()
        
        status = {
            "server_name": "JARVIS MCP",
            "status": "running",
            "skills_initialized": len(self.skills),
            "skills_available": self._get_tool_list(),
            "orchestrator_enabled": self.orchestrator is not None,
            "background_orchestration": self.orchestration_running,
            "context": {
                "auto_detected": context is not None,
                "account": context.get('name') if context else None,
                "path": context.get('path') if context else None
            },
            "accounts_available": len(self.account_hierarchy.list_accounts())
        }

        if self.orchestrator:
            status["agent_status"] = await self.orchestrator.get_system_status()

        return status

    async def run_standalone(self):
        """Run server in standalone mode for verification"""
        self.logger.info("🚀 Starting JARVIS MCP Server (Standalone Mode)...")
        self.logger.info(f"✅ Initialized {len(self.skills)} skills")
        self.logger.info(f"✅ Available tools: {', '.join(self._get_tool_list())}")

        if self.orchestrator:
            self.logger.info("✅ Multi-agent orchestrator initialized")
            status = await self.get_system_status()
            self.logger.info(f"System Status: {json.dumps(status, indent=2)}")

            # Start background orchestration
            self.agent_task = asyncio.create_task(self.start_background_orchestration())
            self.logger.info("✅ Background agent orchestration started")

            try:
                # Run for 60 seconds in standalone mode
                await asyncio.sleep(60)
            except KeyboardInterrupt:
                pass
            finally:
                self.orchestration_running = False
                if self.agent_task:
                    self.agent_task.cancel()
        else:
            self.logger.warning("⚠️  Multi-agent orchestrator not initialized")

    async def shutdown(self):
        """Graceful shutdown — stops all background services within 10s."""
        self.logger.info("🛑 Shutting down JARVIS MCP Server...")
        self.orchestration_running = False

        # Stop queue bus first so no new jobs are started
        self.queue_worker.stop()
        self.file_watcher.stop()

        if self.agent_task and not self.agent_task.done():
            self.agent_task.cancel()
            try:
                await asyncio.wait_for(self.agent_task, timeout=10.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        self.logger.info("✅ Shutdown complete")


async def main():
    """Main entry point for standalone testing"""
    server = JarvisServer()
    await server.run_standalone()


if __name__ == "__main__":
    asyncio.run(main())
