#!/usr/bin/env python3
"""
Asynchronous event bus for inter-component communication using asyncio.
"""

import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class Event:
    """Represents an event in the system."""
    type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            import time
            self.timestamp = time.time()


class EventBus:
    """Central asynchronous event bus with subscription management."""

    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self._global_subscribers: Set[Callable] = set()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the event processing loop."""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        return self

    async def stop(self):
        """Stop the event bus."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

    def publish(self, event: Event):
        """Publish an event to the bus (non-blocking)."""
        self._queue.put_nowait(event)

    async def publish_async(self, event: Event):
        """Publish an event to the bus (async)."""
        await self._queue.put(event)

    def subscribe(self, event_type: str, callback: Callable[[Event], Any]):
        """Subscribe to a specific event type."""
        self._subscribers[event_type].add(callback)
        # If already running, ensure callback receives a callable context
        if asyncio.iscoroutinefunction(callback):
            # For async callbacks, nothing extra
            pass
        else:
            # Wrap sync callbacks to run in executor
            async def wrapper(event):
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, callback, event)
            self._subscribers[event_type].add(wrapper)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove a subscription."""
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)

    def subscribe_all(self, callback: Callable[[Event], Any]):
        """Subscribe to all events (global subscriber)."""
        self._global_subscribers.add(callback)

    async def _process_events(self):
        """Main event processing loop."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            # Notify specific subscribers
            callbacks = list(self._subscribers.get(event.type, []))
            callbacks.extend(self._global_subscribers)

            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(event))
                    else:
                        # Run synchronous callbacks in thread pool
                        loop = asyncio.get_event_loop()
                        loop.run_in_executor(None, callback, event)
                except Exception as e:
                    # Log but don't crash the processor
                    print(f"[EventBus] Error in callback {callback}: {e}")

            self._queue.task_done()

    def get_queue_size(self) -> int:
        """Get number of pending events."""
        return self._queue.qsize()


# Global bus instance
event_bus = EventBus()