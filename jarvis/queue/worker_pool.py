#!/usr/bin/env python3
"""
JARVIS Worker Pool — N concurrent async workers consuming from TaskQueue.

Each worker:
  1. Pulls highest-priority task from queue
  2. Calls the registered handler for that task type
  3. Marks task complete (or failed with retry)
  4. Immediately pulls next task — no idle sleeping

Why N=3 workers by default:
  NVIDIA API has rate limits. 3 parallel requests is a safe default.
  Configurable via jarvis.yaml: queue.workers (1-10)

Context preservation:
  Full task payload (JSON) is passed to the handler.
  Handler writes results to files and publishes events.
  No context is held in memory across task boundaries — everything on disk.

Adding a new task type:
  pool.register("my_task_type", my_async_handler_fn)
  handler signature: async def handler(task: Task, services: dict) -> None
"""

import asyncio
from typing import Any, Callable, Dict, Optional

from jarvis.queue.task_queue import Task, TaskQueue
from jarvis.utils.logger import JARVISLogger


HandlerFn = Callable[[Task, Dict[str, Any]], Any]


class WorkerPool:
    """
    Pool of N async workers consuming tasks from a shared TaskQueue.
    Handlers are registered by task type and called with full task + services dict.
    """

    def __init__(self, queue: TaskQueue, n_workers: int = 3):
        self.queue     = queue
        self.n_workers = n_workers
        self.logger    = JARVISLogger("queue.worker_pool")
        self._handlers: Dict[str, HandlerFn] = {}
        self._services: Dict[str, Any] = {}
        self._tasks: list[asyncio.Task] = []
        self._running = False

    def register(self, task_type: str, handler: HandlerFn):
        """Register a handler for a task type."""
        self._handlers[task_type] = handler
        self.logger.debug("Handler registered", task_type=task_type)

    def set_services(self, services: Dict[str, Any]):
        """Inject shared services (llm_client, event_bus, etc.) into handlers."""
        self._services = services

    async def start(self):
        """Start N worker coroutines."""
        self._running = True
        for i in range(self.n_workers):
            t = asyncio.create_task(self._worker_loop(i), name=f"jarvis-worker-{i}")
            self._tasks.append(t)
        # Cleanup task — runs every hour
        self._tasks.append(asyncio.create_task(self._cleanup_loop(), name="jarvis-queue-cleanup"))
        self.logger.info("Worker pool started", workers=self.n_workers)

    async def stop(self):
        """Stop all workers gracefully."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        self.logger.info("Worker pool stopped")

    async def _worker_loop(self, worker_id: int):
        """Single worker: pull → handle → repeat."""
        self.logger.debug("Worker started", worker_id=worker_id)
        while self._running:
            task = await self.queue.dequeue()

            if task is None:
                # Nothing to do — wait for notification or timeout
                await self.queue.wait_for_work(timeout=5.0)
                continue

            handler = self._handlers.get(task.type)
            if not handler:
                self.logger.warning("No handler for task type", type=task.type)
                await self.queue.complete(task.id)
                continue

            self.logger.debug("Processing task",
                               worker=worker_id, type=task.type,
                               account=task.account, id=task.id[:8])
            try:
                await handler(task, self._services)
                await self.queue.complete(task.id)
                self.logger.debug("Task completed",
                                   worker=worker_id, type=task.type,
                                   account=task.account)
            except Exception as e:
                self.logger.error("Task handler error",
                                   worker=worker_id, type=task.type,
                                   account=task.account, error=str(e))
                await self.queue.fail(task.id, str(e))

            # Small pause between tasks — rate limiting for NVIDIA API
            await asyncio.sleep(0.5)

    async def _cleanup_loop(self):
        """Remove old completed/failed tasks every hour."""
        while self._running:
            await asyncio.sleep(3600)
            await self.queue.cleanup_old(max_age_hours=24)
            stats = await self.queue.stats()
            self.logger.info("Queue stats", **stats)
