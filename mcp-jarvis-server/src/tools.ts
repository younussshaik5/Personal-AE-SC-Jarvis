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
      "Get the full deal dossier for a specific account. If no name is provided, attempts to infer the current account from the workspace directory (must be inside ACCOUNTS/<account>/). Reads all .md and .json files recursively and returns concatenated content.",
    inputSchema: {
      type: "object" as const,
      properties: {
        name: { type: "string" as const, description: "Account folder name (optional if called from within an account folder)" },
      },
      required: [],  // name is optional
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
  {
    name: "jarvis_find_account",
    description:
      "Fuzzy-match a company name to an existing ACCOUNTS/ folder. " +
      "Use this when you read a Gmail, calendar event, or Drive doc and need to find " +
      "the right JARVIS account folder. Returns the best match and a confidence score. " +
      "Always call this before saving Google Workspace data to JARVIS.",
    inputSchema: {
      type: "object" as const,
      properties: {
        name: {
          type: "string" as const,
          description: "Company or account name to search for (e.g. 'Tata Sky Limited')",
        },
      },
      required: ["name"],
    },
  },
  {
    name: "jarvis_log_calendar_event",
    description:
      "Save a Google Calendar meeting to the right JARVIS account. " +
      "Call this when you see a calendar event that relates to a deal or account. " +
      "JARVIS will queue meeting prep automatically if the event is upcoming.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: {
          type: "string" as const,
          description: "Account folder name (use jarvis_find_account first if unsure)",
        },
        title: { type: "string" as const, description: "Meeting title from calendar" },
        date: { type: "string" as const, description: "Meeting date (YYYY-MM-DD)" },
        time: { type: "string" as const, description: "Meeting time (HH:MM)" },
        attendees: {
          type: "array" as const,
          items: { type: "string" as const },
          description: "Attendee names and emails from the calendar event",
        },
        description: {
          type: "string" as const,
          description: "Calendar event description or agenda (optional)",
        },
        is_upcoming: {
          type: "boolean" as const,
          description: "True if meeting is in the future (triggers auto-prep)",
        },
      },
      required: ["account", "title", "date", "attendees"],
    },
  },
  {
    name: "jarvis_save_google_email",
    description:
      "Save a Gmail thread to the right JARVIS account for intelligence extraction. " +
      "Call this automatically whenever you read an email related to a deal or account. " +
      "JARVIS will extract sentiment, objections, buying signals, and action items.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: {
          type: "string" as const,
          description: "Account folder name (use jarvis_find_account first if unsure)",
        },
        subject: { type: "string" as const, description: "Email subject line" },
        from_name: { type: "string" as const, description: "Sender name" },
        from_email: { type: "string" as const, description: "Sender email address" },
        date: { type: "string" as const, description: "Email date (YYYY-MM-DD)" },
        body: { type: "string" as const, description: "Full email body or thread content" },
        thread_summary: {
          type: "string" as const,
          description: "Optional 1-2 line summary of what this email is about",
        },
      },
      required: ["account", "subject", "from_email", "date", "body"],
    },
  },
  {
    name: "jarvis_save_drive_document",
    description:
      "Save a Google Drive document (RFP, proposal, contract, brief) to the right JARVIS account. " +
      "Call this when you read a Drive document related to a deal. " +
      "JARVIS will extract requirements, budget, timeline, and stakeholders.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: {
          type: "string" as const,
          description: "Account folder name (use jarvis_find_account first if unsure)",
        },
        title: { type: "string" as const, description: "Document title" },
        doc_type: {
          type: "string" as const,
          enum: ["rfp", "proposal", "contract", "brief", "presentation", "other"],
          description: "Type of document",
        },
        content: {
          type: "string" as const,
          description: "Full document content or extracted text",
        },
        drive_url: {
          type: "string" as const,
          description: "Google Drive URL for reference (optional)",
        },
      },
      required: ["account", "title", "doc_type", "content"],
    },
  },
  // -------------------------------------------------------------------------
  // Presales Intelligence Tools (AE + SC combined role)
  // -------------------------------------------------------------------------
  {
    name: "jarvis_get_discovery",
    description:
      "Get discovery prep questions and final discovery notes for an account. " +
      "Returns discovery_prep.md (questions JARVIS generated) + final_discovery.md (your notes). " +
      "Call before any discovery call or when you need to review what's been discovered.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  {
    name: "jarvis_update_discovery",
    description:
      "Save final discovery notes after a discovery call. " +
      "Appends to final_discovery.md (never overwrites — full history preserved). " +
      "Triggers cascade: demo strategy + value architecture auto-refresh.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
        notes: { type: "string" as const, description: "Discovery notes to save" },
        attendees: { type: "string" as const, description: "Attendees at the call (optional)" },
        pain_points: { type: "string" as const, description: "Pain points confirmed (optional)" },
        budget_signal: { type: "string" as const, description: "Budget signals mentioned (optional)" },
        champion: { type: "string" as const, description: "Potential champion identified (optional)" },
        next_step: { type: "string" as const, description: "Agreed next step (optional)" },
      },
      required: ["account", "notes"],
    },
  },
  {
    name: "jarvis_fill_rfi",
    description:
      "Trigger RFP analysis for an account and return the analysis for Claude to complete. " +
      "Returns rfi_analysis.md (requirements map) and rfi_responses.md (draft responses). " +
      "Call when user drops an RFP or asks you to fill/respond to an RFP.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  {
    name: "jarvis_get_battlecard_full",
    description:
      "Get the full battlecard for an account: competitive positioning, differentiators, " +
      "trap questions, objection responses, win probability. " +
      "Returns both battlecard.md (readable) and battlecard_data.json (for PPT/Excel creation). " +
      "Use this before a competitive call or demo.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  {
    name: "jarvis_get_demo_strategy",
    description:
      "Get the demo strategy and script for an account. " +
      "Returns demo_strategy.md (flow, use cases, narrative) and demo_script.md (line-by-line). " +
      "Call before a demo to prepare the narrative and know which use cases to show.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  {
    name: "jarvis_get_risk_report",
    description:
      "Get the current risk report for a deal. " +
      "Returns risk_report.md with MEDDPICC gaps, activity counts, stakeholders, and risk signals. " +
      "Updated weekly automatically. Use for deal reviews or manager check-ins.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  {
    name: "jarvis_update_risk_report",
    description:
      "Append a weekly update entry to the risk report. " +
      "Format: [Initials] [Date] — appends to existing file, never overwrites. " +
      "Call after a deal review meeting or weekly pipeline review.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
        update: { type: "string" as const, description: "Weekly update content to append" },
        initials: { type: "string" as const, description: "Your initials (e.g. SY)" },
      },
      required: ["account", "update"],
    },
  },
  {
    name: "jarvis_get_next_steps",
    description:
      "Get email drafts and next step recommendations for the current deal stage. " +
      "Returns next_steps.md with two email options (direct + consultative) " +
      "personalized to the account. Use after any meeting or when stuck on follow-up.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  {
    name: "jarvis_get_value_architecture",
    description:
      "Get the ROI model, TCO analysis, and structured value data for an account. " +
      "Returns roi_model.md, tco_analysis.md, and value_data.json. " +
      "Use this to build executive business case, create Excel/PPT value decks. " +
      "NOTE: When creating Excel/PPT from value_data.json, use claude-haiku or claude-sonnet only.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  // ── Architecture Diagram ────────────────────────────────────────────────
  {
    name: "jarvis_get_architecture_diagram",
    description:
      "Get the Mermaid.js solution architecture diagram for an account. " +
      "Returns the raw Mermaid source + path to the standalone HTML file. " +
      "Use this to share architecture with the customer or include in a presentation.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  // ── Proposal ───────────────────────────────────────────────────────────
  {
    name: "jarvis_get_proposal",
    description:
      "Get the current proposal for an account. Returns the proposal HTML path and " +
      "structured proposal_data.json. Open the HTML in a browser to edit pricing, " +
      "discounts, and send to the customer. Use claude-haiku or claude-sonnet only for any doc generation.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
    },
  },
  // ── Save Conversation ───────────────────────────────────────────────────────
  {
    name: "jarvis_save_conversation",
    description:
      "Save a conversation snippet to JARVIS_BRAIN.md for intelligence routing. " +
      "This allows JARVIS to extract account context, contacts, MEDDPICC signals, and action items. " +
      "If account is not provided, JARVIS will attempt to infer it from the current workspace.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name (optional if called from inside an account folder)" },
        role: { type: "string" as const, description: "Role: 'user' or 'assistant'" },
        content: { type: "string" as const, description: "Conversation content (message text)" },
        model: { type: "string" as const, description: "Model ID used (optional)" },
      },
      required: ["role", "content"],
    },
  },
  // ── Trigger Skill ──────────────────────────────────────────────────────────
  {
    name: "jarvis_trigger_skill",
    description:
      "Trigger a JARVIS background skill to regenerate an intelligence file for an account. " +
      "Use this after saving discovery notes, updating MEDDPICC, or when a file needs refreshing. " +
      "Skills: battlecard, discovery, demo_strategy, risk_report, value_architecture, proposal, sow, architecture_diagram, summary. " +
      "JARVIS orchestrator picks this up within seconds and regenerates the relevant files.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
        skill: {
          type: "string" as const,
          description: "Skill to trigger",
          enum: ["battlecard", "discovery", "demo_strategy", "risk_report", "value_architecture", "proposal", "sow", "architecture_diagram", "summary"],
        },
        reason: { type: "string" as const, description: "Why the skill should run (optional — logged for context)" },
      },
      required: ["account", "skill"],
    },
  },
  // ── SOW ────────────────────────────────────────────────────────────────
  {
    name: "jarvis_get_sow",
    description:
      "Get the Scope of Work document for an account. Returns the full SOW markdown with " +
      "all sections: objectives, deliverables, timeline, roles, success metrics, commercial terms.",
    inputSchema: {
      type: "object" as const,
      properties: {
        account: { type: "string" as const, description: "Account folder name" },
      },
      required: ["account"],
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
        let accountName = (args as { name?: string }).name;
        // If no name provided, try to infer from current workspace stored in context.json
        if (!accountName) {
          try {
            const contextPath = path.join(dataDir, "cache", "context.json");
            if (fs.existsSync(contextPath)) {
              const ctx = JSON.parse(fs.readFileSync(contextPath, "utf-8"));
              const workspace = ctx.current_workspace || "";
              // If workspace is under ACCOUNTS/<account>, extract account name
              const accountsAbs = path.resolve(accountsDir);
              const workspaceAbs = path.resolve(workspace);
              if (workspaceAbs.startsWith(accountsAbs + path.sep) || workspaceAbs === accountsAbs) {
                const rel = path.relative(accountsAbs, workspaceAbs);
                const firstSegment = rel.split(path.sep)[0];
                // Verify it's an existing account folder
                if (fs.existsSync(path.join(accountsDir, firstSegment))) {
                  accountName = firstSegment;
                }
              }
            }
          } catch (e) {
            // ignore and fall back to error message
          }
        }
        if (!accountName) {
          return {
            content: [
              {
                type: "text" as const,
                text: `No account name provided and current workspace is not inside an ACCOUNTS/ folder. Available accounts: ${listDirs(accountsDir).join(", ") || "none"}`,
              },
            ],
          };
        }
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
        const emailsDir = path.join(accountsDir, account, "EMAILS");
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
              text: `Email saved: ACCOUNTS/${account}/EMAILS/${filename}`,
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
      case "jarvis_find_account": {
        const { name: searchName } = args as { name: string };
        const accounts = listDirs(accountsDir);

        if (accounts.length === 0) {
          return {
            content: [{ type: "text" as const, text: JSON.stringify({ match: null, confidence: 0, all_accounts: [], message: "No accounts found. Create a folder in ACCOUNTS/ first." }) }],
          };
        }

        const lower = searchName.toLowerCase().replace(/[^a-z0-9]/g, "");

        // Score each account
        const scored = accounts.map((acct) => {
          const acctLower = acct.toLowerCase().replace(/[^a-z0-9]/g, "");
          let score = 0;
          if (acctLower === lower) score = 100;
          else if (acctLower.startsWith(lower) || lower.startsWith(acctLower)) score = 85;
          else if (acctLower.includes(lower) || lower.includes(acctLower)) score = 70;
          else {
            // Word overlap
            const searchWords = lower.split(/\s+/);
            const acctWords = acctLower.split(/\s+/);
            const overlap = searchWords.filter((w) => acctWords.some((a) => a.includes(w) || w.includes(a)));
            score = Math.round((overlap.length / Math.max(searchWords.length, acctWords.length)) * 60);
          }
          return { account: acct, confidence: score };
        });

        scored.sort((a, b) => b.confidence - a.confidence);
        const best = scored[0];

        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({
              match: best.confidence >= 50 ? best.account : null,
              confidence: best.confidence,
              top_matches: scored.slice(0, 3),
              all_accounts: accounts,
              message: best.confidence >= 50
                ? `Best match: "${best.account}" (${best.confidence}% confidence)`
                : `No strong match found for "${searchName}". Create a new account folder or check the name.`,
            }, null, 2),
          }],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_log_calendar_event": {
        const { account, title, date, time, attendees, description: desc, is_upcoming } = args as {
          account: string; title: string; date: string; time?: string;
          attendees: string[]; description?: string; is_upcoming?: boolean;
        };
        const accountPath = path.join(accountsDir, account);
        ensureDir(path.join(accountPath, "meetings"));

        const filename = `${date}_calendar_${sanitize(title)}.md`;
        const filePath = path.join(accountPath, "meetings", filename);
        const content = [
          `# ${title}`,
          ``,
          `**Source:** Google Calendar`,
          `**Date:** ${date}${time ? ` at ${time}` : ""}`,
          `**Attendees:** ${attendees.join(", ")}`,
          desc ? `\n**Agenda:**\n${desc}` : "",
          ``,
          is_upcoming ? `## Pre-Meeting Notes\n\n*Meeting prep will be generated automatically by JARVIS.*` : `## Meeting Notes\n\n*Add notes here or drop recording in MEETINGS/ folder.*`,
        ].filter((l) => l !== undefined).join("\n");

        fs.writeFileSync(filePath, content);

        // Queue meeting prep if upcoming
        if (is_upcoming) {
          const queueDir = path.join(dataDir, "data", "prep_queue");
          ensureDir(queueDir);
          fs.writeFileSync(
            path.join(queueDir, `${timestamp()}.json`),
            JSON.stringify({ account, title, attendees, date, submitted_at: new Date().toISOString(), status: "pending", source: "google_calendar" }, null, 2)
          );
        }

        return {
          content: [{
            type: "text" as const,
            text: `Calendar event saved: ACCOUNTS/${account}/meetings/${filename}\n${is_upcoming ? "Meeting prep queued — JARVIS will prepare a brief automatically." : "Event logged."}`,
          }],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_save_google_email": {
        const { account, subject, from_name, from_email, date, body, thread_summary } = args as {
          account: string; subject: string; from_name?: string; from_email: string;
          date: string; body: string; thread_summary?: string;
        };
        const emailsDir = path.join(accountsDir, account, "EMAILS");
        ensureDir(emailsDir);

        const filename = `${date}_${sanitize(subject)}.md`;
        const content = [
          `# ${subject}`,
          ``,
          `**Source:** Gmail`,
          `**Date:** ${date}`,
          `**From:** ${from_name ? `${from_name} <${from_email}>` : from_email}`,
          thread_summary ? `\n**Summary:** ${thread_summary}` : "",
          ``,
          `## Content`,
          ``,
          body,
        ].join("\n");

        fs.writeFileSync(path.join(emailsDir, filename), content);

        // Log to activities
        const actFile = path.join(accountsDir, account, "activities.jsonl");
        const act = { type: "email", date, subject, from: from_email, summary: thread_summary || subject, source: "gmail" };
        fs.appendFileSync(actFile, JSON.stringify(act) + "\n");

        return {
          content: [{
            type: "text" as const,
            text: `Email saved: ACCOUNTS/${account}/EMAILS/${filename}\nJARVIS will extract intelligence (sentiment, objections, buying signals, action items) in the background.`,
          }],
        };
      }

      // ---------------------------------------------------------------
      case "jarvis_save_drive_document": {
        const { account, title, doc_type, content: docContent, drive_url } = args as {
          account: string; title: string; doc_type: string; content: string; drive_url?: string;
        };
        const docsDir = path.join(accountsDir, account, "DOCUMENTS");
        ensureDir(docsDir);

        const filename = `${dateStr()}_${doc_type}_${sanitize(title)}.md`;
        const content = [
          `# ${title}`,
          ``,
          `**Source:** Google Drive`,
          `**Type:** ${doc_type.toUpperCase()}`,
          `**Saved:** ${dateStr()}`,
          drive_url ? `**Drive URL:** ${drive_url}` : "",
          ``,
          `## Content`,
          ``,
          docContent,
        ].filter(Boolean).join("\n");

        fs.writeFileSync(path.join(docsDir, filename), content);

        return {
          content: [{
            type: "text" as const,
            text: `Document saved: ACCOUNTS/${account}/DOCUMENTS/${filename}\nJARVIS will extract requirements, budget signals, and stakeholders in the background.`,
          }],
        };
      }

      // ---------------------------------------------------------------
      // Presales Intelligence Handlers
      // ---------------------------------------------------------------
      case "jarvis_get_discovery": {
        const { account } = args as { account: string };
        const discoveryDir = path.join(accountsDir, account, "DISCOVERY");
        const prep = readFileOrNull(path.join(discoveryDir, "discovery_prep.md"));
        const final = readFileOrNull(path.join(discoveryDir, "final_discovery.md"));
        if (!prep && !final) {
          return { content: [{ type: "text" as const,
            text: `No DISCOVERY folder found for "${account}". JARVIS may still be initializing it — try again in 30 seconds.` }] };
        }
        return { content: [{ type: "text" as const,
          text: `# Discovery for ${account}\n\n## Discovery Prep (Questions & Intel)\n${prep || "Not generated yet"}\n\n---\n\n## Final Discovery Notes\n${final || "No notes saved yet — use jarvis_update_discovery after your call"}` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_update_discovery": {
        const { account, notes, attendees, pain_points, budget_signal, champion, next_step } = args as {
          account: string; notes: string; attendees?: string; pain_points?: string;
          budget_signal?: string; champion?: string; next_step?: string;
        };
        const discoveryDir = path.join(accountsDir, account, "DISCOVERY");
        ensureDir(discoveryDir);
        const finalFile = path.join(discoveryDir, "final_discovery.md");
        const today = dateStr();

        const entry = [
          `\n\n---\n`,
          `## ${today} — Discovery Session`,
          attendees ? `**Attendees:** ${attendees}` : "",
          `**Notes:**\n${notes}`,
          pain_points ? `**Pain Points Confirmed:** ${pain_points}` : "",
          budget_signal ? `**Budget Signal:** ${budget_signal}` : "",
          champion ? `**Champion:** ${champion}` : "",
          next_step ? `**Next Step:** ${next_step}` : "",
        ].filter(Boolean).join("\n");

        const existing = readFileOrNull(finalFile) || `# Final Discovery Notes — ${account}\n\n*Auto-managed by JARVIS*\n`;
        fs.writeFileSync(finalFile, existing.trimEnd() + entry);

        // Log activity
        const actFile = path.join(accountsDir, account, "activities.jsonl");
        fs.appendFileSync(actFile, JSON.stringify({ type: "discovery", date: today, summary: notes.slice(0, 100) }) + "\n");

        return { content: [{ type: "text" as const,
          text: `Discovery notes saved to ACCOUNTS/${account}/DISCOVERY/final_discovery.md\nJARVIS will auto-refresh: demo strategy + value architecture in the background.` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_fill_rfi": {
        const { account } = args as { account: string };
        const rfiDir = path.join(accountsDir, account, "RFI");
        const analysis = readFileOrNull(path.join(rfiDir, "rfi_analysis.md"));
        const responses = readFileOrNull(path.join(rfiDir, "rfi_responses.md"));
        const files = fs.existsSync(rfiDir)
          ? fs.readdirSync(rfiDir).filter(f => !f.startsWith(".") && f !== "README.md")
          : [];

        if (files.length === 0) {
          return { content: [{ type: "text" as const,
            text: `No RFI files found in ACCOUNTS/${account}/RFI/. Drop the RFI document there first, then JARVIS will auto-process it.` }] };
        }
        if (!analysis && !responses) {
          return { content: [{ type: "text" as const,
            text: `RFI files found: ${files.join(", ")}\nJARVIS is still processing — check back in 2-3 minutes.\nFiles in RFI/: ${files.join(", ")}` }] };
        }
        return { content: [{ type: "text" as const,
          text: `# RFP Intelligence for ${account}\n\nFiles: ${files.join(", ")}\n\n## Requirements Analysis\n${analysis || "Processing..."}\n\n---\n\n## Draft Responses\n${responses || "Processing..."}` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_battlecard_full": {
        const { account } = args as { account: string };
        const bcDir = path.join(accountsDir, account, "BATTLECARD");
        const md = readFileOrNull(path.join(bcDir, "battlecard.md"));
        const jsonData = readFileOrNull(path.join(bcDir, "battlecard_data.json"));
        if (!md) {
          return { content: [{ type: "text" as const,
            text: `No battlecard found for "${account}" yet. JARVIS is generating it — try again in 1-2 minutes.` }] };
        }
        return { content: [{ type: "text" as const,
          text: `${md}\n\n---\n\n## Structured Data (use for PPT/Excel — Haiku/Sonnet only)\n\`\`\`json\n${jsonData || "{}"}\n\`\`\`` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_demo_strategy": {
        const { account } = args as { account: string };
        const demoDir = path.join(accountsDir, account, "DEMO_STRATEGY");
        const strategy = readFileOrNull(path.join(demoDir, "demo_strategy.md"));
        const script = readFileOrNull(path.join(demoDir, "demo_script.md"));
        if (!strategy) {
          return { content: [{ type: "text" as const,
            text: `No demo strategy found for "${account}" yet. JARVIS generates this after discovery notes are saved. Use jarvis_update_discovery first.` }] };
        }
        return { content: [{ type: "text" as const,
          text: `${strategy}\n\n---\n\n## Demo Script\n${script || "Script not yet generated — save discovery notes first."}` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_risk_report": {
        const { account } = args as { account: string };
        const riskFile = path.join(accountsDir, account, "RISK_REPORT", "risk_report.md");
        const report = readFileOrNull(riskFile);
        if (!report) {
          return { content: [{ type: "text" as const,
            text: `No risk report found for "${account}". JARVIS auto-generates this weekly — it may still be initializing.` }] };
        }
        return { content: [{ type: "text" as const, text: report }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_update_risk_report": {
        const { account, update, initials } = args as { account: string; update: string; initials?: string };
        const riskDir = path.join(accountsDir, account, "RISK_REPORT");
        ensureDir(riskDir);
        const riskFile = path.join(riskDir, "risk_report.md");
        const existing = readFileOrNull(riskFile) || `# Risk Report — ${account}\n`;
        const prefix = initials ? `${initials} ` : "";
        const entry = `\n\n---\n\n## ${prefix}${dateStr()} — Update\n\n${update}`;
        fs.writeFileSync(riskFile, existing.trimEnd() + entry);
        return { content: [{ type: "text" as const,
          text: `Risk report updated for ${account}. Entry: ${prefix}${dateStr()}` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_next_steps": {
        const { account } = args as { account: string };
        const nsDir = path.join(accountsDir, account, "NEXT_STEPS");
        const drafts = readFileOrNull(path.join(nsDir, "next_steps.md"));
        const jsonData = readFileOrNull(path.join(nsDir, "email_drafts.json"));
        const stage = jsonData ? (JSON.parse(jsonData).current_stage || "").replace(/_/g, " ") : "";
        if (!drafts) {
          return { content: [{ type: "text" as const,
            text: `No email drafts found for "${account}" yet. JARVIS generates these after each meeting — they should be ready soon.` }] };
        }
        return { content: [{ type: "text" as const,
          text: `# Next Steps for ${account}${stage ? ` (${stage})` : ""}\n\n${drafts}` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_value_architecture": {
        const { account } = args as { account: string };
        const vaDir = path.join(accountsDir, account, "VALUE_ARCHITECTURE");
        const roi = readFileOrNull(path.join(vaDir, "roi_model.md"));
        const tco = readFileOrNull(path.join(vaDir, "tco_analysis.md"));
        const valueData = readFileOrNull(path.join(vaDir, "value_data.json"));
        if (!roi) {
          return { content: [{ type: "text" as const,
            text: `No value architecture found for "${account}" yet. JARVIS needs discovery data to build the ROI model — save some discovery notes first.` }] };
        }
        return { content: [{ type: "text" as const,
          text: `${roi}\n\n---\n\n${tco || ""}\n\n---\n\n## Structured Value Data (for Excel/PPT — use Haiku or Sonnet to generate)\n\`\`\`json\n${valueData || "{}"}\n\`\`\`` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_architecture_diagram": {
        const { account } = args as { account: string };
        const archDir = path.join(accountsDir, account, "ARCHITECTURE");
        const mdFile = readFileOrNull(path.join(archDir, "architecture_diagram.md"));
        const htmlPath = path.join(archDir, "architecture_diagram.html");
        const htmlExists = fs.existsSync(htmlPath);
        if (!mdFile) {
          return { content: [{ type: "text" as const,
            text: `No architecture diagram found for "${account}" yet. JARVIS generates this from discovery + intel data — it should be ready after the first discovery call.` }] };
        }
        return { content: [{ type: "text" as const,
          text: `# Architecture Diagram — ${account}\n\n${mdFile}\n\n---\n\n**Interactive HTML:** ${htmlExists ? htmlPath : "Not yet generated"}\n\nOpen the HTML file in a browser to view the full interactive diagram with download.` }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_get_proposal": {
        const { account } = args as { account: string };
        const propDir = path.join(accountsDir, account, "PROPOSAL");
        const jsonData = readFileOrNull(path.join(propDir, "proposal_data.json"));
        const htmlPath = path.join(propDir, "proposal.html");
        const htmlExists = fs.existsSync(htmlPath);
        if (!jsonData && !htmlExists) {
          return { content: [{ type: "text" as const,
            text: `No proposal found for "${account}" yet. JARVIS auto-generates this after value architecture is ready — or ask "generate proposal for ${account}" to trigger it now.` }] };
        }
        const data = jsonData ? JSON.parse(jsonData) : {};
        return { content: [{ type: "text" as const,
          text: `# Proposal — ${account}\n\n**Status:** ${data.status || "Draft"}\n**Generated:** ${data.generated_at || "Unknown"}\n\n**Executive Summary:**\n${data.executive_summary || "(not yet filled)"}\n\n**Proposed Solution:** ${data.proposed_solution || "(not yet filled)"}\n\n**Open to edit pricing and send:** ${htmlExists ? htmlPath : "HTML not yet generated"}\n\n---\n\n## Structured Data (use claude-haiku or claude-sonnet to create PPT/Excel)\n\`\`\`json\n${jsonData || "{}"}\n\`\`\`` }] };
       }

       // ---------------------------------------------------------------
       case "jarvis_save_conversation": {
         const { account, role, content, model } = args as { account?: string; role: string; content: string; model?: string };

         if (!role || !content) {
           return { content: [{ type: "text" as const, text: "Error: role and content are required" }], isError: true };
         }

         // Infer account if not provided
         let resolvedAccount = account;
         if (!resolvedAccount) {
           try {
             const cwd = process.cwd();
             const accountsAbs = path.resolve(accountsDir);
             const cwdAbs = path.resolve(cwd);
             if (cwdAbs.startsWith(accountsAbs + path.sep) || cwdAbs === accountsAbs) {
               const rel = path.relative(accountsAbs, cwdAbs);
               const first = rel.split(path.sep)[0];
               if (first) resolvedAccount = first;
             }
           } catch {
             // ignore
           }
         }

         const timestamp = Date.now();
         const date = new Date(timestamp).toISOString().split('T')[0];
         const workspace = process.cwd();

         const entry = `<!-- JARVIS_ENTRY
date: ${date}
role: ${role}
${resolvedAccount ? `account: ${resolvedAccount}\n` : ''}---
\`\`\`json
{
  "workspace_dir": "${workspace}",
  "timestamp": ${timestamp},
  "model": ${model ? JSON.stringify(model) : null}
}
\`\`\`
JARVIS_ENTRY_END -->\n`;

         const brainPath = path.join(dataDir, "..", "JARVIS_BRAIN.md"); // JARVIS_HOME/JARVIS_BRAIN.md
         try {
           fs.appendFileSync(brainPath, entry);
           return { content: [{ type: "text" as const, text: `Conversation saved${resolvedAccount ? ` for ${resolvedAccount}` : ''}` }] };
         } catch (e: any) {
           return { content: [{ type: "text" as const, text: `Failed to save conversation: ${e.message}` }], isError: true };
         }
       }

       // ---------------------------------------------------------------
       case "jarvis_get_sow": {
        const { account } = args as { account: string };
        const sowDir = path.join(accountsDir, account, "SOW");
        const sow = readFileOrNull(path.join(sowDir, "sow.md"));
        if (!sow) {
          return { content: [{ type: "text" as const,
            text: `No SOW found for "${account}" yet. JARVIS generates this from the proposal + discovery data — ask "generate SOW for ${account}" to trigger it now.` }] };
        }
        return { content: [{ type: "text" as const,
          text: sow }] };
      }

      // ---------------------------------------------------------------
      case "jarvis_trigger_skill": {
        const { account, skill, reason } = args as { account: string; skill: string; reason?: string };

        // Write a trigger file that AccountWatcher detects within seconds
        const accountDir = path.join(accountsDir, account);
        if (!fs.existsSync(accountDir)) {
          return { content: [{ type: "text" as const,
            text: `Account "${account}" not found. Check the folder name with jarvis_list_accounts.` }], isError: true };
        }

        const triggerFile = path.join(accountDir, `.jarvis_trigger_${skill}`);
        const triggerData = JSON.stringify({
          skill,
          account,
          reason: reason || "Manually triggered via MCP",
          triggered_at: new Date().toISOString(),
          triggered_by: "claude",
        }, null, 2);

        try {
          fs.writeFileSync(triggerFile, triggerData);
          return { content: [{ type: "text" as const,
            text: `Triggered: ${skill} for ${account}. JARVIS will regenerate the files in the background — check back in 30-60 seconds.` }] };
        } catch (e: any) {
          return { content: [{ type: "text" as const,
            text: `Failed to write trigger file: ${e.message}` }], isError: true };
        }
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
