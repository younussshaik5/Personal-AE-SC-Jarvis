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

## 2. AI-Assisted Configuration (The "Magic" Way)

Instead of manual editing, you can ask your AI assistant (OpenCode or ClaudeCode) to handle the setup for you. Use the following prompts:

### Prompt for ClaudeCode / OpenCode:
> "I have just forked this JARVIS AI template. Please perform the following setup tasks:
> 1. Detect my local OS and workspace paths.
> 2. Update `mcp-opencode-observer/config/mcp-observer.json` to point to my local OpenCode/Claude conversation databases.
> 3. Verify that the `dbPath` in the config exists on my machine.
> 4. Check if I have `node` and `npm` installed, and run `npm install` in the `mcp-opencode-observer` directory if needed.
> 5. Review `jarvis/config/jarvis.yaml` and prompt me for any missing API keys."

## 3. Customizing Your Personas

JARVIS comes with two default personas: `Solution Consultant` and `Account Executive`.
- To modify them, edit the files in `jarvis/persona/`.
- To add new rules for autonomous behavior, edit `mcp-opencode-observer/config/rules.yaml`.

## 4. Troubleshooting "Broken" Links
If you see path errors (e.g., `~/.local/share/opencode/...` not found), it's because the template defaults to standard OpenCode paths. 
- **Claude Users**: Ask the AI: *"I am using ClaudeCode. Update the observer database paths to point to the Claude conversation history location on my Mac/Windows."*

## 5. Deployment
Once configured, use the fireup script:
```bash
./fireup_jarvis.sh
```

---
**Note**: This codebase uses `ACME` as a placeholder for all company data. Search and replace `ACME` with your own company name to personalize the experience.
