"""
Event Bus for JARVIS asynchronous communication.
Provides publish-subscribe pattern with async support.
"""
import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum


class EventType(Enum):
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"

    # Workspace events
    NEW_WORKSPACE = "new_workspace"
    SCAN_REQUESTED = "scan_requested"
    INTEGRATION_COMPLETE = "integration_complete"

    # Task events
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Learning events
    PATTERN_DISCOVERED = "pattern_discovered"
    PREFERENCE_UPDATED = "preference_updated"
    LEARNING_CYCLE = "learning_cycle"
    EVOLUTION_TRIGGERED = "evolution_triggered"

    # Performance events
    METRICS_COLLECTED = "metrics_collected"
    ANALYSIS_REQUESTED = "analysis_requested"
    TREND_DETECTED = "trend_detected"

    # MCP events
    SKILL_SELECTED = "skill_selected"
    CONTEXT_UPDATED = "context_updated"
    PLAN_CREATED = "plan_created"
    PLAN_EXECUTED = "plan_executed"

    # Modification events
    MODIFICATION_REQUESTED = "modification_requested"
    MODIFICATION_APPROVED = "modification_approved"
    MODIFICATION_REJECTED = "modification_rejected"
    MODIFICATION_COMPLETED = "modification_completed"

    # Account/Deal events
    DEAL_CREATED = "deal_created"
    DEAL_UPDATED = "deal_updated"
    PERSONA_SWITCHED = "persona_switched"
    FEEDBACK_RECEIVED = "feedback_received"

    # System events
    COMPONENT_ERROR = "component_error"
    COMPONENT_HEALTH = "component_health"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ARCHIVE_REQUESTED = "archive_requested"
    ERROR_OCCURRED = "error_occurred"
    USER_FEEDBACK = "user_feedback"


@dataclass
class Event:
    type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    priority: int = 1  # 1=low, 5=high

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventBus:
    """
    Asynchronous event bus for component communication.
    Supports synchronous and async subscribers with priority queues.
    """

    def __init__(self, max_size: int = 10000):
        self._queue = asyncio.Queue(maxsize=max_size)
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._event_counter = 0
        self._dropped_events = 0

    async def start(self):
        """Start the event bus processor"""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        print("Event bus started")

    async def stop(self):
        """Stop the event bus"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        print("Event bus stopped")

    def subscribe(self, subscriber_id: str, event_types: List[EventType], callback: Callable):
        """
        Subscribe to specific event types.

        Args:
            subscriber_id: Unique identifier for the subscriber
            event_types: List of event types to subscribe to
            callback: Async function to call when event occurs
        """
        for event_type in event_types:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, subscriber_id: str, event_types: Optional[List[EventType]] = None):
        """Unsubscribe from events"""
        # Implementation for unsubscribe
        pass

    async def publish(self, event: Event):
        """Publish an event to the bus"""
        try:
            self._queue.put_nowait(event)
            self._event_counter += 1
        except asyncio.QueueFull:
            self._dropped_events += 1
            print(f"Warning: Event queue full, dropping event {event.type}")

    async def publish_async(self, event: Event):
        """Alias for publish"""
        await self.publish(event)

    async def _process_events(self):
        """Main event processing loop"""
        while self._running or not self._queue.empty():
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")

    async def _dispatch_event(self, event: Event):
        """Dispatch event to all subscribers"""
        callbacks = self._subscribers.get(event.type, [])
        if not callbacks:
            # Debug: unknown event type
            return

        # Execute callbacks concurrently
        tasks = []
        for callback in callbacks:
            try:
                task = asyncio.create_task(callback(event))
                tasks.append(task)
            except Exception as e:
                print(f"Error creating task for callback: {e}")

        if tasks:
            # Wait for all tasks with timeout
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                print(f"Error in callback execution: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "events_processed": self._event_counter,
            "events_dropped": self._dropped_events,
            "queue_size": self._queue.qsize(),
            "subscriber_counts": {
                event_type.value: len(callbacks)
                for event_type, callbacks in self._subscribers.items()
            }
        }

    def qsize(self) -> int:
        """Get current queue size"""
        return self._queue.qsize()


# Decorator for easy subscription
def subscribes_to(event_types: List[EventType]):
    """Decorator to automatically subscribe a method to events"""
    def decorator(func):
        func._subscribes_to = event_types
        return func
    return decorator
