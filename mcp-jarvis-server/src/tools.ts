import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { execSync } from "child_process";
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

function ensureDir(dir: string) {
  fs.mkdirSync(dir, { recursive: true });
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
      : "No .md or .json files found in this directory.";
  } catch {
    return "Directory not found or unreadable.";
  }
}

async function searchFiles(
  baseDir: string,
  query: string
): Promise<{ file: string; snippet: string }[]> {
  const results: { file: string; snippet: string }[] = [];
  const lowerQuery = query.toLowerCase();
  try {
    const files = await glob("**/*.{md,json}", {
      cwd: baseDir,
      absolute: true,
    });
    for (const f of files) {
      const content = readFileOrNull(f);
      if (!content) continue;
      const lines = content.split("\n");
      for (let i = 0; i < lines.length; i++) {
        if (lines[i].toLowerCase().includes(lowerQuery)) {
          const start = Math.max(0, i - 1);
          const end = Math.min(lines.length, i + 2);
          results.push({
            file: path.relative(baseDir, f),
            snippet: lines.slice(start, end).join("\n"),
          });
          break; // one match per file is enough for listing
        }
      }
    }
  } catch {
    // directory may not exist yet
  }
  return results;
}

function timestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function dateStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function sanitize(s: string): string {
  return s.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 80);
}

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------

const TOOLS = [
  {
    name: "jarvis_setup",
    description:
      "Initialize JARVIS for first use OR check current configuration status. " +
      "Run this first when opening JARVIS with Claude or OpenCode. " +
      "Detects unconfigured state and guides you through setup interactively.",
    inputSchema: {
      type: "object" as const,
      properties: {
        action: {
          type: "string" as const,
          enum: ["check_status", "save_config"],
          description:
            "check_status: detect what is configured and what is missing. " +
            "save_config: write .env and generate config files from provided values.",
        },
        config: {
          type: "object" as const,
          description: "Required when action=save_config",
          properties: {
            nvidia_api_key: {
              type: "string" as const,
              description: "NVIDIA API key from build.nvidia.com",
            },
            jarvis_home: {
              type: "string" as const,
              description: "Where JARVIS stores your deal data (default: ~/JARVIS)",
            },
            claude_space: {
              type: "string" as const,
              description:
                "Your Claude/OpenCode workspace folder path (optional)",
            },
            anthropic_api_key: {
              type: "string" as const,
              description: "Anthropic API key (optional, only for Claude fallback)",
            },
          },
        },
      },
      required: ["action"],
    },
  },
  {
    name: "jarvis_list_accounts",
    description:
      "List all account folders tracked in JARVIS. Returns an array of account names.",
    inputSchema: {
      type: "object" as const,
      properties: {},
      required: [],
    },
  },
  {
    name: "jarvis_get_account",
    description:
      "Get the full deal dossier for a specific account. Reads all .md and .json files recursively and returns concatenated content.",
    inputSchema: {
      type: "object" as const,
      properties: {
        name: { type: "string" as const, description: "Account folder name" },
      },
      required: ["name"],
    },
  },
  {
    name: "jarvis_search",
    description:
      "Search all JARVIS data files (ACCOUNTS/ and MEMORY/) for a query string. Case-insensitive. Returns matching file paths and snippets.",
    inputSchema: {
      type: "object" as const,
      properties: {
        query: { type: "string" as const, description: "Search query" },
      },
      required: ["query"],
    },
  },
  {
    name: "jarvis_get_pipeline",
    description:
      "Get a pipeline summary across all accounts. Reads deal_stage.json and MEDDPICC data from each account.",
    inputSchema: {
      type: "object" as const,
      properties: {},
      required: [],
    },
  },
  {
    name: "jarvis_get_battlecard",
    description:
      "Get competitive intelligence / battlecard for a specific competitor.",
    inputSchema: {
      type: "object" as const,
      properties: {
        competitor: {
          type: "string" as const,
          description: "Competitor name (used to find the battlecard file)",
        },
      },
      required: ["competitor"],
    },
  },
  {
    name: "jarvis_process_meeting",
    description:
      "Submit a meeting recording for processing by the JARVIS Python daemon. Writes a processing request to the meeting queue.",
    inputSchema: {
      type: "object" as const,
      properties: {
        recording_path: {
          type: "string" as const,
          description: "Path to the meeting recording file",
        },
        account: {
          type: "string" as const,
          description: "Account name this meeting belongs to",
        },
        title: {
          type: "string" as const,
          description: "Meeting title",
        },
      },
      required: ["recording_path", "account", "title"],
    },
  },
  {
    name: "jarvis_save_meeting_context",
    description:
      "Save meeting notes for an account. Creates the meeting file in the account's meetings/ directory.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account name" },
        title: { type: "string" as const, description: "Meeting title" },
        date: {
          type: "string" as const,
          description: "Meeting date (YYYY-MM-DD)",
        },
        attendees: {
          type: "array" as const,
          items: { type: "string" as const },
          description: "List of attendees",
        },
        notes: {
          type: "string" as const,
          description: "Full meeting notes content",
        },
      },
      required: ["account", "title", "date", "attendees", "notes"],
    },
  },
  {
    name: "jarvis_save_email_context",
    description:
      "Save an email to an account's emails/ directory for future reference.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account name" },
        from_addr: { type: "string" as const, description: "Sender email" },
        to_addr: { type: "string" as const, description: "Recipient email" },
        subject: { type: "string" as const, description: "Email subject" },
        body: { type: "string" as const, description: "Email body" },
      },
      required: ["account", "from_addr", "to_addr", "subject", "body"],
    },
  },
  {
    name: "jarvis_prep_for_meeting",
    description:
      "Get or generate a meeting prep brief for an upcoming meeting. Returns existing prep if available, otherwise reads account data to help prepare.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account name" },
        title: { type: "string" as const, description: "Meeting title" },
        attendees: {
          type: "array" as const,
          items: { type: "string" as const },
          description: "Expected attendees",
        },
      },
      required: ["account", "title", "attendees"],
    },
  },
  {
    name: "jarvis_draft_followup",
    description:
      "Get or request a follow-up draft after a meeting. Returns existing draft if available, otherwise queues the request.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account name" },
        meeting_date: {
          type: "string" as const,
          description: "Date of the meeting (YYYY-MM-DD)",
        },
        context: {
          type: "string" as const,
          description:
            "Additional context or instructions for the follow-up draft",
        },
      },
      required: ["account", "meeting_date", "context"],
    },
  },
  {
    name: "jarvis_get_notifications",
    description:
      "Get pending JARVIS notifications and mark them as read. Returns any alerts, reminders, or status updates.",
    inputSchema: {
      type: "object" as const,
      properties: {},
      required: [],
    },
  },
];

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Setup helpers
// ---------------------------------------------------------------------------

function getRepoRoot(): string {
  // MCP server dist/ is at <repo>/mcp-jarvis-server/dist/
  // So: __dirname -> dist/, parent -> mcp-jarvis-server/, parent -> repo root
  return path.resolve(__dirname, "..", "..");
}

function checkJarvisStatus(): {
  configured: boolean;
  missing: string[];
  present: string[];
  jarvis_home: string;
  env_path: string;
} {
  const repoRoot = getRepoRoot();
  const envPath = path.join(repoRoot, ".env");
  const missing: string[] = [];
  const present: string[] = [];

  // Check .env file
  const envExists = fs.existsSync(envPath);
  if (envExists) {
    present.push(".env file");
  } else {
    missing.push(".env file (run ./setup.sh or use jarvis_setup save_config)");
  }

  // Check NVIDIA key
  const nvidiaKey = process.env.NVIDIA_API_KEY || "";
  if (nvidiaKey && nvidiaKey !== "YOUR_NVIDIA_API_KEY_HERE") {
    present.push("NVIDIA_API_KEY");
  } else {
    missing.push("NVIDIA_API_KEY (get from https://build.nvidia.com/)");
  }

  // Check JARVIS_HOME
  const jarvisHome = process.env.JARVIS_HOME || path.join(os.homedir(), "JARVIS");
  const jarvisHomeExists = fs.existsSync(jarvisHome);
  if (jarvisHomeExists) {
    present.push(`JARVIS_HOME (${jarvisHome})`);
  } else {
    missing.push(`JARVIS_HOME directory not created yet (will be at ${jarvisHome})`);
  }

  // Check ACCOUNTS directory
  const accountsPath = path.join(jarvisHome, "ACCOUNTS");
  if (fs.existsSync(accountsPath)) {
    present.push("ACCOUNTS/ directory");
  } else {
    missing.push("ACCOUNTS/ directory (created automatically by setup)");
  }

  return {
    configured: missing.length === 0,
    missing,
    present,
    jarvis_home: jarvisHome,
    env_path: envPath,
  };
}

export function registerTools(server: Server, dataDir: string) {
  const accountsDir = path.join(dataDir, "ACCOUNTS");
  const memoryDir = path.join(dataDir, "MEMORY");

  // List tools
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOLS,
  }));

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    switch (name) {
      // ---------------------------------------------------------------
      case "jarvis_setup": {
        const { action, config } = args as {
          action: "check_status" | "save_config";
          config?: {
            nvidia_api_key?: string;
            jarvis_home?: string;
            claude_space?: string;
            anthropic_api_key?: string;
          };
        };

        if (action === "check_status") {
          const status = checkJarvisStatus();

          if (status.configured) {
            return {
              content: [
                {
                  type: "text" as const,
                  text: [
                    "✅ JARVIS is configured and ready.",
                    "",
                    "**What's set up:**",
                    ...status.present.map((p) => `  • ${p}`),
                    "",
                    `**JARVIS Home:** ${status.jarvis_home}`,
                    "",
                    "**Quick commands:**",
                    "  • `jarvis_list_accounts` — see your accounts",
                    "  • `jarvis_get_pipeline` — see deal pipeline",
                    "  • Create a folder in ACCOUNTS/ → JARVIS auto-initializes it",
                    "",
                    "**To start JARVIS daemon:** run `./start_jarvis.sh` in the project folder",
                  ].join("\n"),
                },
              ],
            };
          }

          return {
            content: [
              {
                type: "text" as const,
                text: [
                  "⚠️ JARVIS needs setup. Here's what's missing:",
                  "",
                  ...status.missing.map((m) => `  ❌ ${m}`),
                  "",
                  "**What's already configured:**",
                  ...(status.present.length > 0
                    ? status.present.map((p) => `  ✅ ${p}`)
                    : ["  (nothing yet)"]),
                  "",
                  "─────────────────────────────────────────",
                  "**OPTION A — Guided setup (recommended for new users):**",
                  "",
                  "Please ask me the following questions one by one:",
                  "1. What is your NVIDIA API key? (get free key at https://build.nvidia.com/)",
                  "2. Where do you want JARVIS to store your deal data?",
                  "   (press Enter to use default: ~/JARVIS)",
                  "3. What is your Claude/OpenCode workspace folder path?",
                  "   (the folder where you use Claude Code/OpenCode — optional)",
                  "",
                  "Once you have the answers, call:",
                  "  `jarvis_setup(action='save_config', config={nvidia_api_key: '...', jarvis_home: '~/JARVIS', claude_space: '...'})`",
                  "",
                  "─────────────────────────────────────────",
                  "**OPTION B — Manual setup:**",
                  "  Run `./setup.sh` in the project folder — it will prompt for everything.",
                  "",
                  `**Project folder:** ${getRepoRoot()}`,
                ].join("\n"),
              },
            ],
          };
        }

        // action === "save_config"
        if (!config) {
          return {
            content: [
              {
                type: "text" as const,
                text: "Error: config object is required for save_config action.",
              },
            ],
            isError: true,
          };
        }

        const nvidiaKey = config.nvidia_api_key || "";
        const jarvisHome = config.jarvis_home
          ? config.jarvis_home.replace(/^~/, os.homedir())
          : path.join(os.homedir(), "JARVIS");
        const claudeSpace = config.claude_space
          ? config.claude_space.replace(/^~/, os.homedir())
          : "";
        const anthropicKey = config.anthropic_api_key || "";

        const repoRoot = getRepoRoot();
        const envPath = path.join(repoRoot, ".env");

        // Write .env
        const envContent = [
          "# JARVIS v2 — Configuration",
          "# Generated by jarvis_setup MCP tool",
          "",
          `NVIDIA_API_KEY=${nvidiaKey}`,
          `ANTHROPIC_API_KEY=${anthropicKey}`,
          `JARVIS_HOME=${jarvisHome}`,
          `CLAUDE_SPACE=${claudeSpace}`,
          "TELEGRAM_BOT_TOKEN=",
        ].join("\n");
        fs.writeFileSync(envPath, envContent);

        // Create directory structure
        const dirs = [
          "ACCOUNTS", "MEETINGS", "MEMORY", "MEMORY/patterns",
          "data/personas", "data/templates", "data/meeting_queue",
          "data/cache", "logs", "recordings",
          "ACCOUNTS/_template/MEETINGS", "ACCOUNTS/_template/DOCUMENTS",
          "ACCOUNTS/_template/EMAILS", "ACCOUNTS/_template/INTEL",
        ];
        for (const d of dirs) {
          fs.mkdirSync(path.join(jarvisHome, d), { recursive: true });
        }

        // Create ACCOUNTS/.claude/CLAUDE.md for when user opens ACCOUNTS in OpenCode
        const claudeMdDir = path.join(jarvisHome, "ACCOUNTS", ".claude");
        fs.mkdirSync(claudeMdDir, { recursive: true });
        fs.writeFileSync(
          path.join(claudeMdDir, "CLAUDE.md"),
          [
            "# ACCOUNTS — JARVIS Deal Intelligence",
            "",
            "This folder contains all your account and opportunity data.",
            "Each subfolder is one account or opportunity — create them freely.",
            "",
            "JARVIS monitors this folder automatically:",
            "- Drop a recording in MEETINGS/ → JARVIS transcribes and summarizes",
            "- Drop a document in DOCUMENTS/ → JARVIS extracts intelligence",
            "- Paste emails in EMAILS/ → JARVIS tracks sentiment and action items",
            "- INTEL/ is auto-generated by JARVIS — do not edit manually",
            "",
            "MCP tools are registered globally — you can ask Claude about any account here.",
            "",
            "**Quick commands to try:**",
            "  • 'list my accounts'",
            "  • 'show my pipeline'",
            "  • 'brief me on [account name]'",
          ].join("\n")
        );

        // Run generate_config.py to create jarvis.yaml and mcp configs
        let configGenOutput = "";
        try {
          const scriptPath = path.join(repoRoot, "scripts", "generate_config.py");
          const args = [
            `--jarvis-home="${jarvisHome}"`,
            claudeSpace ? `--claude-space="${claudeSpace}"` : "",
            nvidiaKey ? `--nvidia-key="${nvidiaKey}"` : "",
            anthropicKey ? `--anthropic-key="${anthropicKey}"` : "",
          ].filter(Boolean).join(" ");
          configGenOutput = execSync(`python3 ${scriptPath} ${args}`, {
            encoding: "utf-8",
            cwd: repoRoot,
            timeout: 30000,
          });
        } catch (e: any) {
          configGenOutput = `Config generation: ${e.message || String(e)}`;
        }

        return {
          content: [
            {
              type: "text" as const,
              text: [
                "✅ JARVIS configured successfully!",
                "",
                `**JARVIS Home:** ${jarvisHome}`,
                claudeSpace ? `**Claude Space:** ${claudeSpace}` : "",
                `**NVIDIA Key:** ${nvidiaKey ? "set (" + nvidiaKey.slice(0, 8) + "...)" : "NOT SET — please add manually to .env"}`,
                "",
                "**Next steps:**",
                "1. Start JARVIS: open a terminal in the project folder and run `./start_jarvis.sh`",
                "2. Create your first account: `mkdir ~/JARVIS/ACCOUNTS/YourAccountName`",
                "3. JARVIS will auto-initialize it within seconds",
                "",
                "**Config output:**",
                configGenOutput || "(no output)",
              ].filter(Boolean).join("\n"),
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_list_accounts": {
        const accounts = listDirs(accountsDir);
        return {
          content: [
            {
              type: "text" as const,
              text:
                accounts.length > 0
                  ? JSON.stringify(accounts, null, 2)
                  : "No accounts found. Create account folders in ACCOUNTS/ to get started.",
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_account": {
        const accountName = (args as { name: string }).name;
        const accountPath = path.join(accountsDir, accountName);
        if (!fs.existsSync(accountPath)) {
          return {
            content: [
              {
                type: "text" as const,
                text: `Account "${accountName}" not found. Available accounts: ${listDirs(accountsDir).join(", ") || "none"}`,
              },
            ],
          };
        }
        const dossier = await readAllFiles(accountPath);
        return {
          content: [{ type: "text" as const, text: dossier }],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_search": {
        const query = (args as { query: string }).query;
        const accountResults = await searchFiles(accountsDir, query);
        const memoryResults = await searchFiles(memoryDir, query);
        const all = [
          ...accountResults.map((r) => ({
            ...r,
            file: `ACCOUNTS/${r.file}`,
          })),
          ...memoryResults.map((r) => ({ ...r, file: `MEMORY/${r.file}` })),
        ];
        return {
          content: [
            {
              type: "text" as const,
              text:
                all.length > 0
                  ? JSON.stringify(all, null, 2)
                  : `No results found for "${query}".`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_pipeline": {
        const accounts = listDirs(accountsDir);
        const pipeline: Record<string, unknown>[] = [];
        for (const acct of accounts) {
          const entry: Record<string, unknown> = { account: acct };
          // Read deal_stage.json
          const stageFile = path.join(accountsDir, acct, "deal_stage.json");
          const stageContent = readFileOrNull(stageFile);
          if (stageContent) {
            try {
              entry.deal_stage = JSON.parse(stageContent);
            } catch {
              entry.deal_stage_raw = stageContent;
            }
          }
          // Read MEDDPICC data
          const meddpiccDir = path.join(accountsDir, acct, "meddpicc");
          if (
            fs.existsSync(meddpiccDir) &&
            fs.statSync(meddpiccDir).isDirectory()
          ) {
            const meddpiccContent = await readAllFiles(meddpiccDir);
            entry.meddpicc = meddpiccContent;
          }
          // Also check for meddpicc.json at account root
          const meddpiccFile = path.join(accountsDir, acct, "meddpicc.json");
          const meddpiccJson = readFileOrNull(meddpiccFile);
          if (meddpiccJson) {
            try {
              entry.meddpicc = JSON.parse(meddpiccJson);
            } catch {
              entry.meddpicc_raw = meddpiccJson;
            }
          }
          if (Object.keys(entry).length > 1) {
            pipeline.push(entry);
          }
        }
        return {
          content: [
            {
              type: "text" as const,
              text:
                pipeline.length > 0
                  ? JSON.stringify(pipeline, null, 2)
                  : "No pipeline data found. Add deal_stage.json or meddpicc/ folders to account directories.",
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_battlecard": {
        const competitor = (args as { competitor: string }).competitor;
        const competitorLower = competitor.toLowerCase();

        // Try exact path first
        const exactPath = path.join(
          memoryDir,
          "competitors",
          `${competitor}.json`
        );
        let content = readFileOrNull(exactPath);

        // Try lowercase
        if (!content) {
          const lowerPath = path.join(
            memoryDir,
            "competitors",
            `${competitorLower}.json`
          );
          content = readFileOrNull(lowerPath);
        }

        // Try .md variants
        if (!content) {
          content =
            readFileOrNull(
              path.join(memoryDir, "competitors", `${competitor}.md`)
            ) ||
            readFileOrNull(
              path.join(memoryDir, "competitors", `${competitorLower}.md`)
            );
        }

        // Search across all battlecard-like files
        if (!content) {
          const results = await searchFiles(memoryDir, competitor);
          if (results.length > 0) {
            content = JSON.stringify(results, null, 2);
          }
        }

        return {
          content: [
            {
              type: "text" as const,
              text:
                content ||
                `No battlecard found for "${competitor}". Create one at MEMORY/competitors/${competitorLower}.json`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_process_meeting": {
        const { recording_path, account, title } = args as {
          recording_path: string;
          account: string;
          title: string;
        };
        const queueDir = path.join(dataDir, "data", "meeting_queue");
        ensureDir(queueDir);

        const requestFile = path.join(queueDir, `${timestamp()}.json`);
        const request = {
          recording_path,
          account,
          title,
          submitted_at: new Date().toISOString(),
          status: "pending",
        };
        fs.writeFileSync(requestFile, JSON.stringify(request, null, 2));

        return {
          content: [
            {
              type: "text" as const,
              text: `Meeting processing request queued: ${path.basename(requestFile)}\nAccount: ${account}\nTitle: ${title}\nRecording: ${recording_path}\n\nThe JARVIS daemon will pick this up for transcription and analysis.`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_save_meeting_context": {
        const { account, title, date, attendees, notes } = args as {
          account: string;
          title: string;
          date: string;
          attendees: string[];
          notes: string;
        };
        const meetingsDir = path.join(accountsDir, account, "meetings");
        ensureDir(meetingsDir);

        const filename = `${date}_${sanitize(title)}.md`;
        const filePath = path.join(meetingsDir, filename);
        const content = `# ${title}\n\n**Date:** ${date}\n**Attendees:** ${attendees.join(", ")}\n\n## Notes\n\n${notes}\n`;
        fs.writeFileSync(filePath, content);

        return {
          content: [
            {
              type: "text" as const,
              text: `Meeting notes saved: ACCOUNTS/${account}/meetings/${filename}`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_save_email_context": {
        const { account, from_addr, to_addr, subject, body } = args as {
          account: string;
          from_addr: string;
          to_addr: string;
          subject: string;
          body: string;
        };
        const emailsDir = path.join(accountsDir, account, "emails");
        ensureDir(emailsDir);

        const date = dateStr();
        const filename = `${date}_${sanitize(subject)}.md`;
        const filePath = path.join(emailsDir, filename);
        const content = `# ${subject}\n\n**Date:** ${date}\n**From:** ${from_addr}\n**To:** ${to_addr}\n\n## Body\n\n${body}\n`;
        fs.writeFileSync(filePath, content);

        return {
          content: [
            {
              type: "text" as const,
              text: `Email saved: ACCOUNTS/${account}/emails/${filename}`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_prep_for_meeting": {
        const {
          account,
          title,
          attendees,
        } = args as {
          account: string;
          title: string;
          attendees: string[];
        };

        // Check for existing prep
        const prepsDir = path.join(accountsDir, account, "preps");
        const prepFile = path.join(prepsDir, `${sanitize(title)}.md`);
        const existingPrep = readFileOrNull(prepFile);
        if (existingPrep) {
          return {
            content: [
              {
                type: "text" as const,
                text: `## Existing Prep Found\n\n${existingPrep}`,
              },
            ],
          };
        }

        // Read account data for context
        const accountPath = path.join(accountsDir, account);
        if (!fs.existsSync(accountPath)) {
          return {
            content: [
              {
                type: "text" as const,
                text: `Account "${account}" not found. Cannot prepare brief.`,
              },
            ],
          };
        }
        const accountData = await readAllFiles(accountPath);

        // Write prep request
        const queueDir = path.join(dataDir, "data", "prep_queue");
        ensureDir(queueDir);
        const requestFile = path.join(queueDir, `${timestamp()}.json`);
        fs.writeFileSync(
          requestFile,
          JSON.stringify(
            {
              account,
              title,
              attendees,
              submitted_at: new Date().toISOString(),
              status: "pending",
            },
            null,
            2
          )
        );

        return {
          content: [
            {
              type: "text" as const,
              text: `## Meeting Prep Context for: ${title}\n\n**Account:** ${account}\n**Attendees:** ${attendees.join(", ")}\n\nPrep request queued. Here is the account data to prepare from:\n\n${accountData}`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_draft_followup": {
        const { account, meeting_date, context } = args as {
          account: string;
          meeting_date: string;
          context: string;
        };

        // Check for existing draft
        const draftsDir = path.join(accountsDir, account, "drafts");
        const draftFile = path.join(
          draftsDir,
          `followup_${meeting_date}.md`
        );
        const existingDraft = readFileOrNull(draftFile);
        if (existingDraft) {
          return {
            content: [
              {
                type: "text" as const,
                text: `## Existing Follow-up Draft\n\n${existingDraft}`,
              },
            ],
          };
        }

        // Queue the request
        const queueDir = path.join(dataDir, "data", "followup_queue");
        ensureDir(queueDir);
        const requestFile = path.join(queueDir, `${timestamp()}.json`);
        fs.writeFileSync(
          requestFile,
          JSON.stringify(
            {
              account,
              meeting_date,
              context,
              submitted_at: new Date().toISOString(),
              status: "pending",
            },
            null,
            2
          )
        );

        // Read meeting notes for context
        const meetingsDir = path.join(accountsDir, account, "meetings");
        let meetingNotes = "No meeting notes found for this date.";
        try {
          const files = fs.readdirSync(meetingsDir);
          const match = files.find((f) => f.startsWith(meeting_date));
          if (match) {
            meetingNotes =
              readFileOrNull(path.join(meetingsDir, match)) || meetingNotes;
          }
        } catch {
          // meetings dir may not exist
        }

        return {
          content: [
            {
              type: "text" as const,
              text: `Follow-up draft request queued for ${account} (meeting ${meeting_date}).\n\nContext: ${context}\n\n## Meeting Notes\n\n${meetingNotes}`,
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_notifications": {
        const notifFile = path.join(dataDir, "data", "notifications.json");
        const content = readFileOrNull(notifFile);

        if (!content) {
          return {
            content: [
              {
                type: "text" as const,
                text: "No notifications file found. All clear.",
              },
            ],
          };
        }

        let notifications: unknown[];
        try {
          const parsed = JSON.parse(content);
          notifications = Array.isArray(parsed)
            ? parsed
            : parsed.notifications || [];
        } catch {
          return {
            content: [
              {
                type: "text" as const,
                text: "Could not parse notifications file.",
              },
            ],
          };
        }

        const pending = notifications.filter(
          (n: any) => n.status !== "read"
        );

        if (pending.length === 0) {
          return {
            content: [
              { type: "text" as const, text: "No pending notifications." },
            ],
          };
        }

        // Mark as read
        const updated = notifications.map((n: any) => ({
          ...n,
          status: "read",
          read_at: new Date().toISOString(),
        }));

        try {
          ensureDir(path.dirname(notifFile));
          fs.writeFileSync(
            notifFile,
            JSON.stringify(
              Array.isArray(JSON.parse(content))
                ? updated
                : { notifications: updated },
              null,
              2
            )
          );
        } catch {
          // best effort
        }

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(pending, null, 2),
            },
          ],
        };
      }

      // ---------------------------------------------------------------
      default:
        return {
          content: [
            {
              type: "text" as const,
              text: `Unknown tool: ${name}`,
            },
          ],
          isError: true,
        };
    }
  });
}
