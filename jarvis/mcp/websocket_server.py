#!/usr/bin/env python3
"""
WebSocket Server - Real-time event streaming to UI dashboard.
"""

import asyncio
import json
import logging
from typing import Set
import websockets

# Support both old and new websockets API
try:
    from websockets.asyncio.server import serve
except ImportError:
    from websockets import serve

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class WebSocketServer:
    """WebSocket server that broadcasts JARVIS events to connected UI clients."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.host = "localhost"
        self.port = getattr(config, 'websocket_port', 8081)
        self.logger = JARVISLogger("websocket")
        self.clients = set()
        self._server = None
        self._running = False

    async def start(self):
        """Start the WebSocket server."""
        self.logger.info("Starting WebSocket server", host=self.host, port=self.port)
        self._running = True

        # Subscribe to all events on the event bus
        self.event_bus.subscribe_all(self._broadcast_event)

        # Start server
        self._server = await serve(
            self._handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=30
        )
        self.logger.info("WebSocket server started", url=f"ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self.logger.info("WebSocket server stopped")

    async def _handler(self, websocket):
        """Handle new WebSocket connections."""
        self.clients.add(websocket)
        self.logger.debug("Client connected", clients_count=len(self.clients))

        try:
            # Send initial state
            await self._send_initial_state(websocket)

            # Keep connection alive
            async for message in websocket:
                # Handle messages from UI (e.g., commands)
                await self._handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            self.logger.debug("Client disconnected")
        finally:
            self.clients.discard(websocket)

    async def _send_initial_state(self, websocket):
        """Send initial system state to newly connected client."""
        state = {
            "type": "system.initial",
            "data": {
                "status": "connected",
                "server_time": asyncio.get_event_loop().time(),
                "clients_count": len(self.clients)
            }
        }
        try:
            await websocket.send(json.dumps(state))
        except:
            pass

    async def _handle_client_message(self, websocket, message: str):
        """Handle messages from UI client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            payload = data.get("data", {})

            if msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong", "data": payload}))
            elif msg_type == "command":
                # Could trigger actions via event bus
                self.logger.debug("Received command", command=payload.get("action"))
        except json.JSONDecodeError:
            self.logger.warning("Invalid WebSocket message received")

    async def _broadcast_event(self, event: Event):
        """Broadcast event to all connected clients."""
        if not self.clients:
            return

        message = {
            "type": event.type,
            "source": event.source,
            "data": event.data,
            "timestamp": event.timestamp
        }

        await self._send_to_clients(message)

    async def _send_to_clients(self, message: dict):
        """Send message to all connected clients."""
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                self.logger.error("Failed to send to client", error=str(e))
                disconnected.add(client)

        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)