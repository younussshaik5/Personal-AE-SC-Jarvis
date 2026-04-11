# Zero Manual Creation: Complete Guide

## What You Now Have

JARVIS has been upgraded with **zero-manual-creation** features. You no longer need to manually:
- Create account folders
- Create template files
- Manage account hierarchies
- Remember CLAUDE.md settings

Everything is **auto-created, auto-detected, auto-evolved**.

---

## Five New Superpowers

### 1. **Account Scaffolding** (`scaffolder.py`)
Auto-creates account folders with pre-filled templates from natural language.

**What it creates:**
```
ACCOUNTS/Tata/
├── company_research.md      (auto-created with company info)
├── discovery.md             (template with company name)
├── deal_stage.json          (template with Tata pre-filled)
└── CLAUDE.md                (account-specific settings)
```

**How it works:**
```
You say:  "I'm working on Tata, 50M revenue, enterprise SaaS"
Claude:  "I detected 'Tata' is a new account. Should I create it?"
You:     "Yes"
JARVIS:  Auto-creates all files with Tata info pre-filled ✓
```

### 2. **Account Hierarchy** (`account_hierarchy.py`)
Supports parent/child account relationships (Tata → TataTele, TataSky).

**Folder structure:**
```
ACCOUNTS/
├── Tata/
│   ├── company_research.md     (parent - shared)
│   ├── discovery.md            (parent's own)
│   ├── deal_stage.json         (parent's own)
│   ├── TataTele/
│   │   ├── discovery.md        (child-specific)
│   │   ├── deal_stage.json     (child-specific)
│   │   └── (inherits parent's company_research.md)
│   └── TataSky/
│       ├── discovery.md        (child-specific)
│       ├── deal_stage.json     (child-specific)
│       └── (inherits parent's company_research.md)
```

**Key Features:**
- ✅ Recursive account discovery (find accounts at any depth)
- ✅ Parent context inheritance (children share parent's company data)
- ✅ Fuzzy matching (say "TataTele", JARVIS finds it)
- ✅ Smart caching (fast lookups)

### 3. **Context Detection** (`context_detector.py`)
Auto-detects account when you open a folder in cowork.

**How it works:**
```
Step 1: Open cowork in ACCOUNTS/Tata/TataTele/
Step 2: JARVIS reads deal_stage.json
Step 3: Claude automatically knows you're working on TataTele
Step 4: All skill calls automatically use TataTele context
```

**No need to say the account name anymore!**

### 4. **CLAUDE.md Parsing** (`claude_md_loader.py`)
Dynamically loads account-specific settings from CLAUDE.md files.

**Hierarchical loading (most specific wins):**
```
1. ACCOUNTS/Tata/TataTele/CLAUDE.md          (most specific)
2. ACCOUNTS/Tata/CLAUDE.md                   (parent)
3. ~/.claude/CLAUDE.md                       (global)
```

**What it reads:**
- Cascade rules (when discovery.updated → refresh these skills)
- Model preferences (which Claude model for each task)
- Skill preferences (how to configure each skill)
- Routing rules (which skill to use when)

### 5. **CLAUDE.md Evolution** (`claude_md_evolve.py`)
Auto-learns from your interactions and improves over time.

**How it learns:**
```
Day 1:
  You: "Create proposal"
  JARVIS: Records interaction (skill=proposal, model=text, quality=4.8)

Day 5:
  JARVIS: "Detected: You've used proposal 5x with model=text, quality=4.9"
  JARVIS: "Suggestion: Always use Sonnet for proposals?"
  You: "Yes"
  CLAUDE.md: Auto-updates with this preference

Day 10:
  You: "Create proposal"
  JARVIS: Automatically uses Sonnet (learned preference) ✓
```

**Tracked metrics:**
- Skill usage frequency
- Best models for each task
- Quality scores per interaction
- User feedback patterns
- ROI patterns
- Pain point patterns

---

## End-to-End Workflow: Create Tata → Create TataTele → Work in Cowork

### Step 1: Create Tata (Parent Account)

**You say:**
```
Claude, I need to work on Tata Corporation.
They're a $50M enterprise SaaS company.
Looking to automate their onboarding process.
```

**JARVIS does:**
1. Detects "Tata" as new account
2. Extracts: name=Tata, revenue=$50M, industry=SaaS
3. Prompts: "Should I create the account structure?"
4. Auto-creates:
   ```
   ACCOUNTS/Tata/
   ├── company_research.md (pre-filled with Tata, $50M, SaaS)
   ├── discovery.md (template with company name)
   ├── deal_stage.json (template with Tata pre-filled)
   └── CLAUDE.md (account-specific)
   ```
5. Confirms: "Account created! Ready to work on Tata."

### Step 2: Create TataTele (Sub-Account)

**You say:**
```
Actually, we have two separate divisions:
- TataTele (telecom division)
- TataSky (satellite division)
```

**JARVIS does:**
1. Offers: "Create TataTele and TataSky as sub-accounts?"
2. Auto-creates both under Tata:
   ```
   ACCOUNTS/Tata/
   ├── TataTele/
   │   ├── discovery.md
   │   ├── deal_stage.json
   │   └── (inherits company_research.md from Tata)
   └── TataSky/
       ├── discovery.md
       ├── deal_stage.json
       └── (inherits company_research.md from Tata)
   ```
3. Confirms: "Created TataTele and TataSky"

### Step 3: Work in Cowork

**You:**
1. Open cowork in `ACCOUNTS/Tata/TataTele/`
2. Say: "Create a proposal"

**JARVIS does:**
1. Detects: You're in TataTele folder
2. Reads: `ACCOUNTS/Tata/TataTele/deal_stage.json` + `discovery.md`
3. Inherits: Company research from `ACCOUNTS/Tata/company_research.md`
4. Loads: `ACCOUNTS/Tata/TataTele/CLAUDE.md` (account-specific settings)
5. Generates: Proposal specifically for TataTele
6. Records: Interaction (proposal generated, quality tracked)
7. Returns: Professional proposal

**No need to mention account name!**

---

## How Files Integrate

```
┌─────────────────────────────────────────────────────────┐
│                     User in Cowork                       │
│              (open folder, say commands)                 │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    mcp_server.py   context_detector.py  (detects folder as account)
         │
         ├─→ account_hierarchy.py
         │   (finds account, parent, sub-accounts)
         │
         ├─→ claude_md_loader.py
         │   (loads account CLAUDE.md hierarchically)
         │
         ├─→ scaffolder.py (if new account)
         │   (auto-creates folders, templates)
         │
         └─→ [24 skills] + preferences.py + dashboard.py
             (generate content, track interactions)
         │
         └─→ claude_md_evolve.py
             (track interactions, suggest improvements,
              auto-update CLAUDE.md)
```

---

## Key Concepts

### Account Naming
- Account name = folder name in ACCOUNTS/
- JARVIS fuzzy matches: "Tata Tele" → finds "TataTele"
- Case-insensitive matching

### Context Priority
1. **Explicit account** (you mention it) - highest priority
2. **Current folder** (detected from cwd) - medium priority
3. **Environment variable** `JARVIS_ACCOUNT` - lowest priority

### File Inheritance
- **Inherited:** `company_research.md` (parent → child)
- **Own:** `discovery.md`, `deal_stage.json` (each has own)
- **Inherited:** `CLAUDE.md` (child inherits parent's if not own)

### CLAUDE.md Sections
- **Static** (you control): Preferences, routing rules
- **Dynamic** (auto-updated): Performance metrics, learned preferences, suggestions
- **Approval gate**: Suggestions need your approval before applying

---

## Usage Examples

### Example 1: New Account from Scratch
```
You: "Working on Google. Need to create a account for them."
Claude: "Should I scaffold a Google account?"
You: "Yes"
→ ACCOUNTS/Google/ created with all templates
```

### Example 2: Sub-Opportunities
```
You: "Google has 3 divisions: Cloud, Workspace, and Search"
Claude: "Create sub-accounts?"
You: "Yes"
→ ACCOUNTS/Google/Cloud/
→ ACCOUNTS/Google/Workspace/
→ ACCOUNTS/Google/Search/
```

### Example 3: Work in Cowork
```
$ cd ~/Documents/claude\ space/ACCOUNTS/Google/Cloud
$ claude code  (open cowork)

You: "Create demo strategy"
Claude: (auto-detects Cloud context)
→ Generates demo for Google Cloud
→ Records interaction
→ CLAUDE.md learns your preferences
```

### Example 4: Auto-Learning
```
Day 1-5: You always ask for ROI after proposal
Day 6: Claude suggests "Should I auto-include ROI?"
You: "Yes"
Day 7+: Claude auto-includes ROI in all proposals
```

---

## Files Created

| File | Purpose | LOC |
|------|---------|-----|
| `account_hierarchy.py` | Parent/child relationships, recursive discovery, fuzzy matching | 250 |
| `context_detector.py` | Detect account from current folder | 150 |
| `claude_md_loader.py` | Parse CLAUDE.md hierarchically | 300 |
| `claude_md_evolve.py` | Track interactions, auto-learn, suggest improvements | 300 |
| `scaffolder.py` | Auto-create accounts with templates | 300 |

**Total new infrastructure:** ~1300 LOC

---

## What's NOT Manual Anymore

❌ **You DON'T do:**
- Create folders manually
- Create deal_stage.json manually
- Create company_research.md manually
- Create discovery.md manually
- Mention account names repeatedly
- Update CLAUDE.md settings manually
- Decide which model to use
- Remember cascade rules

✅ **JARVIS DOES:**
- Create folders from natural language
- Create all template files
- Pre-fill with company info
- Detect account from folder
- Load account-specific settings
- Learn your preferences
- Suggest improvements
- Auto-update configurations

---

## Next Steps

1. **Test hierarchy:** Create Tata → Create TataTele → Use in cowork
2. **Test auto-scaffolding:** Create new account from natural language
3. **Test learning:** Use proposals 5x, watch CLAUDE.md evolve
4. **Test sub-accounts:** Create sub-divisions under parent account

---

## Success Indicators

✅ Account created without touching filesystem
✅ Sub-accounts work with parent inheritance
✅ Opening folder auto-loads account context
✅ CLAUDE.md learns and suggests improvements
✅ Zero manual file creation
✅ Fuzzy matching finds accounts anywhere in tree

---

**That's what you have now. JARVIS is fully autonomous for account management.** 🚀
