# JARVIS Lifecycle Management — When to Expect JARVIS to Work

> **For sales people: Understanding when JARVIS starts, stops, and persists.**

---

## Overview

JARVIS follows Claude Desktop's lifecycle:
- **When Claude Desktop opens** → JARVIS starts automatically (2-3 second startup)
- **When Claude Desktop closes** → JARVIS stops cleanly (graceful shutdown)
- **When Claude reopens** → JARVIS starts fresh and ready (all your accounts still there)

---

## What Persists Across Close/Reopen Cycles

✅ **Your account data** — All ACCOUNTS/ folders are saved on disk  
✅ **Deal files** — deal_stage.json, discovery.md, company_research.md stay put  
✅ **Generated outputs** — MEDDPICC scores, risk reports, battlecards persist  
✅ **Configuration** — .env file with API keys remains  
✅ **JARVIS home** — .jarvis/ folder is permanent  

**Result:** When you close Claude Desktop and reopen it 1 hour later, all your accounts and deal data are exactly as you left them.

---

## Startup Sequence (Claude Desktop Opens)

1. **Claude Desktop launches** (you click the app or it auto-opens)
2. **Claude Desktop starts MCP servers** (including JARVIS)
3. **JARVIS launcher checks environment** (validates .env, JARVIS_HOME, ACCOUNTS folder)
4. **If check passes:**
   - ✅ JARVIS initializes all 24 skills
   - ✅ File watchers activate (watching for file changes)
   - ✅ Account context detection activates
   - ✅ CRM Dashboard starts (if applicable)
   - **Status:** JARVIS is ready (you can start using skills immediately)

5. **If check fails:**
   - ❌ Error message shown: "JARVIS_HOME not set. Run: python install.py"
   - **Status:** JARVIS won't work until setup is fixed

---

## Expected Startup Time

| Component | Time |
|-----------|------|
| Claude Desktop opening | 5-10 sec |
| JARVIS launching (total) | 2-3 sec |
| **First skill call** | 20-40 sec (first call is slower due to LLM initialization) |
| **Subsequent skill calls** | 10-20 sec |

---

## Shutdown Sequence (Claude Desktop Closes)

1. **You quit Claude Desktop** (Cmd+Q on Mac, close button on Windows)
2. **Claude Desktop signals shutdown** to all MCP servers
3. **JARVIS receives shutdown signal**
4. **JARVIS gracefully shuts down:**
   - Stops all background tasks
   - Stops file watchers
   - Closes activity logs
   - Waits up to 10 seconds for cleanup
5. **JARVIS process terminates cleanly**

**Your data:** All files are already saved to disk (JARVIS doesn't keep anything in memory).

---

## What If I Close Claude Abruptly?

**Scenario:** You force-close Claude Desktop or your computer crashes

**What happens:**
- All your account files are safe (they're on disk)
- JARVIS process is killed immediately (but has nothing important in RAM)
- When you reopen Claude Desktop, JARVIS will restart fresh
- All your deals and notes are still there

**Result:** No data loss. JARVIS is designed to handle abrupt shutdowns.

---

## What If I Accidentally Delete JARVIS Files?

**Scenario:** You delete the `.jarvis/` folder or JARVIS project folder accidentally

**If you delete `.jarvis/ACCOUNTS/`:**
- ❌ All your account data is gone (permanently)
- **Recovery:** Run `python install.py` again to create fresh .jarvis folder
- **Your deals:** Permanently lost (unless you have backups)

**If you delete the JARVIS project folder itself:**
- ❌ Entire JARVIS installation is gone
- **Recovery:** Download JARVIS from GitHub again, then run `python install.py`

**Prevention:**
- Don't delete JARVIS project folder once setup
- Don't move the .jarvis/ folder manually
- Keep your JARVIS project in a safe location

---

## Project-Scoped Behavior

**Important:** This JARVIS instance is **project-specific**.

### Scenario: Multiple JARVIS Projects

If you have:
- `~/Projects/CompanyA/` → JARVIS (with CompanyA deals)
- `~/Projects/CompanyB/` → JARVIS (with CompanyB deals)

**Each has its own:**
- Virtual environment (venv/)
- Configuration (.env)
- Account folder (.jarvis/ACCOUNTS/)

**When you open:**
- CompanyA project in Claude Desktop → Uses CompanyA's JARVIS
- CompanyB project in Claude Desktop → Uses CompanyB's JARVIS

**Result:** Complete isolation. No account mixing.

---

## Reopening After Close

### Scenario 1: Close Claude, Reopen (Normal)

1. Close Claude Desktop (Cmd+Q or window close)
2. All processes stop, all files saved
3. Reopen Claude Desktop
4. JARVIS starts automatically (2-3 seconds)
5. All your accounts are there, ready to use

**Expected:** Seamless. No issues.

### Scenario 2: Switch Projects

1. Close Claude Desktop
2. Open DIFFERENT JARVIS project folder in Claude Desktop
3. JARVIS starts for NEW project (using that project's .jarvis/ folder)

**Expected:** Completely separate JARVIS instances.

### Scenario 3: Computer Restart

1. Restart computer (shutdown, sleep, etc.)
2. Open Claude Desktop
3. JARVIS starts automatically
4. All accounts restored, ready to use

**Expected:** Works exactly the same as normal close/reopen.

---

## Troubleshooting Persistence Issues

### Issue: "JARVIS won't start after reopening Claude Desktop"

**Possible causes & fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| Error: "JARVIS_HOME not set" | .env file missing/corrupted | Run `python install.py` |
| Error: "ACCOUNTS folder not found" | .jarvis/ was deleted | Run `python install.py` |
| JARVIS takes 30+ seconds to start | Normal (first start of day) | Be patient, or check console logs |
| JARVIS tools don't appear in Claude | MCP not registered | Restart Claude Desktop completely |

### Issue: "My accounts disappeared after closing Claude"

**Likely cause:** You deleted .jarvis/ACCOUNTS/ folder by accident

**Check:** 
- Does the folder `{PROJECT}/.jarvis/ACCOUNTS/` still exist?
- Are your account folders still in it? (e.g., `.jarvis/ACCOUNTS/AcmeCorp/`)

**If accounts are gone:**
- They're permanently deleted (unless you have backups)
- Run `python install.py` to create fresh .jarvis folder
- Recreate your accounts from scratch or from notes

### Issue: "JARVIS works after reopening, but account files look different"

**Likely cause:** You may be in a different JARVIS project

**Check:**
- Which project folder is open in Claude?
- Is it the same project you were using before?
- Check `{PROJECT}/.jarvis/ACCOUNTS/` path (is it correct?)

---

## Monitoring JARVIS Health

### How to know JARVIS is running:

1. **Claude Desktop is open** → JARVIS is running
2. **You can call JARVIS skills** → JARVIS is healthy
3. **Skills complete normally** → No issues

### How to know JARVIS has an issue:

1. **Skill returns error** → Check error message
2. **JARVIS won't start** → Check environment (run `python install.py`)
3. **Slow skill execution** → Check API key (maybe hitting rate limits)

---

## Best Practices

✅ **Keep your JARVIS project folder stable** — Don't move or rename it frequently  
✅ **Keep .env file updated** — Add more API keys if you hit rate limits  
✅ **Backup your ACCOUNTS folder** — Periodic backups to prevent data loss  
✅ **Restart Claude Desktop weekly** — Refreshes JARVIS and clears memory  
✅ **Check .jarvis/ACCOUNTS/ exists** — After every major change  

---

## What If I Want to Move JARVIS to a Different Location?

**Scenario:** You move your JARVIS project to a different folder

**Steps:**
1. **Move entire project folder** (JARVIS stays in same place with .jarvis/ intact)
2. **Re-run setup:** `python install.py` (to update Claude Desktop config)
3. **Restart Claude Desktop** (to reconnect to new path)
4. **All accounts should still be there** ✓

---

## Support

If JARVIS won't start after a close/reopen cycle:

1. **Run install.py again** to verify environment
2. **Check that Claude Desktop is fully closed** (check system tray, processes)
3. **Restart Claude Desktop** completely (force close if needed)
4. **Check .jarvis/ folder exists** with ACCOUNTS subfolder
5. **Read error messages** from JARVIS — they usually tell you what's wrong

---

## Key Takeaway

✅ **JARVIS starts & stops with Claude Desktop** — Automatic, no manual steps  
✅ **Your accounts persist** — All deal data saved to disk  
✅ **Each project is isolated** — Multiple JARVIS projects don't interfere  
✅ **Graceful shutdown** — No data loss even if Claude closes abruptly  

**You should never need to think about JARVIS lifecycle management — it just works.**
