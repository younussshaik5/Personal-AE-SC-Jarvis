# OPENCODE FIREUP SKILL - COMPLETE AUTONOMOUS LAUNCH

## CRITICAL: This skill AUTOMATICALLY starts JARVIS and MCP observer when you say "fireup"

---

## EXECUTION STEPS (Run These Sequentially)

### STEP 0: Pre-flight Checks
```bash
# Verify workspace structure
if [ -d "persona" ] && [ -d "jarvis" ] && [ -d "mcp-opencode-observer" ]; then
    echo "✅ All components present"
else
    echo "❌ Missing components. Install JARVIS first."
    exit 1
fi
```

### STEP 1: Launch MCP Observer (Node.js)
```bash
# Check if already running
if pgrep -f "mcp-opencode-observer" > /dev/null; then
    echo "✅ MCP observer already running"
else
    echo "🚀 Starting MCP observer..."
    # Build if needed
    if [ ! -f "mcp-opencode-observer/dist/index.js" ]; then
        cd mcp-opencode-observer
        npm install
        npm run build
        cd ..
    fi
    
    # Launch in background
    node mcp-opencode-observer/dist/index.js &
    MCP_PID=$!
    echo $MCP_PID > .mcp_observer.pid
    sleep 2
    
    # Verify it started
    if ps -p $MCP_PID > /dev/null; then
        echo "✅ MCP observer started (PID $MCP_PID)"
    else
        echo "❌ MCP observer failed to start"
        exit 1
    fi
fi
```

### STEP 2: Initialize JARVIS Python Core
```bash
# Check if already running
if pgrep -f "jarvis.core.orchestrator" > /dev/null; then
    echo "✅ JARVIS already running"
else
    echo "🤖 Starting JARVIS core..."
    
    # Install package if needed
    if ! python3 -c "import jarvis" 2>/dev/null; then
        pip install -e jarvis
    fi
    
    # Ensure config exists
    if [ ! -f "jarvis/config/jarvis.yaml" ]; then
        python3 jarvis/scripts/setup.py --silent
    fi
    
    # Create data directories
    mkdir -p jarvis/data/personas
    mkdir -p jarvis/data/patterns
    mkdir -p jarvis/data/archives
    mkdir -p jarvis/logs
    
    # Launch JARVIS in background
    cd jarvis
    nohup python3 -m jarvis.core.orchestrator > ../logs/jarvis.log 2>&1 &
    JARVIS_PID=$!
    cd ..
    echo $JARVIS_PID > .jarvis.pid
    sleep 3
    
    # Verify
    if ps -p $JARVIS_PID > /dev/null; then
        echo "✅ JARVIS started (PID $JARVIS_PID)"
    else
        echo "❌ JARVIS failed to start. Check logs/jarvis.log"
        exit 1
    fi
fi
```

### STEP 3: Workspace Scan & Persona Activation
```bash
# Get current workspace path
WORKSPACE="$(pwd)"
echo "🔍 Scanning workspace: $WORKSPACE"

# Trigger scan via JARVIS API
python3 << 'PYEOF'
import sys, json
sys.path.insert(0, 'jarvis')
try:
    from core.orchestrator import Orchestrator
    from utils.config import ConfigManager
    import asyncio
    
    async def scan():
        cfg = ConfigManager()
        cfg.load()
        orc = Orchestrator(cfg.config)
        await orc.initialize()
        print("  ✅ Workspace scan completed")
        await orc.shutdown()
    
    asyncio.run(scan())
except Exception as e:
    print(f"  ⚠ Scan failed: {e}")
PYEOF
```

### STEP 3.5: Launch JARVIS UI Dashboard (Tony Stark Style!)
```bash
# Start the beautiful UI dashboard
echo "🖥️  Launching JARVIS UI dashboard..."

# Install UI dependencies if needed
if ! python3 -c "import http.server" 2>/dev/null; then
    echo "  Installing UI dependencies..."
    pip install -q aiohttp websockets 2>/dev/null
fi

# Launch UI server in background (run from workspace root)
nohup python3 -m jarvis.ui.server > logs/ui.log 2>&1 &
UI_PID=$!
echo $UI_PID > .ui.pid

sleep 1

# Check if UI started
if ps -p $(cat .ui.pid 2>/dev/null) > /dev/null; then
    echo "  ✅ JARVIS UI launched at http://localhost:8080"
    echo ""
    echo " ──────────────────────────────────────"
    echo "   OPEN IN BROWSER: http://localhost:8080"
    echo " ──────────────────────────────────────"
    echo ""
else
    echo "  ⚠ UI failed to start, check logs/ui.log"
fi
```

### STEP 4: Load Persona-Specific Skills
```bash
# Determine active persona from active_persona.json or config
PERSONA_FILE="MEMORY/active_persona.json"
if [ -f "$PERSONA_FILE" ]; then
    PERSONA=$(python3 -c "import json; print(json.load(open('$PERSONA_FILE'))['current_persona'])")
else
    PERSONA="solution_consultant"  # default
fi

echo "👤 Active persona: $PERSONA"

# Load persona skill based on type
case "$PERSONA" in
    "solution_consultant")
        SKILL_FILE="persona/solution_consultant/SOLUTION_CONSULTANT_SKILL.md"
        ;;
    "account_executive")
        SKILL_FILE="persona/account_executive/ACCOUNT_EXECUTIVE_SKILL.md"
        ;;
    *)
        SKILL_FILE="persona/solution_consultant/SOLUTION_CONSULTANT_SKILL.md"
        ;;
esac

if [ -f "$SKILL_FILE" ]; then
    echo "📚 Loaded persona skill: $SKILL_FILE"
    # The skill file content is automatically included in OpenCode's context
else
    echo "⚠ Persona skill not found: $SKILL_FILE"
fi
```

### STEP 5: Verify System Health
```bash
echo "🏥 Health Check..."

# Check MCP observer
if ps -p $(cat .mcp_observer.pid 2>/dev/null) > /dev/null; then
    echo "  ✓ MCP observer: running"
else
    echo "  ✗ MCP observer: stopped"
fi

# Check JARVIS
if ps -p $(cat .jarvis.pid 2>/dev/null) > /dev/null; then
    echo "  ✓ JARVIS core: running"
else
    echo "  ✗ JARVIS core: stopped"
fi

# Check directories
[ -d "MEMORY/patterns" ] && echo "  ✓ Memory patterns: exists" || echo "  ⚠ Memory patterns: missing"
[ -d "jarvis/data/personas" ] && echo "  ✓ Persona data: exists" || echo "  ⚠ Persona data: missing"

# Count learned patterns
if [ -f "MEMORY/patterns/solution_consultant_patterns.json" ]; then
    PATTERNS=$(python3 -c "import json; d=json.load(open('MEMORY/patterns/solution_consultant_patterns.json')); print(len(d.get('interaction_patterns', [])))")
    echo "  ✓ Learned patterns: $PATTERNS"
fi

echo ""
echo "🎉 JARVIS system is ready!"
echo ""
echo "Next steps:"
echo "  - Open http://localhost:8080 for the dashboard"
echo "  - tail -f logs/jarvis.log to watch events"
echo "  - Add accounts under ACCOUNTS/ folder"
```

---

## FULL AUTOMATION SCRIPT

Save this as `fireup` (executable) in your workspace root:

```bash
#!/bin/bash
# fireup - Complete JARVIS + MCP autonomous startup

set -e  # Exit on error

echo "=================================="
echo "   JARVIS AUTONOMOUS FIREUP"
echo "=================================="
echo ""

# Change to workspace root (assuming this script is in it)
cd "$(dirname "$0")"

# Execute steps
. <(cat << 'STEPS'

# STEP 0: Pre-flight
echo "🔹 Step 0/5: Pre-flight checks"
if [ ! -d "persona" ] || [ ! -d "jarvis" ] || [ ! -d "mcp-opencode-observer" ]; then
    echo "❌ Missing JARVIS components. Run setup first:"
    echo "   python3 jarvis/scripts/setup.py"
    exit 1
fi

# STEP 1: MCP Observer
echo "🔹 Step 1/5: Launching MCP Observer"
if ! pgrep -f "mcp-opencode-observer" > /dev/null; then
    if [ ! -f "mcp-opencode-observer/dist/index.js" ]; then
        echo "  Building MCP observer..."
        (cd mcp-opencode-observer && npm install && npm run build) > /dev/null 2>&1
    fi
    node mcp-opencode-observer/dist/index.js > logs/mcp_observer.log 2>&1 &
    echo $! > .mcp_observer.pid
    sleep 2
    if ps -p $(cat .mcp_observer.pid) > /dev/null; then
        echo "  ✅ MCP observer launched"
    else
        echo "  ❌ Failed to start MCP observer"
        exit 1
    fi
else
    echo "  ✅ MCP observer already running"
fi

# STEP 2: JARVIS Core
echo "🔹 Step 2/5: Starting JARVIS core"
if ! pgrep -f "jarvis.core.orchestrator" > /dev/null; then
    # Install if needed
    if ! python3 -c "import jarvis" 2>/dev/null; then
        echo "  Installing JARVIS package..."
        pip install -e jarvis > /dev/null 2>&1
    fi
    
    # Setup config if missing
    if [ ! -f "jarvis/config/jarvis.yaml" ]; then
        echo "  Running first-time setup..."
        python3 jarvis/scripts/setup.py --silent
    fi
    
    # Ensure data dirs
    mkdir -p jarvis/data/{personas,patterns,archives,cache,history}
    mkdir -p logs/{audit,errors,performance}
    
    # Launch
    nohup python3 -m jarvis.core.orchestrator > logs/jarvis.log 2>&1 &
    echo $! > .jarvis.pid
    sleep 3
    
    if ps -p $(cat .jarvis.pid) > /dev/null; then
        echo "  ✅ JARVIS core launched"
    else
        echo "  ❌ Failed to start JARVIS. Check logs/jarvis.log"
        exit 1
    fi
else
    echo "  ✅ JARVIS core already running"
fi

# STEP 3: Workspace Scan
echo "🔹 Step 3/5: Scanning workspace"
# Trigger scan by calling JARVIS API or CLI
python3 << 'PYEOF'
import sys, json
sys.path.insert(0, 'jarvis')
try:
    from core.orchestrator import Orchestrator
    from utils.config import ConfigManager
    import asyncio
    
    async def scan():
        cfg = ConfigManager()
        cfg.load()
        orc = Orchestrator(cfg.config)
        await orc.initialize()
        print("  ✅ Workspace scan completed")
        await orc.shutdown()
    
    asyncio.run(scan())
except Exception as e:
    print(f"  ⚠ Scan failed: {e}")
PYEOF

# STEP 4: Persona Check
echo "🔹 Step 4/5: Persona activation"
if [ -f "MEMORY/active_persona.json" ]; then
    PERSONA=$(python3 -c "import json; print(json.load(open('MEMORY/active_persona.json'))['current_persona'])")
    echo "  ✅ Active persona: $PERSONA"
    
    # Show skill file
    case "$PERSONA" in
        "solution_consultant") SKILL="persona/solution_consultant/SOLUTION_CONSULTANT_SKILL.md" ;;
        "account_executive") SKILL="persona/account_executive/ACCOUNT_EXECUTIVE_SKILL.md" ;;
        *) SKILL="persona/solution_consultant/SOLUTION_CONSULTANT_SKILL.md" ;;
    esac
    [ -f "$SKILL" ] && echo "  ✅ Persona skill loaded: $SKILL"
else
    echo "  ⚠ No persona active (will use default)"
fi

# STEP 5: Health Check
echo "🔹 Step 5/5: Health verification"
HEALTH_OK=true

if ! ps -p $(cat .mcp_observer.pid 2>/dev/null) > /dev/null; then
    echo "  ❌ MCP observer not running"
    HEALTH_OK=false
else
    echo "  ✓ MCP observer healthy"
fi

if ! ps -p $(cat .jarvis.pid 2>/dev/null) > /dev/null; then
    echo "  ❌ JARVIS core not running"
    HEALTH_OK=false
else
    echo "  ✓ JARVIS core healthy"
fi

if [ "$HEALTH_OK" = true ]; then
    echo ""
    echo "=================================="
    echo "✅ JARVIS SYSTEM FULLY OPERATIONAL"
    echo "=================================="
    echo ""
    echo "Quick commands:"
    echo "  Open http://localhost:8080     # Dashboard"
    echo "  tail -f logs/jarvis.log        # Live events"
    echo "  ps aux | grep jarvis           # Check processes"
    echo ""
else
    echo ""
    echo "⚠️  Some components failed. Check logs/"
    exit 1
fi

STEPS

)

chmod +x fireup
echo "✅ Fireup script created and ready"
```

---

## HOW IT WORKS

1. **You type "fireup" in OpenCode**
   - OpenCode executes the commands in this skill file
   - Each ` ```bash ` block runs sequentially

2. **MCP observer starts** (Node.js)
   - Connects to OpenCode's DB
   - Starts polling for conversations
   - Publishes events to JARVIS

3. **JARVIS core starts** (Python)
   - Orchestrator initializes all components
   - Loads active persona from MEMORY/
   - Scans workspace to detect tech stack
   - Loads appropriate skills dynamically

4. **Persona skill loads** (Markdown)
   - Based on active_persona.json
   - Opens correct skill file (solution_consultant or ae)
   - That skill provides context-specific guidance

5. **System runs autonomously**
   - Observers watch files and conversations
   - Learners extract patterns
   - Safety guard approves low-risk changes
   - Archiver takes snapshots
   - Meta-learner improves system weekly

---

## WHAT TRIGGERS THIS

- You say **"fireup"** in OpenCode chat
- OR you run the `fireup` script directly from terminal
- OR OpenCode calls it as part of its startup sequence (if configured)

---

## FILES CREATED/used

| File | Purpose |
|------|---------|
| `OPENCODE_FIREUP_SKILL.md` | THIS file - instructions for OpenCode |
| `fireup` | Executable bash script (generated from above) |
| `mcp-opencode-observer/dist/index.js` | Node.js MCP bridge |
| `jarvis/core/orchestrator.py` | Python main loop |
| `persona/*/SOLUTION_CONSULTANT_SKILL.md` | Persona-specific guidance |
| `MEMORY/active_persona.json` | Current persona state |
| `jarvis/config/jarvis.yaml` | JARVIS configuration |
| `.mcp_observer.pid`, `.jarvis.pid` | Process IDs |

---

## VERIFICATION

After fireup completes, verify:

```bash
# Check processes
ps aux | grep -E "mcp-opencode-observer|jarvis.core.orchestrator"

# Check logs
tail -f logs/mcp_observer.log
tail -f logs/jarvis.log
tail -f MEMORY/patterns/solution_consultant_patterns.json

# Check dashboard
open http://localhost:8080  # or curl http://localhost:8080

# Launch UI Dashboard (Tony Stark style!)
echo "🖥️  Launching JARVIS UI dashboard..."
nohup python3 -m jarvis.ui.server > logs/ui.log 2>&1 &
echo $! > .ui.pid
sleep 1
if ps -p $(cat .ui.pid 2>/dev/null) > /dev/null; then
    echo "✅ JARVIS UI running at http://localhost:8080"
    echo ""
    echo " ──────────────────────────────────────"
    echo "   OPEN IN BROWSER: http://localhost:8080"
    echo " ──────────────────────────────────────"
    echo ""
else
    echo "⚠ UI failed, check logs/ui.log"
fi
```

---

## DASHBOARD CREDENTIALS

After fireup completes:

1. **Open your browser**
2. **Navigate to**: `http://localhost:8080`
3. **See your JARVIS CRM** - Fully synchronized with MCP and JARVIS core

**Dashboard features:**
- **Live event stream** - See everything JARVIS observes
- **Persona management** - Switch between Solution Consultant and AE
- **Deal tracking CRM** - Create, track, and manage deals
- **Workspace overview** - Tech stack, file counts, recent edits
- **Approval queue** - One-click approve/reject
- **Patterns & competitors** - Learned insights
- **Quick actions** - Snapshot, evolve, scan, backup
- **System health** - Uptime, message count, change log
- **Holographic UI** - Tony Stark JARVIS aesthetic

All data syncs in real-time via MCP WebSocket connection.

---

## TROUBLESHOOTING

**MCP observer fails to start**:
- Check Node.js: `node --version` (need 18+)
- Rebuild: `cd mcp-opencode-observer && npm run build`
- Check logs: `logs/mcp_observer.log`

**JARVIS core fails**:
- Check Python: `python3 --version` (need 3.11+)
- Install deps: `pip install -e jarvis`
- Check logs: `logs/jarvis.log`

**No persona switching**:
- Ensure `MEMORY/active_persona.json` exists
- Manually set: `echo '{"current_persona":"solution_consultant"}' > MEMORY/active_persona.json`
- Re-run `fireup`

**Skills not loading**:
- Check `mcp/skills/` directory exists with skill files
- Check `fireup_config.json` for loaded skills list
- Check JARVIS logs for import errors

---

This file is the **complete instruction set** that makes everything happen automatically when you say "fireup". All steps are sequential with error checking and verification.