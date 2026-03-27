# JARVIS AI Template: Post-Fork Setup Guide

Congratulations on forking JARVIS! This template is designed to be your autonomous sales/presales assistant. Since it was originally built for OpenCode and recently adapted for Claude, follow these steps to make it work seamlessly in your environment.

## 1. Quick Start Setup

### Step 1: Install Dependencies
Navigate to the observer directory and install the required Node.js modules.
```bash
cd mcp-opencode-observer
npm install
```

### Step 2: Environment Configuration
Copy the example configurations and update them with your local paths.
- **Main Config**: `jarvis/config/jarvis.yaml`
- **Observer Config**: `mcp-opencode-observer/config/mcp-observer.json`

## 2. AI-Assisted Configuration & Repair

Because this project has a complex architecture (Python and Node.js working together), if you find any "broken" files or startup errors, you can have your AI assistant fix them automatically.

### Prompt for ClaudeCode / OpenCode:
> "I have just forked this JARVIS AI template. I am experiencing some issues [describe the issue]. 
> 1. Please first **analyze the entire project architecture** to understand how the MCP Observer and JARVIS Core interact.
> 2. Once you understand the system, perform the following setup:
>    - Update `mcp-opencode-observer/config/mcp-observer.json` with my local paths.
>    - Ensure the `dbPath` correctly points to my local OpenCode/Claude database.
>    - Run `npm install` in the observer directory.
>    - Fix any syntax or path errors you find to make the system fully functional."

## 3. Operations: What Happens When You "Fire Up"?

When you run `./fireup_jarvis.sh`, JARVIS launches multiple components that work in parallel:

1. **MCP Observer (Port 3000/3001)**: Starts a Node.js service that monitors your local OpenCode and Claude conversation databases. It sets up a WebSocket server for real-time data streaming.
2. **JARVIS Core (Python)**: The "Brain" starts up, loads your configured personas, and initializes the event bus.
3. **Internal Dashboard (Port 8080)**: Launches a local server to host the interactive HTML dashboards for each account.

## 4. Full Capabilities: What JARVIS Does for You

Once active, JARVIS acts as your autonomous double. Whatever you chat about in **ClaudeCode** or **OpenCode**, JARVIS synthesizes it in real-time.

### 🧠 Real-Time Conversation Synthesis
- **Continuous Monitoring**: JARVIS polls your chat history every 60 seconds.
- **Insight Extraction**: Automatically identifies customer interests, pain points, and technical requirements mentioned in your conversations.
- **Competitor Detection**: If a competitor (like Salesforce or Zendesk) is mentioned, JARVIS logs it and prepares battlecard updates.

### 📝 Autonomous Document Generation
For every account folder you create in `ACCOUNTS/`, JARVIS will automatically generate and keep updated:
- **Technical Risk Assessment**: Evaluates the complexity and potential blockers in a deal.
- **Deep Discovery (Internal/External)**: Tracks what you know and what questions you still need to ask.
- **MEDDICC/MEDDPICC Reports**: Scores the opportunity based on your conversations.
- **ROI & TCO Models**: Drafts financial justifications based on mentioned value drivers.
- **Demo Strategy**: Prescribes a specific demo flow and talk track based on the customer's revealed interests.

### 🎭 Multi-Persona Intelligence
- **Persona Switching**: Detects if your conversation is more "Account Executive" (deal-focused) or "Solution Consultant" (technical) and adjusts its output tone and focus.
- **Rules Engine**: You can custom-program autonomous actions in `mcp-opencode-observer/config/rules.yaml` (e.g., "if I mention a demo, automatically update the Demo Strategy doc").

### 📊 Interactive Account Dashboards
- Every account gets a `DASHBOARD.html` that aggregates all the above.
- One-click exports to **PDF**, **Word**, or **Excel** for immediate handoffs to your team.

---

## 5. Customizing Your Personas
- To modify persona definitions, edit the files in `jarvis/persona/`.
- To add new rules for autonomous behavior, edit `mcp-opencode-observer/config/rules.yaml`.

## 6. Troubleshooting "Broken" Links
If you see path errors (e.g., `~/.local/share/opencode/...` not found), it's because the template defaults to standard OpenCode paths. 
- **Claude Users**: Ask the AI: *"I am using ClaudeCode. Update the observer database paths to point to the Claude conversation history location on my Mac/Windows."*

---
**Note**: This codebase uses `ACME` as a placeholder for all company data. Search and replace `ACME` with your own company name to personalize the experience.
