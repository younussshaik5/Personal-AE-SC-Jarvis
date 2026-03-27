# JARVIS - Autonomous AI Employee

**Version:** 2.0.0  
**Workspace:** `/path/to/your/workspace`  
**Solution Engineer:** YOUR_NAME (YourCompany)  
**Last Updated:** 2026-03-25

---

## Executive Summary

JARVIS is an autonomous AI employee system that continuously learns from OpenCode conversations, monitors file systems, and auto-generates sales engineering artifacts per account/opportunity. It operates in real-time (< 1 min latency) across the entire workspace, regardless of which subfolder you're working in.

### Core Capabilities

1. **Workspace-Wide Awareness** - Monitors all subfolders through OpenCode DB and file system watcher
2. **Real-Time Intelligence** - LLM-enhanced synthesis with fallback rule-based extraction
3. **Auto-Documentation** - Generates and maintains per-account:
   - `TECHNICAL_RISK_ASSESSMENT.md`
   - `discovery/internal_discovery.md`
   - `discovery/final_discovery.md`
   - `discovery/Q2A.md`
   - `MEMORY/accounts/<account>/conversations.json`
4. **Cross-Linking** - All documents interlink and reference each other; updates propagate automatically
5. **General Intelligence** - Uses LLM to synthesize insights from deals, notes, conversations, and discovery docs

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│ OpenCode DB (Workspace Sessions)                    │
└──────────────────────┬──────────────────────────────┘
                       │ polls every 60s (workspace-filtered)
                       ↓
┌─────────────────────────────────────────────────────┐
│ MCP Observer (Node.js)                              │
│ • getMessageFromTime(workspace_root)               │
│ • Insight extraction                               │
│ • Auto-approvals & pattern learning               │
└──────────────────────┬──────────────────────────────┘
                       │ events
                       ↓
┌─────────────────────────────────────────────────────┐
│ JARVIS Core Python (Orchestrator)                  │
│ • Event Bus                                        │
│ • Skill Registry                                   │
│ • Component lifecycle                              │
└───────┬─────────────────┬────────────┬─────────────┘
        │                 │            │
        ↓                 ↓            ↓
┌───────────────┐ ┌─────────────┐ ┌─────────────────┐
│ Risk Assess   │ │ Discovery   │ │ Other Skills    │
│ Skill         │ │ Skill       │ │ (Competitive    │
│ • LLM synth   │ │ • Internal  │ │  Intelligence,   │
│ • Rule fallback│ │ • Final     │ │  Conversation   │
│ • Interlinks  │ │ • Q2A       │ │  Summarizer)    │
└───────────────┘ └─────────────┘ └─────────────────┘
        │                 │
        └─────────────────┘
                  │
                  ↓
        ACCOUNTS/<team>/<account>/
        ├── notes.json
        ├── summary.md
        ├── activities.jsonl
        ├── deals/<deal>.json
        ├── TECHNICAL_RISK_ASSESSMENT.md (auto)
        └── discovery/ (auto)
            ├── internal_discovery.md
            ├── final_discovery.md
            └── Q2A.md
```

---

## Quick Start

### Starting JARVIS
```bash
./fireup_jarvis.sh
```

Components:
- MCP Observer → `http://localhost:3000` (internal)
- UI Dashboard → `http://localhost:8080`
- Logs → `logs/`

### Adding a New Account

1. Create folder under `ACCOUNTS/<team>/<Account Name>/`
2. Add smartness files:
   - `notes.json` (facts, preferences, knowledge_gaps)
   - `summary.md` (optional, auto-generated)
   - `deals/<deal>.json` (deal details)
   - `activities.jsonl` (action log)
3. JARVIS auto-initializes and creates:
   - `index.json`
   - `TECHNICAL_RISK_ASSESSMENT.md`
   - `discovery/` folder with all docs

### Updating Data

Just modify any file in the account folder. JARVIS detects changes and updates all linked documents within 60 seconds.

---

## Generated Document Structure

### TECHNICAL_RISK_ASSESSMENT.md

**Owner:** SE YOUR_NAME  
**Frequency:** Real-time updates  
**Includes:**
- Top 3 Technical Use Cases
- SE Activities (Discovery, Demo, POV counts)
- Stakeholders identified
- Next steps / Outstanding items
- Technical gaps & risks
- Risk level (Low/Medium/High)
- Links to discovery docs

### discovery/internal_discovery.md

**Prepared by:** SE YOUR_NAME  
**Includes:**
- Deal overview (product, ARR, stage, competitors)
- Current systems & environment
- Key requirements
- Knowledge gaps & risks
- Technical discovery status table
- Next steps & open questions
- Links to risk assessment, final discovery, Q2A

### discovery/final_discovery.md

**SE:** SE YOUR_NAME  
**Includes:**
- Executive summary
- Solution architecture
- Risks & mitigations
- Implementation considerations
- Handoff notes
- Links to other docs

### discovery/Q2A.md

**Owner:** SE YOUR_NAME  
**Includes:**
- Priority 1, 2, 3 questions
- Sources & dependencies
- Answer status table
- Discovery call agenda template

---

## LLM Integration

To enable full LLM synthesis:

1. Set API key in `jarvis/config/jarvis.yaml`:
   ```yaml
   opencode_ai:
     enabled: false  # Currently using OpenCode AI config
   llm:
     provider: "openai"
     api_key: "your-key"
     base_url: "https://api.openai.com/v1"
     model: "gpt-4"
   ```

2. Restart JARVIS: `./fireup_jarvis.sh`

When enabled, all documents are synthesized with general intelligence, analyzing:
- Deal JSON files
- Notes.json (facts, gaps)
- Conversation history
- Existing discovery artifacts

Graceful fallback to rule-based if LLM fails.

---

## Event Bus Triggers

| Event | Triggers | Documents Updated |
|-------|----------|-------------------|
| `account.initialized` | New account folder | All |
| `file.modified` (ACCOUNTS/) | Any smartness file change | All |
| `conversation.stored` | New conversation logged | Risk Assessment |
| `discovery.updated` | Discovery docs changed | Risk Assessment |
| `notes.updated` | notes.json modified | All |
| `deal.updated` | Deal JSON modified | All |
| `competitor.detected` | Competitor mention | Risk Assessment |

---

## Configuration

Main config: `jarvis/config/jarvis.yaml`

Key settings:
- `workspace_root`: `/path/to/your/workspace`
- `polling_interval_seconds`: 60
- `approval_required`: true
- `solution_engineer.name`: `YOUR_NAME`
- `llm.provider`: `openai` (or nvidia, anthropic)
- `opencode_ai.enabled`: false (use external LLM)

---

## Monitoring & Logs

**Skill logs (JSONL):**
- `logs/skill.risk_assessment.jsonl`
- `logs/skill.discovery.jsonl`
- `logs/skill.conversation_summarizer.jsonl`
- `logs/skill.competitive_intelligence.jsonl`

**Component logs:**
- `logs/orchestrator_manual.log`
- `logs/jarvis.log`
- `logs/file_system.jsonl`

**Status commands:**
```bash
ps aux | grep -E "jarvis|mcp-opencode"
./fireup_jarvis.sh   # re-checks and restarts if needed
```

---

## Troubleshooting

### Orchestrator crashes on startup
Check `logs/orchestrator_manual.log` for missing method errors. Ensure all skills are properly registered in `orchestrator.py`.

### LLM synthesis failing
Verify API key and connectivity. System falls back to rule-based automatically.

### Files not updating
- Check if folder is under `ACCOUNTS/`
- Ensure at least one smartness file exists (`notes.json`, `summary.md`, `deals/`)
- Wait up to 60 seconds for next poll cycle
- Check skill logs for errors

### MCP observer not filtering workspace
Confirm `workspace_root` in `config/mcp-observer.json` and `autonomy.ts` matches your workspace path.

---

## Extending JARVIS

### Adding New Skills

1. Create file in `jarvis/skills/your_skill.py`
2. Define class with `start()`, `stop()`, event handlers
3. Register in `orchestrator.py`:
   ```python
   from jarvis.skills.your_skill import YourSkill
   COMPONENT_CLASSES['your_skill'] = YourSkill
   ```
4. Add to `init_order` before `account_auto_init`
5. Rebuild (if Node changes) and restart

### Custom Document Templates

Edit the respective skill file:
- Risk Assessment → `_generate_risk_assessment()` in `technical_risk_assessment.py`
- Discovery docs → `_generate_internal_discovery()`, `_generate_final_discovery()`, `_generate_q2a()` in `discovery_management.py`

---

## Current Accounts

| Account Name | Team | Deals | Gaps | Last Updated |
|--------------|------|-------|------|--------------|
| Ivalua::Freshdesk (35) Pro::New Business | PRESALES SOLUTION CONSULTANT | 1 | 7 | 2026-03-25 12:26 |
| AKSHAYAKALPA ORGANIC | AE | - | - | 2026-03-25 12:26 |
| TEST ACCOUNT AE | AE | - | - | 2026-03-25 12:26 |
| deals | AE | - | - | 2026-03-25 12:26 |

*All accounts auto-updated every 60 seconds.*

---

## License & Ownership

**Created for:** YourCompany SE Team  
**Primary User:** YOUR_NAME (Solution Engineer)  
**All generated documents:** Property of the workspace owner  
**System:** Open-source under MIT (modify as needed)

---

*This master sheet is maintained by JARVIS and auto-updates when system configuration changes.*