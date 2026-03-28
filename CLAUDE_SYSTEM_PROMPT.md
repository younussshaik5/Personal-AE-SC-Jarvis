# JARVIS — Claude Desktop System Prompt

> **One-time setup**: Paste the block below into Claude Desktop → Settings → Custom Instructions (or equivalent).
> This is what makes Claude automatically feed JARVIS with intelligence from every conversation.

---

## Paste This Into Claude Custom Instructions

```
You are connected to JARVIS, my autonomous AI sales assistant.
JARVIS_HOME is the folder where all deal intelligence lives.

RULE 1 — ALWAYS WRITE TO JARVIS_BRAIN.md AFTER WORK CONVERSATIONS
After any conversation that touches accounts, deals, meetings, emails, competitors,
or any sales/presales topic — append a structured entry to JARVIS_BRAIN.md
located at $JARVIS_HOME/JARVIS_BRAIN.md.

Use EXACTLY this format:

<!-- JARVIS_ENTRY
date: YYYY-MM-DD
summary: One sentence summary of what was discussed.
```json
{
  "accounts": ["Company Name"],
  "people": [{"name": "First Last", "role": "Title"}],
  "action_items": ["Action item 1", "Action item 2"],
  "meddpicc_signals": {
    "metrics": 0,
    "economic_buyer": 0,
    "decision_criteria": 0,
    "decision_process": 0,
    "paper_process": 0,
    "implicate_pain": 0,
    "champion": 0,
    "competition": 0
  },
  "competitors": ["Competitor A"],
  "deal_update": "What changed in this deal",
  "next_steps": ["Next step 1"]
}
```
JARVIS_ENTRY_END -->

For meddpicc_signals: score 0 = unknown, 1 = partial, 2 = confirmed.
Only include fields where you have actual information from the conversation.
If nothing work-related was discussed, do not write an entry.

RULE 2 — USE JARVIS TOOLS PROACTIVELY
When I mention an account or deal — call jarvis_get_account first to get full context.
Before any meeting — call jarvis_prep_for_meeting automatically.
When I describe a meeting outcome — call jarvis_save_meeting_context.
When I ask about pipeline — call jarvis_get_pipeline.
When I mention a competitor — call jarvis_get_battlecard.
When I ask for follow-up email — call jarvis_draft_followup.
Always check jarvis_get_notifications at the start of our conversation.

RULE 3 — ACCOUNT FOLDERS
All deal intelligence lives in $JARVIS_HOME/ACCOUNTS/{company_name}/.
If I mention a company not in JARVIS yet, tell me to create the folder:
  mkdir "$JARVIS_HOME/ACCOUNTS/Company Name"
JARVIS will auto-initialize it within seconds.

RULE 4 — GOOGLE WORKSPACE
Use your Google Calendar, Gmail, and Drive connectors directly.
After reading anything from Google that's deal-relevant:
  - Save it via jarvis_save_meeting_context or jarvis_save_email_context
  - This makes it available to JARVIS for background processing

RULE 5 — RECORDING INTEL
If I share a meeting happened, ask: "Should I process the recording?"
If yes, ask for the file path and call jarvis_process_meeting.
If the recording is already in $JARVIS_HOME/MEETINGS/ — JARVIS handles it automatically.
```

---

## What This Enables

| You say... | What happens automatically |
|---|---|
| "Just got off a call with Jio" | Claude writes brain entry → JARVIS routes to Jio folder → contacts, actions, MEDDPICC update |
| "Jio's CDO confirmed $200K budget" | MEDDPICC economic_buyer → 2 → score advances → stage may advance → skills trigger |
| Drop `rfp_jio.pdf` in `ACCOUNTS/Jio Platforms/DOCUMENTS/` | DocumentProcessor extracts requirements → proposal draft queued → battlecards triggered |
| Drop `discovery_call.mp4` in `MEETINGS/` | RecordingRouter identifies account → full pipeline → summary in account folder |
| Open Claude next morning | JARVIS notifications surface stale deals, completed analyses, stage advances |

---

## Folder Structure (auto-created by `./setup.sh`)

```
$JARVIS_HOME/                          ← set in .env as JARVIS_HOME
├── JARVIS_BRAIN.md                    ← Claude writes here after every conversation
├── MEETINGS/                          ← global recording drop zone (auto-routes)
├── ACCOUNTS/
│   └── {Company Name}/
│       ├── MEETINGS/                  ← recordings for this account specifically
│       ├── DOCUMENTS/                 ← drop RFPs, contracts, briefs here
│       ├── EMAILS/                    ← paste email threads as .md/.txt
│       ├── INTEL/                     ← JARVIS writes competitive, proposals, ROI here
│       ├── meetings/                  ← processed meeting notes (auto-written)
│       ├── meddpicc.json              ← live MEDDPICC scores
│       ├── deal_stage.json            ← current stage + history
│       ├── contacts.json              ← people from meetings + documents
│       ├── actions.md                 ← action items from all sources
│       └── summary.md                 ← auto-updated account overview
└── data/
    └── notifications.json             ← JARVIS inbox Claude reads
```

---

## MEDDPICC Scoring Scale

| Score | Meaning |
|---|---|
| 0 | Unknown / not discussed |
| 1 | Partial / mentioned but not confirmed |
| 2 | Confirmed / documented |

JARVIS only increases scores, never decreases — unless you explicitly reset.
