import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerTools } from "./tools";
import { registerResources } from "./resources";
import * as path from "path";
import * as os from "os";

const JARVIS_DATA_DIR =
  process.env.JARVIS_DATA_DIR ||
  path.join(os.homedir(), "Documents", "claude space", "JARVIS");

async function main() {
  const server = new Server(
    {
      name: "mcp-jarvis-server",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
        resources: {},
      },
    }
  );

  registerTools(server, JARVIS_DATA_DIR);
  registerResources(server, JARVIS_DATA_DIR);

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error(`JARVIS MCP Server running. Data dir: ${JARVIS_DATA_DIR}`);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
