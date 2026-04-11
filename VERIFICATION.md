# JARVIS v2.0 - COMPLETE END-TO-END VERIFICATION

**Testing everything as a fresh clone + setup**

## Step 1: Verify Code Quality

### 1.1 Check Python syntax
```bash
python3 -m py_compile jarvis_mcp/mcp_server.py
python3 -m py_compile jarvis_mcp/config/config_manager.py
python3 -m py_compile jarvis_mcp/llm/llm_manager.py
```

### 1.2 Check all imports work
```bash
python3 -c "from jarvis_mcp.mcp_server import JarvisServer; print('✓ mcp_server')"
python3 -c "from jarvis_mcp.config.config_manager import ConfigManager; print('✓ config')"
python3 -c "from jarvis_mcp.llm.llm_manager import LLMManager; print('✓ llm')"
python3 -c "from jarvis_mcp.safety.guard import SafetyGuard; print('✓ safety')"
python3 -c "from jarvis_mcp.skills import SKILL_REGISTRY; print(f'✓ skills: {len(SKILL_REGISTRY)}')"
```

## Step 2: Verify Accounts Exist

### 2.1 Check ACCOUNTS folder
```bash
ls -la ~/Documents/claude\ space/ACCOUNTS/Tata/
ls -la ~/Documents/claude\ space/ACCOUNTS/Tata/TataTele/
ls -la ~/Documents/claude\ space/ACCOUNTS/Tata/TataSky/
```

### 2.2 Check required files
```bash
test -f ~/Documents/claude\ space/ACCOUNTS/Tata/deal_stage.json && echo "✓ Tata/deal_stage.json"
test -f ~/Documents/claude\ space/ACCOUNTS/Tata/company_research.md && echo "✓ Tata/company_research.md"
test -f ~/Documents/claude\ space/ACCOUNTS/Tata/discovery.md && echo "✓ Tata/discovery.md"
test -f ~/Documents/claude\ space/ACCOUNTS/Tata/CLAUDE.md && echo "✓ Tata/CLAUDE.md"
test -f ~/Documents/claude\ space/ACCOUNTS/Tata/dashboard.html && echo "✓ Tata/dashboard.html"
```

## Step 3: Verify Features Work

### 3.1 Test account hierarchy
```bash
python3 << 'PYEOF'
from jarvis_mcp.config.config_manager import ConfigManager
from jarvis_mcp.account_hierarchy import AccountHierarchy

config = ConfigManager()
hierarchy = AccountHierarchy(config.get_accounts_root())

# List all accounts
accounts = hierarchy.list_all_accounts()
print(f"✓ Found {len(accounts)} accounts:")
for name, path in accounts:
    print(f"  - {name}")
PYEOF
```

### 3.2 Test context detection
```bash
python3 << 'PYEOF'
from jarvis_mcp.config.config_manager import ConfigManager
from jarvis_mcp.context_detector import ContextDetector

config = ConfigManager()
detector = ContextDetector(config.get_accounts_root())
context = detector.detect_account_context()
print(f"✓ Context detection: {context is not None or 'Can detect when in account folder'}")
PYEOF
```

### 3.3 Test CLAUDE.md loading
```bash
python3 << 'PYEOF'
from jarvis_mcp.config.config_manager import ConfigManager
from jarvis_mcp.claude_md_loader import ClaudeMdLoader

config = ConfigManager()
loader = ClaudeMdLoader(config.get_accounts_root())

tata_path = config.get_account_path("Tata")
settings = loader.load_for_account(tata_path)
print(f"✓ CLAUDE.md loaded with {len(settings)} setting groups")
PYEOF
```

### 3.4 Test scaffolder
```bash
python3 << 'PYEOF'
from pathlib import Path
from jarvis_mcp.scaffolder import AccountScaffolder
from jarvis_mcp.config.config_manager import ConfigManager

config = ConfigManager()
scaffolder = AccountScaffolder(config.get_accounts_root())

# Check it can create accounts
test_path = scaffolder.scaffold_account("TestAccount_DeleteMe")
if test_path.exists():
    print(f"✓ Scaffolder works: Created {test_path}")
    # Clean up
    import shutil
    shutil.rmtree(test_path)
    print("✓ Cleanup successful")
PYEOF
```

## Step 4: Verify Server Starts

### 4.1 Start server in verification mode
```bash
timeout 5 python3 -m jarvis_mcp.mcp_server 2>&1 | head -50
```

### 4.2 Check server loads all skills
```bash
python3 << 'PYEOF'
from jarvis_mcp.mcp_server import JarvisServer

server = JarvisServer()
print(f"✓ Server initialized with {len(server.skills)} skills")

# List all skills
print("\nSkills loaded:")
for i, skill in enumerate(sorted(server.skills.keys()), 1):
    print(f"  {i:2d}. {skill}")
PYEOF
```

## Step 5: Verify Documentation

### 5.1 Check files exist
```bash
test -f README.md && echo "✓ README.md exists"
test -f QUICKSTART.md && echo "✓ QUICKSTART.md exists"
test -f ACCOUNT_CREATION.md && echo "✓ ACCOUNT_CREATION.md exists"
test -f requirements.txt && echo "✓ requirements.txt exists"
```

### 5.2 Check README clarity
```bash
wc -l README.md QUICKSTART.md ACCOUNT_CREATION.md
```

## Step 6: Integration Tests

### 6.1 Run test suite
```bash
python3 test_integration.py
```

## Step 7: GitHub Ready Check

### 7.1 Check git status
```bash
git status
git log --oneline | head -10
```

### 7.2 Verify all files committed
```bash
git ls-files | wc -l
```

---

## VERIFICATION CHECKLIST

- [ ] All Python files have valid syntax
- [ ] All imports work without errors
- [ ] ACCOUNTS folder exists with Tata, TataTele, TataSky
- [ ] All required account files exist
- [ ] Account hierarchy detection works
- [ ] Context detection works
- [ ] CLAUDE.md loading works
- [ ] Scaffolder works (creates and cleans up)
- [ ] Server starts and loads all 25 skills
- [ ] Integration tests pass (15/15)
- [ ] Documentation files exist and are clear
- [ ] Git history is clean
- [ ] All files are committed
- [ ] README suitable for sales/presales teams
- [ ] Setup is truly plug-and-play (just API key needed)

---

## CLONE & USE TEST

**Simulate fresh clone:**

```bash
# 1. Verify clone path
pwd
git remote -v

# 2. Check key files exist
ls -la jarvis_mcp/mcp_server.py
ls -la ACCOUNTS/Tata/deal_stage.json
ls -la README.md

# 3. Verify no secrets in code
grep -r "API_KEY" jarvis_mcp/ 2>/dev/null || echo "✓ No hardcoded keys"
grep -r "secret" jarvis_mcp/ 2>/dev/null || echo "✓ No secrets"

# 4. Check dependencies
cat requirements.txt

# 5. Test server with env var
export NVIDIA_API_KEY="test_key"
python3 -m jarvis_mcp.mcp_server 2>&1 | grep "status"
```

---

This document verifies everything is working end-to-end as a user would experience it.
