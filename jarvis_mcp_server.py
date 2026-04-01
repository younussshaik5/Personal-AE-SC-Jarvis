#!/usr/bin/env python3
"""
JARVIS MCP Server - Proper MCP Protocol Implementation
Communicates with Claude Desktop via stdio using MCP protocol
"""

import json
import sys
import asyncio
from typing import Any, Optional
import logging

# Setup logging (writes to stderr, doesn't interfere with MCP protocol on stdout)
logging.basicConfig(
    level=logging.INFO,
    format='[JARVIS MCP] %(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

from jarvis_mcp.mcp_server import JarvisServer


class MCPServerProtocol:
    """Implements MCP protocol for Claude Desktop communication"""

    def __init__(self):
        self.server = None
        self.request_id_counter = 0
        logger.info("Initializing JARVIS MCP Server Protocol...")

    async def initialize(self):
        """Initialize the JARVIS server"""
        try:
            self.server = JarvisServer()
            logger.info(f"✅ JARVIS Server initialized with {len(self.server.skills)} skills")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            return False

    def write_response(self, response: dict) -> None:
        """Write MCP response to stdout"""
        try:
            json.dump(response, sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Failed to write response: {e}")

    async def handle_initialize(self, params: dict) -> dict:
        """Handle MCP initialize request"""
        logger.info("Received initialize request")

        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "jarvis",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }

    async def handle_list_tools(self, params: Optional[dict]) -> dict:
        """Handle list tools request"""
        if not self.server:
            return {"tools": []}

        tools = []
        tool_list = self.server._get_tool_list()

        for tool_name in tool_list:
            tools.append({
                "name": tool_name,
                "description": f"JARVIS skill: {tool_name}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "account_name": {
                            "type": "string",
                            "description": "Account name"
                        },
                        "input": {
                            "type": "string",
                            "description": "Skill input"
                        }
                    },
                    "required": []
                }
            })

        logger.info(f"Listed {len(tools)} tools")
        return {"tools": tools}

    async def handle_call_tool(self, params: dict) -> dict:
        """Handle tool call request"""
        tool_name = params.get("name")
        tool_input = params.get("input", {})

        logger.info(f"Calling tool: {tool_name}")

        if not self.server:
            return {
                "type": "text",
                "text": "Server not initialized"
            }

        try:
            # Execute the skill
            if hasattr(self.server, tool_name):
                skill_method = getattr(self.server, tool_name)
                result = await skill_method(tool_input) if asyncio.iscoroutinefunction(skill_method) else skill_method(tool_input)

                return {
                    "type": "text",
                    "text": str(result)
                }
            else:
                return {
                    "type": "text",
                    "text": f"Tool '{tool_name}' not found"
                }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "type": "text",
                "text": f"Error: {str(e)}"
            }

    async def process_request(self, request: dict) -> dict:
        """Process incoming MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.info(f"Processing: {method}")

        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            else:
                result = {"error": f"Unknown method: {method}"}

            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

        return response

    async def run(self):
        """Main server loop - read from stdin, write to stdout"""
        # Initialize server
        if not await self.initialize():
            logger.error("Failed to initialize, exiting")
            return

        logger.info("JARVIS MCP Server ready, listening for requests...")

        # Process requests from stdin
        loop = asyncio.get_event_loop()

        while True:
            try:
                # Read line from stdin
                line = await loop.run_in_executor(None, sys.stdin.readline)

                if not line:
                    logger.info("EOF on stdin, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse JSON request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

                # Process request
                response = await self.process_request(request)

                # Write response
                self.write_response(response)

            except KeyboardInterrupt:
                logger.info("Interrupted, shutting down")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue


async def main():
    """Main entry point"""
    protocol = MCPServerProtocol()
    await protocol.run()


if __name__ == "__main__":
    asyncio.run(main())
