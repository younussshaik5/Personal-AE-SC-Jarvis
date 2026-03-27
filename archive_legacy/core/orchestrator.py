import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from utils.event_bus import EventBus, Event, EventType
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class ComponentState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ComponentInfo:
    name: str
    state: ComponentState
    dependencies: List[str]
    subscribers: List[str]
    health_status: Dict[str, Any]
    last_heartbeat: datetime
    metrics: Dict[str, float]


class Orchestrator:
    """
    Central coordinator for all JARVIS components.
    Manages lifecycle, scheduling, and event routing.
    """

    def __init__(self, config: Config):
        self.config = config
        self.state = ComponentState.INITIALIZING
        self.start_time: Optional[datetime] = None
        self.components: Dict[str, ComponentInfo] = {}
        self.event_bus = EventBus(max_size=10000)
        self._shutdown_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []

        # Scheduling (seconds)
        self._schedules = {
            "workspace_scan": 300,  # Every 5 minutes
            "performance_analysis": 3600,  # Every hour
            "meta_learning": 21600,  # Every 6 hours
            "archive_snapshot": 86400,  # Daily
            "health_check": 60,  # Every minute
        }

        # Event routing table
        self._event_routes = {
            EventType.FILE_CREATED: ["learner.pattern_recognition", "updater.file_modder"],
            EventType.FILE_MODIFIED: ["learner.performance_analyzer"],
            EventType.NEW_WORKSPACE: ["scanner.integration_engine", "mcp.skill_selector"],
            EventType.TASK_COMPLETED: ["learner.meta", "persona.deal_tracker"],
            EventType.ERROR_OCCURRED: ["safety.guard", "learner.trend_detector"],
            EventType.USER_FEEDBACK: ["learner.preference_extractor", "persona.comm_logger"],
        }

    async def initialize(self):
        """Initialize all components in proper order"""
        logger.info("Initializing JARVIS orchestrator")

        try:
            # 1. Initialize message bus
            await self.event_bus.start()
            self._subscribe_to_core_events()

            # 2. Load and initialize components in dependency order
            await self._initialize_components()

            # 3. Start scheduling
            await self._start_schedulers()

            # 4. Perform initial workspace scan
            await self._trigger_initial_scan()

            self.state = ComponentState.RUNNING
            logger.info("JARVIS orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self.state = ComponentState.ERROR
            raise

    def _subscribe_to_core_events(self):
        """Subscribe to critical system events"""
        self.event_bus.subscribe(
            "orchestrator",
            [EventType.COMPONENT_ERROR, EventType.SYSTEM_SHUTDOWN],
            self._handle_system_event
        )

    async def _initialize_components(self):
        """Initialize components respecting dependencies"""
        initialization_order = [
            "safety.guard",
            "utils.logger",
            "persona.history_db",
            "mcp.context_engine",
            "scanner.workspace_scanner",
            "observers.file_system",
            "observers.git",
            "observers.conversations",
            "observers.database",
            "learners.pattern_recognition",
            "learners.preference_extractor",
            "learners.performance_analyzer",
            "learners.trend_detector",
            "learners.meta",
            "persona.persona_manager",
            "persona.deal_tracker",
            "mcp.skill_selector",
            "mcp.autonomous_planner",
            "updaters.file_modder",
            "updaters.code_generator",
            "updaters.config_updater",
            "updaters.schema_migrator",
            "fireup.skill_loader",
            "archive.archiver",
            "sync_manager",
        ]

        for component_name in initialization_order:
            try:
                component = self._load_component(component_name)
                await component.start()
                self.components[component_name] = ComponentInfo(
                    name=component_name,
                    state=ComponentState.RUNNING,
                    dependencies=component.dependencies,
                    subscribers=[],
                    health_status={"active": True},
                    last_heartbeat=datetime.utcnow(),
                    metrics={}
                )
                logger.info(f"Initialized component: {component_name}")
            except Exception as e:
                logger.error(f"Failed to initialize {component_name}: {e}")
                # Continue with other components, mark this as error

    def _load_component(self, name: str):
        """Dynamically load a component module"""
        # Implementation would use importlib to load modules
        # This is simplified for clarity
        raise NotImplementedError("Component loading to be implemented")

    async def _start_schedulers(self):
        """Start scheduled tasks"""
        for task_name, schedule in self._schedules.items():
            task = asyncio.create_task(self._run_scheduled_task(task_name, schedule))
            self._tasks.append(task)

    async def _run_scheduled_task(self, task_name: str, interval_seconds: int):
        """Run a scheduled task according to its interval"""
        while not self._shutdown_event.is_set():
            try:
                await self._execute_scheduled_task(task_name)
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduled task {task_name}: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _execute_scheduled_task(self, task_name: str):
        """Execute a specific scheduled task"""
        task_handlers = {
            "workspace_scan": self._trigger_workspace_scan,
            "performance_analysis": self._trigger_performance_analysis,
            "meta_learning": self._trigger_meta_learning,
            "archive_snapshot": self._trigger_archive,
            "health_check": self._perform_health_check,
        }

        handler = task_handlers.get(task_name)
        if handler:
            await handler()
        else:
            logger.warning(f"Unknown scheduled task: {task_name}")

    async def _trigger_workspace_scan(self):
        """Trigger a workspace scan"""
        await self.event_bus.publish(Event(
            type=EventType.SCAN_REQUESTED,
            source="orchestrator.scheduler",
            timestamp=datetime.utcnow(),
            data={"trigger": "scheduled", "task": "workspace_scan"}
        ))

    async def _trigger_performance_analysis(self):
        """Trigger performance analysis"""
        await self.event_bus.publish(Event(
            type=EventType.ANALYSIS_REQUESTED,
            source="orchestrator.scheduler",
            timestamp=datetime.utcnow(),
            data={"type": "performance", "period": "1h"}
        ))

    async def _trigger_meta_learning(self):
        """Trigger meta-learning cycle"""
        await self.event_bus.publish(Event(
            type=EventType.LEARNING_CYCLE,
            source="orchestrator.scheduler",
            timestamp=datetime.utcnow(),
            data={"trigger": "scheduled"}
        ))

    async def _trigger_archive(self):
        """Trigger archive snapshot"""
        await self.event_bus.publish(Event(
            type=EventType.ARCHIVE_REQUESTED,
            source="orchestrator.scheduler",
            timestamp=datetime.utcnow(),
            data={"type": "daily"}
        ))

    async def _perform_health_check(self):
        """Check health of all components"""
        for name, info in self.components.items():
            if not self._is_component_healthy(info):
                logger.warning(f"Component {name} appears unhealthy")
                # Could trigger restart or escalation

    def _is_component_healthy(self, info: ComponentInfo) -> bool:
        """Check if component is healthy"""
        time_since_heartbeat = (datetime.utcnow() - info.last_heartbeat).total_seconds()
        return time_since_heartbeat < 300 and info.state == ComponentState.RUNNING

    async def _handle_system_event(self, event: Event):
        """Handle critical system events"""
        if event.type == EventType.SYSTEM_SHUTDOWN:
            logger.info("Shutdown signal received")
            await self.shutdown()
        elif event.type == EventType.COMPONENT_ERROR:
            logger.error(f"Component error: {event.data}")
            # Could trigger recovery procedures

    async def _trigger_initial_scan(self):
        """Perform initial workspace scan on startup"""
        logger.info("Triggering initial workspace scan")
        await self._trigger_workspace_scan()

    async def run(self):
        """Main run loop"""
        await self.initialize()

        while not self._shutdown_event.is_set():
            try:
                # Process events, monitor components, etc.
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down JARVIS orchestrator")
        self._shutdown_event.set()

        # Cancel all scheduled tasks
        for task in self._tasks:
            task.cancel()

        # Stop all components in reverse order
        component_names = list(self.components.keys())[::-1]
        for name in component_names:
            try:
                component = self._load_component(name)
                await component.stop()
                logger.info(f"Stopped component: {name}")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

        # Stop event bus
        await self.event_bus.stop()

        logger.info("JARVIS orchestrator shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        uptime = 0
        if self.start_time is not None:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "state": self.state.value,
            "uptime": uptime,
            "components": {
                name: {
                    "state": info.state.value,
                    "last_heartbeat": info.last_heartbeat.isoformat(),
                    "health": self._is_component_healthy(info)
                }
                for name, info in self.components.items()
            },
            "event_queue_size": self.event_bus.qsize(),
        }


async def main():
    """Main entry point"""
    config = Config.load()
    orchestrator = Orchestrator(config)

    try:
        await orchestrator.run()
        # After successful run, set start_time (if not shutdown)
        if orchestrator.state == ComponentState.RUNNING:
            orchestrator.start_time = datetime.utcnow()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
