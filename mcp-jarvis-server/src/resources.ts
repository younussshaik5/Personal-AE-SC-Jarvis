import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListResourceTemplatesRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as path from "path";
import { glob } from "glob";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function readFileOrNull(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }
}

function listDirs(dir: string): string[] {
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
  } catch {
    return [];
  }
}

async function readAllFiles(dir: string): Promise<string> {
  try {
    const files = await glob("**/*.{md,json}", { cwd: dir, absolute: true });
    const parts: string[] = [];
    for (const f of files) {
      const rel = path.relative(dir, f);
      const content = readFileOrNull(f);
      if (content) {
        parts.push(`--- ${rel} ---\n${content}`);
      }
    }
    return parts.length > 0
      ? parts.join("\n\n")
      : "No data files found.";
  } catch {
    return "Directory not found or unreadable.";
  }
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

export function registerResources(server: Server, dataDir: string) {
  const accountsDir = path.join(dataDir, "ACCOUNTS");
  const memoryDir = path.join(dataDir, "MEMORY");

  // Resource templates
  server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
    resourceTemplates: [
      {
        uriTemplate: "jarvis://accounts/{name}/summary",
        name: "Account Summary",
        description: "Summary and key data for a specific account",
        mimeType: "text/plain",
      },
      {
        uriTemplate: "jarvis://accounts/{name}/meddpicc",
        name: "Account MEDDPICC",
        description: "MEDDPICC qualification data for a specific account",
        mimeType: "text/plain",
      },
      {
        uriTemplate: "jarvis://competitors/{name}",
        name: "Competitor Battlecard",
        description: "Competitive intelligence for a specific competitor",
        mimeType: "text/plain",
      },
    ],
  }));

  // Static resources
  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    const accounts = listDirs(accountsDir);
    const resources: Array<{
      uri: string;
      name: string;
      description: string;
      mimeType: string;
    }> = [];

    // Pipeline resource (always available)
    resources.push({
      uri: "jarvis://pipeline",
      name: "Sales Pipeline",
      description: "Full pipeline view across all accounts",
      mimeType: "text/plain",
    });

    // Per-account resources
    for (const acct of accounts) {
      resources.push({
        uri: `jarvis://accounts/${acct}/summary`,
        name: `${acct} - Summary`,
        description: `Account summary for ${acct}`,
        mimeType: "text/plain",
      });
      resources.push({
        uri: `jarvis://accounts/${acct}/meddpicc`,
        name: `${acct} - MEDDPICC`,
        description: `MEDDPICC data for ${acct}`,
        mimeType: "text/plain",
      });
    }

    // Competitor resources
    const competitorsDir = path.join(memoryDir, "competitors");
    try {
      const files = fs.readdirSync(competitorsDir);
      for (const f of files) {
        const name = path.basename(f, path.extname(f));
        resources.push({
          uri: `jarvis://competitors/${name}`,
          name: `Competitor: ${name}`,
          description: `Battlecard for ${name}`,
          mimeType: "text/plain",
        });
      }
    } catch {
      // competitors dir may not exist yet
    }

    return { resources };
  });

  // Read resource
  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = request.params.uri;

    // jarvis://pipeline
    if (uri === "jarvis://pipeline") {
      const accounts = listDirs(accountsDir);
      const pipeline: Record<string, unknown>[] = [];
      for (const acct of accounts) {
        const entry: Record<string, unknown> = { account: acct };
        const stageFile = path.join(accountsDir, acct, "deal_stage.json");
        const stageContent = readFileOrNull(stageFile);
        if (stageContent) {
          try {
            entry.deal_stage = JSON.parse(stageContent);
          } catch {
            entry.deal_stage_raw = stageContent;
          }
        }
        const meddpiccFile = path.join(accountsDir, acct, "meddpicc.json");
        const meddpiccContent = readFileOrNull(meddpiccFile);
        if (meddpiccContent) {
          try {
            entry.meddpicc = JSON.parse(meddpiccContent);
          } catch {
            entry.meddpicc_raw = meddpiccContent;
          }
        }
        const meddpiccDir = path.join(accountsDir, acct, "meddpicc");
        if (
          fs.existsSync(meddpiccDir) &&
          fs.statSync(meddpiccDir).isDirectory()
        ) {
          entry.meddpicc_details = await readAllFiles(meddpiccDir);
        }
        if (Object.keys(entry).length > 1) {
          pipeline.push(entry);
        }
      }
      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text:
              pipeline.length > 0
                ? JSON.stringify(pipeline, null, 2)
                : "No pipeline data available.",
          },
        ],
      };
    }

    // jarvis://accounts/{name}/summary
    const summaryMatch = uri.match(
      /^jarvis:\/\/accounts\/([^/]+)\/summary$/
    );
    if (summaryMatch) {
      const accountName = decodeURIComponent(summaryMatch[1]);
      const accountPath = path.join(accountsDir, accountName);

      // Try summary.md first, then fall back to all files
      const summaryFile = path.join(accountPath, "summary.md");
      let text = readFileOrNull(summaryFile);
      if (!text) {
        text = await readAllFiles(accountPath);
      }

      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text: text || `No data found for account "${accountName}".`,
          },
        ],
      };
    }

    // jarvis://accounts/{name}/meddpicc
    const meddpiccMatch = uri.match(
      /^jarvis:\/\/accounts\/([^/]+)\/meddpicc$/
    );
    if (meddpiccMatch) {
      const accountName = decodeURIComponent(meddpiccMatch[1]);

      // Try meddpicc.json
      const meddpiccFile = path.join(
        accountsDir,
        accountName,
        "meddpicc.json"
      );
      let text = readFileOrNull(meddpiccFile);

      // Try meddpicc/ directory
      if (!text) {
        const meddpiccDir = path.join(accountsDir, accountName, "meddpicc");
        if (
          fs.existsSync(meddpiccDir) &&
          fs.statSync(meddpiccDir).isDirectory()
        ) {
          text = await readAllFiles(meddpiccDir);
        }
      }

      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text:
              text ||
              `No MEDDPICC data found for "${accountName}". Create meddpicc.json or meddpicc/ folder in the account directory.`,
          },
        ],
      };
    }

    // jarvis://competitors/{name}
    const competitorMatch = uri.match(
      /^jarvis:\/\/competitors\/([^/]+)$/
    );
    if (competitorMatch) {
      const competitorName = decodeURIComponent(competitorMatch[1]);
      const competitorsDir = path.join(memoryDir, "competitors");

      const text =
        readFileOrNull(
          path.join(competitorsDir, `${competitorName}.json`)
        ) ||
        readFileOrNull(
          path.join(competitorsDir, `${competitorName}.md`)
        ) ||
        readFileOrNull(
          path.join(
            competitorsDir,
            `${competitorName.toLowerCase()}.json`
          )
        ) ||
        readFileOrNull(
          path.join(
            competitorsDir,
            `${competitorName.toLowerCase()}.md`
          )
        );

      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text:
              text ||
              `No competitive intel found for "${competitorName}".`,
          },
        ],
      };
    }

    // Unknown resource
    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: `Unknown resource: ${uri}`,
        },
      ],
    };
  });
}
