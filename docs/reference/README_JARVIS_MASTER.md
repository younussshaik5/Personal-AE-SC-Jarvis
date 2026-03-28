# JARVIS - Autonomous AI Employee System

> [!WARNING]
> **This document is from an early design phase and contains outdated information** (fictional CLI commands like `jarvis execute`, `jarvis workspace add`, trust-based permissions, fireup system, etc.). The system has evolved significantly. For the current, accurate documentation, see:
> - [README.md](../../README.md) – Current system overview
> - [START_HERE.md](../getting-started/START_HERE.md) – Getting started guide
> - [Skills Overview](../skills/OVERVIEW.md) – All 15+ implemented skills
>
> This file is preserved for historical/architectural reference only.

## Quick Answer: What Is This?

**JARVIS is an AI that works for you autonomously:**
- Watches your code files automatically
- Learns your coding patterns
- Understands which client (persona) you're working for
- Executes tasks like "add authentication" with 85%+ autonomy
- Self-improves over time
- Manages client deals and deadlines
- Has full safety: backups, rollback, approvals

**The magic is in FIREUP** - it auto-detects your project type and loads the right skills, then updates itself when you add new folders/files.

---

## The 5-Minute Understanding

### Core Concept
```
Normal Development:      JARVIS:
You write code     →     JARVIS writes code
You decide what     →    JARVIS decides HOW
You manage clients  →    JARVIS tracks deals automatically
You learn new tech  →    JARVIS detects & integrates it
You get faster     →    JARVIS self-evolves to be faster
```

### How It Works (Simple)
1. **Startup**: `fireup/` scans your project, loads Django/React/etc skills automatically
2. **Watch**: FileObserver sees every change, Learner extracts patterns
3. **Think**: MCP plans multi-step tasks using learned patterns
4. **Act**: Updaters modify files safely (backup + rollback)
5. **Learn**: Meta-learner watches performance and optimizes system

### Who It's For
- Solo devs: Get a 24/7 coding assistant that knows your style
- Agencies: Manage multiple clients with separate "personas"
- Teams: Automate boilerplate, tests, documentation
- Everyone: Focus on architecture, not repetitive tasks

---

## File Structure (Clean View)

```
jarvis-system/
├── README_JARVIS_MASTER.md    ← You are here
├── START_HERE.md              ← Read this first
├── AUTONOMY_AND_INTERCONNECTION.md ← Understand how it connects
│
├── core/
│   └── orchestrator.py       Central coordinator (runs everything)
│
├── utils/
│   ├── event_bus.py          Communication highway (all events)
│   ├── logger.py             JSON structured logs
│   └── config.py             Configuration
│
├── fireup/                   THE KEY - dynamic startup & auto-adaptation
│   ├── fireup.py             Auto-detects tech, loads skills, updates itself
│   └── dynamic_skills/       Auto-generated workspace-specific code
│
├── jarvis/                   Main package (contains most components)
│   ├── observers/            Watch files, git, conversations
│   ├── learners/             Learn patterns, preferences, trends
│   ├── updaters/             Safe code modification
│   ├── mcp/                  AI brain (context, planning, skill selection)
│   │   └── skills/           Actual skills (django, react, testing...)
│   ├── persona/              Multi-client management
│   ├── scanner/              Project type detection
│   ├── safety/               Approval & rollback
│   ├── archive/              Snapshots & restore
│   └── ...
│
├── data/                     Runtime data (created at runtime)
├── logs/                     Log files (created at runtime)
└── tests/                    Test suites

Essential docs:
├── JARVIS_DESIGN.md          Complete 67KB architecture reference
├── JARVIS_COMPLETE_GUIDE.md  API & operations guide
└── CLEANUP_PLAN.txt         What to keep/remove (if needed)
```

---

## The Autonomy Engine (How It All Connects)

### 1. FIREUP - The Trigger That Adapts

```python
# fireup/fireup.py does this automatically:

async def initialize(workspace):
    profile = await scanner.scan(workspace)
    # → Detects: Django + React + PostgreSQL
    
    skills = determine_skills(profile)
    # → Loads: django_skills, react_skills, postgres_skills
    
    await load_skills(skills)
    # → Skills ready to use
    
    update_fireup_config(profile, skills)
    # → Writes its own config based on what it learned!
    
    generate_dynamic_skills(profile)
    # → Creates auto_generated.py with workspace-specific helpers

# When new folder added:
async def reload_for_workspace_change(new_file_event):
    new_profile = await scanner.scan_again()
    if new_profile.tech_stack changed:
        # → Dynamically load NEW skills
        # → Hot-reload, no restart!
```

**Why this matters**: JARVIS adapts to YOUR project automatically. Add React Native? It loads mobile skills. Add Docker? It loads deployment skills. No config needed.

---

### 2. Event Bus - Everyone Talks Through It

```
Component A (Observer): "I saw a new file!"
    ↓ publishes
EventBus: EVENT: FILE_CREATED {path: models.py, type: python}
    ↓ broadcasts to all subscribers
Component B (Learner): "Learning pattern from this file..."
Component C (Fireup): "Should I reload skills? Check..."
Component D (Persona): "Logging activity for TechCorp persona..."
Component E (Archive): "Maybe backup this..."

No component calls another directly!
Everything is loosely coupled.
```

**Autonomy enabler**: Components can be added/removed without breaking others. System evolves gracefully.

---

### 3. MCP - The Decision Brain

```
You: "Add authentication"

MCP thinks:
1. ContextEngine:
   "This is TechCorp persona (Django project)
    They've used JWT 3 times before
    Current files: api/views.py, no auth yet
    → Need Django REST + SimpleJWT"

2. AutonomousPlanner:
   Steps:
   1. Install djangorestframework-simplejwt
   2. Add to INSTALLED_APPS
   3. Configure SimpleJWT settings
   4. Create UserSerializer
   5. Create TokenObtainPairView
   6. Add to urls.py
   7. Write tests
   8. Update docs

3. SkillSelector:
   For step 1: config_updater (score 0.92)
   For step 2: django_settings_modifier (0.89)
   ... selects best skill for each step

4. Executor:
   Runs skills in order, handles errors
   If skill fails → try next one
   All fail → ask human

5. Verifier:
   Run tests → all 12 pass ✅
   Check syntax → valid ✅
   Done!
```

**Autonomy level**: High - plans and executes multi-step tasks, selects appropriate skills based on context.

---

### 4. Safety Guard - The Enabler

**Without Safety**: Every change needs manual review → no autonomy
**With Safety**: Risk-based approvals → 85% autonomy

```
Risk Assessment:
file = tests/test_*.py      → LOW  → auto-approve ✅
file = requirements.txt    → MEDIUM → PR (auto-merge if CI green)
file = models.py           → HIGH → manual approval ⚠️
file = core/orchestrator.py → CRITICAL → 2-person approval 🔒

Trust Score Impact:
Trust 0.87 (TechCorp) → medium risk AUTO-APPROVED
Trust 0.50 (New) → medium risk NEEDS_REVIEW

Result: JARVIS can act boldly but safely.
```

---

### 5. Persona System - Multi-Client Intelligence

```
persona/techcorp.json:
{
  "name": "TechCorp Inc",
  "workspaces": ["/techcorp-backend", "/techcorp-frontend"],
  "preferences": {
    "backend": "django",
    "testing": "pytest",
    "formatter": "black"
  },
  "trust_score": 0.87,
  "deals": [...]
}

persona/beta.json:
{
  "name": "Beta Inc",
  "workspaces": ["/beta-project"],
  "preferences": {
    "backend": "fastapi",
    "testing": "unittest"
  },
  "trust_score": 0.65
}

Auto-switching:
cd /techcorp-backend → TechCorp persona active (Django + pytest)
cd /beta-project → Beta persona active (FastAPI + unittest)

JARVIS adapts to each client's style automatically.
```

---

### 6. Learners - The Knowledge Builders

```
File created: models.py with Django User

PatternRecognition:
  Parses AST → "django_model_with_custom_user"
  Stores in data/patterns/ with confidence 0.92
  → Future: "Create model" will use this pattern

PreferenceExtractor:
  Checks git blame → author uses Black
  Updates TechCorp persona: formatter=black

PerformanceAnalyzer:
  Task took 18m (avg 2.3h) → record: faster than usual
  → Meta-learner will notice positive outlier

TrendDetector:
  Sees new dep: djangorestframework-simplejwt==3.14.0
  Checks registry → 3.15.0 available
  → Creates TODO: "Update to 3.15.0"
```

Learners run **constantly in background**, building knowledge without any task request.

---

### 7. Meta-Learner - Self-Improvement

```
Meta-Learner (runs every 6 hours):
1. Collect metrics from last 100 tasks
2. Spot anomaly: FileModder slowed from 3s/file to 5s/file
3. Generate hypotheses:
   - "Batch file modifications" → expected 50% faster
   - "Use AST instead of regex" → expected 30% faster
   - "Cache file reads" → expected 20% faster
4. Test hypothesis 1 in sandbox:
   - Before: 100 files × 5s = 500s
   - After: 10 batches × 15s = 150s ✅ 70% faster!
5. Deploy:
   - Update FileModder with batching
   - Canary: 10% workspaces (monitor 24h)
   - Roll out to 100%
6. Record: hypothesis effectiveness = 0.87

JARVIS just improved itself. No human needed.
```

---

### 8. Archive - Time Travel

```
Every modification:
1. Backup file to .jarvis/backups/
2. Log to history DB
3. Compress to daily archive at 2 AM
4. Keep: hourly(24h), daily(30d), weekly(12w), monthly(24m), yearly(10y)

When error occurs:
→ Safety triggers rollback
→ Archive.restore(change_id)
→ All files revert to pre-change state
→ Done in seconds

This safety enables autonomy: JARVIS can act boldly knowing everything is reversible.
```

---

## Complete Autonomous Workflow (End-to-End)

### Example: "Add payment integration"

**You**: (cd into techcorp-backend)
```
$ jarvis execute "Add Stripe payment to checkout"
```

**What Happens**:

1. **Fireup** (already running):
   - Active persona: TechCorp (Django, trust 0.87)
   - Loaded skills: django_skills, react_skills, testing_skills
   - Context: "TechCorp has 3 Stripe integrations before"

2. **MCP receives task**:
   - ContextEngine: searches patterns → "stripe_integration" seen 3×
   - Planner: creates 9-step plan (install SDK, configure, implement, test, docs)
   - SkillSelector: scores skills for each step
   - Result: Plan with skills ready

3. **Safety check**:
   - Risk: MEDIUM (new dependency, code changes)
   - Trust 0.87 → auto-approve ✅

4. **Execute plan**:
   ```
   Step 1: Add stripe to requirements.txt
           → ConfigUpdater (0.3s) ✅
   
   Step 2: Add STRIPE_API_KEY to settings.py
           → FileModder (0.2s) ✅
   
   Step 3: Create payment/models.py (StpeCustomer, Payment)
           → CodeGenerator (2.1s) ✅
   
   Step 4: Create payment/views.py (CreatePayment, Webhook)
           → CodeGenerator (2.5s) ✅
   
   Step 5: Add to urls.py
           → FileModder (0.1s) ✅
   
   Step 6: Write tests (test_payment.py)
           → TestWriter (3.2s) ✅
   
   Step 7: Run tests
           → pytest → 15 tests pass ✅
   
   Step 8: Update README.md
           → DocGenerator (0.8s) ✅
   ```

5. **Automatic PR**:
   - Git commit: "feat(payment): add Stripe integration (JARVIS)"
   - PR #47 created
   - CI runs → all checks pass ✅
   - Auto-merged (medium risk, CI green)

6. **Learning**:
   - PatternRecognition: "stripe_integration_workflow" → store
   - Performance: 9.2m completion (avg 2.3h) → success!
   - Preference: "TechCorp uses Stripe webhooks" → reinforce
   - Trend: "Stripe API v2025-03-01 available" → flag

7. **Deal tracking** (if linked):
   - Deal "E-commerce Platform" progress +1 task
   - Time spent: +0.15h

8. **User notified**:
   ```
   ✅ Stripe payment added!
   - 7 files modified
   - 15 tests added (all passing)
   - PR #47 merged
   - Time saved: ~2 hours
   ```

**Total autonomy**: 95% - only needed you to say "execute" and approve PR (auto-merged).

---

## What Makes This Autonomous (Not Just Automation)

| Feature | Traditional Scripts | JARVIS |
|---------|-------------------|--------|
| **Adapts to project** | No - hardcoded | Yes - Fireup auto-detects tech |
| **Learns your style** | No | Yes - PreferenceExtractor |
| **Self-improves** | No | Yes - MetaLearner |
| **Manages clients** | No | Yes - Persona system |
| **Safe modifications** | No | Yes - Backup + rollback |
| **Plans tasks** | No | Yes - MCP decomposition |
| **Selects skills** | Fixed | Yes - Context-aware scoring |
| **Tracks business** | No | Yes - Deal tracker |
| **Hot-reload** | Restart needed | Yes - Dynamic skill loading |
| **Observable** | Minimal | Full logs, metrics, audit |

**Key insight**: JARVIS isn't just automated tasks. It's an **autonomous agent** that perceives, learns, decides, acts, and improves itself.

---

## Implementation Roadmap (For Your Friend)

### Week 1-2: Get Core Running
- ✅ All core files exist (orchestrator, event_bus, logger, config)
- ✅ Fireup implemented (the key trigger)
- ⚠️ Need to fix imports (use absolute imports properly)
- Goal: `python -m fireup.fireup` starts without errors

### Week 3-4: Implement Observers
- FileSystemObserver (watchdog)
- GitObserver (GitPython)
- Test: file change → event published → PatternRecognition receives it

### Week 5-6: Implement Learners & Updaters
- PatternRecognition (AST parsing)
- FileModder (AST-based editing)
- Test: Create Django model → pattern learned → suggest improvements

### Week 7-8: MCP Intelligence
- Integrate sentence-transformers (embeddings)
- Implement ContextEngine
- Implement SkillSelector
- Create 5 skills (django_model, django_view, test_writer, etc.)
- Test: "Create API" → MCP plans and executes

### Week 9-10: Persona & Safety
- Complete PersonaManager
- Implement SafetyGuard with risk assessment
- Test: Different personas → different behaviors

### Week 11-12: Polish & Deploy
- MetaLearner (self-improvement)
- Archive system
- CLI commands
- Docker deployment
- Documentation finalization

---

## The Files Your Friend Actually Needs

### Must Read (in order):
1. **START_HERE.md** - Complete getting started guide (11KB)
2. **AUTONOMY_AND_INTERCONNECTION.md** - How it all connects (this doc)
3. **JARVIS_DESIGN.md** - Deep reference (67KB, comprehensive)

### Optional Reference:
4. **JARVIS_COMPLETE_GUIDE.md** - API details
5. **README.md** - GitHub README (for showing others)

### Must Implement (code):
1. `fireup/fireup.py` - Already complete! ✅
2. `utils/event_bus.py` - Already complete! ✅
3. `utils/logger.py` - Already complete! ✅
4. `core/orchestrator.py` - Already complete! ✅
5. `jarvis/observers/file_system.py` - Needs integration with watchdog
6. `jarvis/learners/pattern_recognition.py` - Needs AST parsing logic
7. `jarvis/updaters/file_modder.py` - Needs safe editing logic
8. `jarvis/mcp/context_engine.py` - Needs embeddings integration
9. `jarvis/mcp/autonomous_planner.py` - Needs task decomposition
10. `jarvis/mcp/skills/django_skills.py` - Example skill to start

**Start with #5, #6, #7** - get basic "detect → learn" cycle working.

---

## Quick Start Commands (Once Implemented)

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Initialize
jarvis init
  → Creates: data/, logs/, config/

# 3. Add your project
jarvis workspace add /path/to/project
jarvis persona create --name "My Project" --workspace /path/to/project

# 4. Start JARVIS
jarvis start
  → Fireup scans, loads skills, starts observing

# 5. Watch it learn
tail -f logs/jarvis.log | jq .

# 6. Create a test file
echo "class User(models.Model): pass" > test_model.py
# → See log: Pattern discovered: django_model

# 7. Ask for task
jarvis execute "Add REST API for User"
# → Watch MCP plan and execute

# 8. Check status
jarvis status
jarvis metrics
```

---

## The Bottom Line

**JARVIS achieves autonomy through**:

1. **Self-configuring startup** (Fireup reads workspace, loads skills, writes its own config)
2. **Continuous observation** (never stops learning)
3. **Event-driven everything** (components work independently, loosely coupled)
4. **Safety-enabled boldness** (backups/rollback allow experimental autonomy)
5. **Trust-based permissions** (more trust = more freedom)
6. **Meta-learning** (improves its own algorithms)
7. **Persona isolation** (multiple clients, separate knowledge)
8. **Hot-reload** (adapts to new tech instantly)

**The result**: An AI employee that works autonomously, adapts to you, manages multiple clients, and gets better over time.

---

## Your Friend's First Milestone

**Goal**: Get "file change → pattern learned" working.

1. Run `fireup/fireup.py` in test Django project
2. Add new model file
3. Check `data/patterns/` → see new pattern file
4. Check logs → see PATTERN_DISCOVERED event

**That alone is powerful**: JARVIS observing and learning your codebase automatically.

**Then**: Add FileModder → can auto-suggest improvements.
**Then**: Add MCP → can execute tasks.
**Then**: Add safety → can execute safely.
**Then**: Add persona → works for multiple clients.
**Then**: Add meta-learner → system optimizes itself.

One step at a time, but the **architecture is solid**.

---

**You now have the complete blueprint. Time to build.** 🚀

Questions? Read AUTONOMY_AND_INTERCONNECTION.md for deep details.
