#!/usr/bin/env python3
"""
JARVIS Core Orchestrator - Central coordination of all components.
"""

import asyncio
import signal
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.config import ConfigManager
from jarvis.safety.guard import SafetyGuard
from jarvis.persona.persona_manager import PersonaManager
from jarvis.observers.file_system import FileSystemObserver
from jarvis.observers.conversations import ConversationObserver
from jarvis.learners.pattern_recognition import PatternRecognition
from jarvis.mcp.context_engine import ContextEngine
from jarvis.archive.archiver import Archiver
from jarvis.mcp.websocket_server import WebSocketServer
from jarvis.scanner.workspace_scanner import WorkspaceScanner
from jarvis.learners.conversation_learner import ConversationLearner
from jarvis.skills.conversation_summarizer import ConversationSummarizationSkill
from jarvis.skills.competitive_intelligence import CompetitiveIntelligenceSkill
from jarvis.skills.documentation import DocumentationSkill
from jarvis.skills.technical_risk_assessment import TechnicalRiskAssessmentSkill
from jarvis.skills.discovery_management import DiscoveryManagementSkill
from jarvis.skills.meddpicc_skill import DealMeddpiccSkill
from jarvis.skills.tech_utilities import TechUtilitiesSkill
from jarvis.skills.battlecards_skill import BattlecardsSkill
from jarvis.skills.value_architecture_skill import ValueArchitectureSkill
from jarvis.skills.risk_report_skill import DealRiskReportSkill
from jarvis.skills.demo_strategy_skill import DemoStrategySkill
from jarvis.skills.account_dashboard_skill import AccountDashboardSkill
from jarvis.observers.account_initializer import AccountAutoInitializer
from jarvis.skills.meeting_summary_skill import MeetingSummarySkill
from jarvis.skills.meeting_prep_skill import MeetingPrepSkill
from jarvis.skills.proposal_generator_skill import ProposalGeneratorSkill
from jarvis.skills.followup_email_skill import FollowupEmailSkill
from jarvis.skills.deal_stage_tracker_skill import DealStageTrackerSkill
from jarvis.meeting.meeting_processor import MeetingProcessor
from jarvis.playbook.automation_engine import PlaybookAutomationEngine
from jarvis.sync.claude_sync_manager import ClaudeSyncManager
from jarvis.brain.conversation_extractor import ConversationExtractor
from jarvis.brain.document_processor import DocumentProcessor
from jarvis.observers.account_watcher import AccountWatcher


@dataclass
class ComponentStatus:
    name: str
    healthy: bool = True
    last_heartbeat: float = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """Central coordinator that starts, monitors, and manages all JARVIS components."""

    COMPONENT_CLASSES = {
        'file_system': FileSystemObserver,
        'conversations': ConversationObserver,
        'pattern_learner': PatternRecognition,
        'context_engine': ContextEngine,
        'safety_guard': SafetyGuard,
        'persona_manager': PersonaManager,
        'archiver': Archiver,
        'websocket_server': WebSocketServer,
        'scanner': WorkspaceScanner,
        'conversation_learner': ConversationLearner,
        'conversation_summarizer': ConversationSummarizationSkill,
        'competitive_intelligence': CompetitiveIntelligenceSkill,
        'documentation': DocumentationSkill,
        'technical_risk_assessment': TechnicalRiskAssessmentSkill,
        'discovery_management': DiscoveryManagementSkill,
        'meddpicc': DealMeddpiccSkill,
        'tech_utilities': TechUtilitiesSkill,
        'battlecards': BattlecardsSkill,
        'value_architecture': ValueArchitectureSkill,
        'risk_report': DealRiskReportSkill,
        'demo_strategy': DemoStrategySkill,
        'account_dashboard': AccountDashboardSkill,
        'account_auto_init': AccountAutoInitializer,
        # v2: Meeting, Playbook, Sync, New Skills
        'meeting_summary': MeetingSummarySkill,
        'meeting_prep': MeetingPrepSkill,
        'proposal_generator': ProposalGeneratorSkill,
        'followup_email': FollowupEmailSkill,
        'deal_stage_tracker': DealStageTrackerSkill,
        'meeting_processor': MeetingProcessor,
        'playbook_engine': PlaybookAutomationEngine,
        'claude_sync': ClaudeSyncManager,
        # Brain — interlinking reactive layer
        'account_watcher': AccountWatcher,
        'conversation_extractor': ConversationExtractor,
        'document_processor': DocumentProcessor,
    }

    def __init__(self, config):
        self.config = config
        self.logger = JARVISLogger("orchestrator")
        self.event_bus = EventBus()
        self.components: Dict[str, Any] = {}
        self.status: Dict[str, ComponentStatus] = {}
        self._shutdown = False
        self._tasks: list[asyncio.Task] = []

    async def initialize(self):
        """Initialize all components in proper order."""
        self.logger.info("Initializing JARVIS orchestrator", version="2.0.0")

        # Load configuration
        self.config.load()
        self.logger.info("Configuration loaded", config_file=str(self.config.CONFIG_FILE))

        # Create component status tracking
        for name in self.COMPONENT_CLASSES:
            self.status[name] = ComponentStatus(name=name)

        # Start event bus first
        await self.event_bus.start()
        self.logger.info("Event bus started")

        # Initialize components in dependency order
        init_order = [
            'safety_guard', 'persona_manager', 'context_engine',
            'file_system', 'conversations', 'pattern_learner', 'conversation_learner',
            'conversation_summarizer', 'competitive_intelligence', 'documentation',
            'technical_risk_assessment', 'discovery_management',
            'meddpicc', 'tech_utilities', 'battlecards', 'value_architecture', 'risk_report', 'demo_strategy',
            'account_dashboard',
            'account_auto_init',
            # v2 components
            'meeting_summary', 'meeting_prep', 'proposal_generator',
            'followup_email', 'deal_stage_tracker',
            # account_watcher must start before brain components
            'account_watcher',
            'meeting_processor', 'playbook_engine', 'claude_sync',
            'conversation_extractor', 'document_processor',
            'scanner', 'archiver', 'websocket_server'
        ]

        for name in init_order:
            if name in self.COMPONENT_CLASSES:
                await self._init_component(name)
                await asyncio.sleep(0.5)  # Stagger startup

        # Subscribe orchestrator to important events
        self.event_bus.subscribe("component.error", self._handle_component_error)
        self.event_bus.subscribe("system.shutdown", self._handle_shutdown)

        self.logger.info("All components initialized", count=len(self.components))

        # Health check task
        self._tasks.append(asyncio.create_task(self._health_monitor()))

    async def _init_component(self, name: str):
        """Initialize a single component."""
        try:
            cls = self.COMPONENT_CLASSES[name]
            instance = cls(self.config, self.event_bus)
            await instance.start()
            self.components[name] = instance
            self.status[name].healthy = True
            self.status[name].last_heartbeat = asyncio.get_event_loop().time()
            self.logger.info("Component started", component=name)
        except Exception as e:
            self.logger.error("Component failed to start", component=name, error=str(e))
            self.status[name].healthy = False
            self.status[name].error_count += 1
            raise

    async def _handle_component_error(self, event: Event):
        """Handle error events from components."""
        component = event.data.get("component")
        error = event.data.get("error")
        self.logger.error("Component error reported", component=component, error=error)
        if component in self.status:
            self.status[component].error_count += 1
            # If errors exceed threshold, restart component
            if self.status[component].error_count > 5:
                await self._restart_component(component)

    async def _handle_shutdown(self, event: Event):
        """Handle shutdown event from any component."""
        self.logger.info("Shutdown event received")
        await self.shutdown()

    async def _restart_component(self, name: str):
        """Attempt to restart a failed component."""
        self.logger.warning("Restarting component", component=name)
        if name in self.components:
            try:
                await self.components[name].stop()
            except:
                pass
        try:
            await self._init_component(name)
        except Exception as e:
            self.logger.error("Failed to restart component", component=name, error=str(e))

    async def _health_monitor(self):
        """Periodic health check of all components."""
        while not self._shutdown:
            await asyncio.sleep(30)
            now = asyncio.get_event_loop().time()
            for name, comp_status in self.status.items():
                if comp_status.healthy:
                    # Check heartbeat (if component supports it)
                    last = comp_status.last_heartbeat
                    if last and (now - last) > 120:  # 2 minutes
                        self.logger.warning("Component heartbeat missing", component=name)
                        comp_status.healthy = False

    async def shutdown(self):
        """Graceful shutdown of all components."""
        self.logger.info("Shutting down JARVIS")
        self._shutdown = True

        # Stop all tasks
        for task in self._tasks:
            task.cancel()

        # Stop components in reverse order
        for name in reversed(list(self.components.keys())):
            try:
                await self.components[name].stop()
                self.logger.info("Component stopped", component=name)
            except Exception as e:
                self.logger.error("Error stopping component", component=name, error=e)

        # Stop event bus
        await self.event_bus.stop()
        self.logger.info("JARVIS shutdown complete")

    async def run(self):
        """Main run loop."""
        try:
            await self.initialize()
            self.logger.info("JARVIS is ready and running")

            # Keep running until shutdown
            while not self._shutdown:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.critical("Fatal error in orchestrator", error=str(e))
        finally:
            await self.shutdown()


async def main():
    """Entry point for standalone JARVIS daemon."""
    import sys
    from pathlib import Path

    # Load full configuration
    config_manager = ConfigManager()
    config_manager.load()
    # Ensure path attributes are Path objects
    from pathlib import Path
    for attr in ["workspace_root","data_dir","logs_dir","temp_dir","opencode_db_path","killswitch_path"]:
        val = getattr(config_manager.config, attr)
        if isinstance(val, str):
            setattr(config_manager.config, attr, Path(val))
    # Expose killswitch_path on ConfigManager for compatibility
    setattr(config_manager, "killswitch_path", config_manager.config.killswitch_path)
    orchestrator = Orchestrator(config_manager)

    # Signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(orchestrator.shutdown()))

    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())