# JARVIS Testing Checklist — PHASE 7

> **Comprehensive manual and automated testing plan for JARVIS MCP Server (1.0.0)**

---

## Automated Tests (Unit & Integration)

Run these commands to execute test suites:

```bash
# Install dev dependencies (if not already done)
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_config.py -v
pytest tests/test_platform_utils.py -v
pytest tests/test_safety.py -v
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=jarvis_mcp --cov-report=html
```

### Test Coverage Target

- **Minimum:** 70% coverage on core modules (`config_manager.py`, `platform_utils.py`, `mcp_server.py`)
- **Ideal:** 85%+ across entire codebase
- Coverage report generated in `htmlcov/index.html`

---

## Platform-Specific Manual Testing

### Pre-Flight Checklist (All Platforms)

Before running any platform tests:

- [ ] Delete existing venv (if present)
- [ ] Delete existing `JARVIS/` folder in home directory
- [ ] Delete `.env` file
- [ ] Delete `claude_desktop_config.json` modifications
- [ ] Close Claude Desktop completely
- [ ] Clear any cached processes (see platform-specific sections)

### Windows (WSL or Git Bash)

**Environment:** Windows 11, Python 3.9+ in WSL or native

#### Setup Test

```bash
# 1. Navigate to project directory
cd /mnt/c/Users/YourName/Documents/Personal-AE-SC-Jarvis

# 2. Run setup script
bash setup.sh

# Expected output:
# ✅ Python 3.9+ detected
# ✅ Virtual environment created
# ✅ Dependencies installed
# ✅ .env file created with API key prompt
# ✅ JARVIS_HOME set to [path]
# ✅ ACCOUNTS folder created
# ✅ Claude Desktop configured
# ✅ Setup complete!
```

**Tests:**
- [ ] Setup completes without errors
- [ ] `venv/Scripts/activate.bat` exists and activates correctly
- [ ] `.env` file created and contains `NVIDIA_API_KEY=nvapi-...`
- [ ] `ACCOUNTS/` directory created at correct path
- [ ] `claude_desktop_config.json` updated with JARVIS server config

#### API Key Test

```bash
# With venv activated
python check_api_key.py

# Expected output:
# ✓ NVIDIA API key valid
# ✓ Kimi K2 model accessible
```

**Tests:**
- [ ] API key validation passes
- [ ] No "key exhausted" errors
- [ ] Script completes in < 5 seconds

#### Port Conflict Test

```bash
# 1. Occupy port 8000 in one terminal
nc -l 127.0.0.1 8000 &

# 2. Start JARVIS in another terminal
bash setup.sh

# Expected behavior:
# - JARVIS detects port 8000 in use
# - Finds next available port (8001, 8002, etc.)
# - Logs: "Using alternate port 8001 instead of 8000"
# - CRM dashboard opens on http://localhost:8001
```

**Tests:**
- [ ] Port conflict detected
- [ ] Alternate port found automatically
- [ ] CRM dashboard opens on alternate port
- [ ] No process remains hanging on port 8000

#### Graceful Shutdown Test

```bash
# With JARVIS running in Claude Desktop
# Press Ctrl+C in terminal where Claude Desktop was started

# Expected behavior:
# - CRM subprocess terminates
# - All file handles closed
# - Port is freed (check with: netstat -ano | grep 8000)
# - No orphaned processes
```

**Tests:**
- [ ] Graceful shutdown completes in < 5 seconds
- [ ] Port is freed (can bind again immediately)
- [ ] No orphaned `serve_crm.py` processes
- [ ] No resource leaks (check Task Manager)

#### Skill Execution Test

1. **Create Account:**
   ```
   "Create account AcmeWindow. They're evaluating us, 
    primary contact is Sarah, target $200k, March deadline."
   ```
   - [ ] Account folder created at `~/JARVIS/ACCOUNTS/AcmeWindow/`
   - [ ] `deal_stage.json` with correct ARR/stage
   - [ ] `discovery.md` populated with notes

2. **Run Skill:**
   ```
   "Score MEDDPICC for AcmeWindow"
   ```
   - [ ] MEDDPICC runs without error
   - [ ] Output shows 8 dimensions (M, E, D, D, P, I, C, C)
   - [ ] File saved to `meddpicc.md`
   - [ ] Evolution log updated with `[timestamp] ✓ meddpicc`

3. **Cascade Test:**
   - [ ] After MEDDPICC completes, downstream skills auto-trigger:
     - risk_report
     - battlecard
     - value_architecture
   - [ ] Each skill generates output file
   - [ ] Evolution log shows cascade entries

#### Error Handling Test

```bash
# Test 1: Invalid account name
"Get summary for ../../../etc/passwd"

# Expected: Error message about invalid account name
# Test passes if no path traversal attempted
```

- [ ] Path traversal blocked
- [ ] Alphanumeric-only validation enforced
- [ ] Error message is clear

```bash
# Test 2: Missing API key
# Remove NVIDIA_API_KEY from .env, restart Claude Desktop
"Score MEDDPICC for AcmeWindow"

# Expected: ❌ API key not found error (with helpful message)
```

- [ ] Missing key detected early
- [ ] Error message suggests solution (add key to .env)
- [ ] Skill doesn't hang or timeout waiting for key

```bash
# Test 3: Skill timeout (set JARVIS_SKILL_TIMEOUT=10)
# Create a custom skill that sleeps > 10 seconds
# Run it

# Expected: Timeout after 10 seconds, logged as error
```

- [ ] Timeout fires after configured duration
- [ ] Skill is cancelled cleanly
- [ ] Queue worker continues processing
- [ ] No orphaned async tasks

### macOS (Intel or Apple Silicon)

**Environment:** macOS 12.0+, Python 3.9+, zsh or bash

#### Setup Test

```bash
# 1. Navigate to project
cd ~/Documents/Personal-AE-SC-Jarvis

# 2. Run setup
bash setup.sh

# Expected: Same as Windows (above), but paths use ~/
```

**Tests:**
- [ ] Setup completes without errors
- [ ] Python version check passes (Python 3.9+)
- [ ] `venv/bin/activate` works correctly
- [ ] `.env` created in project root
- [ ] `~/JARVIS/ACCOUNTS/` created (not `~/JARVIS_ACCOUNTS/`)

#### Crash Recovery Test (macOS only)

```bash
# 1. Start JARVIS (Claude Desktop + subprocess)
# 2. Kill subprocess manually
killall -9 serve_crm.py

# 3. Try to use JARVIS (run a skill)
"Score MEDDPICC for AcmeAccount"

# Expected behavior:
# - JARVIS detects dead subprocess
# - Restarts serve_crm.py automatically
# - Skill runs successfully
```

**Tests:**
- [ ] Dead subprocess detected
- [ ] Automatic restart triggered
- [ ] CRM dashboard recovers
- [ ] No manual restart needed

#### Signal Handler Test (macOS/Linux only)

```bash
# 1. Start JARVIS
# 2. Send SIGTERM
kill -TERM $(pgrep -f "crm_sidecar.py")

# Expected:
# - Graceful shutdown initiated
# - subprocess receives SIGTERM
# - Waits 5 seconds for clean shutdown
# - Kills forcefully if needed
```

**Tests:**
- [ ] SIGTERM handled gracefully
- [ ] SIGINT (Ctrl+C) also handled
- [ ] Cleanup completes within 10 seconds
- [ ] No orphaned processes

#### File System Test (macOS only)

```bash
# Test case insensitive filesystem behavior
# macOS APFS is case-insensitive by default

# Create account "AcmeCorp"
"Create account AcmeCorp..."

# Try to access as "acmecorp"
"Get summary for acmecorp"

# Expected: Finds account despite case difference (if APFS)
```

**Tests:**
- [ ] Case handling consistent (document behavior)
- [ ] No unexpected file conflicts
- [ ] Whitelist validation still works

### Linux (Ubuntu 20.04 LTS or newer)

**Environment:** Linux with bash, Python 3.9+

#### Setup Test

```bash
# Same as macOS/Windows
bash setup.sh

# Additionally verify:
# [ ] glibc version compatible (ldd --version)
# [ ] No WSL (check: grep -i "microsoft" /proc/version)
```

**Tests:**
- [ ] Dependencies install without build errors
- [ ] No C extension compilation failures
- [ ] Virtual environment uses correct Python

#### Port Cleanup Test (Linux)

```bash
# Check if port is in use with different tools
ss -tlnp | grep 8000
netstat -tlnp | grep 8000
lsof -ti :8000

# Kill existing process gracefully
kill -TERM $(lsof -ti :8000)

# Verify port is freed
ss -tlnp | grep 8000  # Should be empty
```

**Tests:**
- [ ] Port checking works with `ss` or `netstat`
- [ ] Process killing works with `kill -TERM`
- [ ] Port freed within 5 seconds
- [ ] No socket in TIME_WAIT state

#### Permissions Test

```bash
# Test with read-only ACCOUNTS directory (simulate permission issue)
chmod 444 ~/JARVIS/ACCOUNTS

# Try to create new account
"Create account TestAccount..."

# Expected: Error message about permissions
```

**Tests:**
- [ ] Permission errors caught and logged
- [ ] Helpful error message (e.g., "Cannot write to ACCOUNTS directory")
- [ ] No crash or silent failure

#### systemd Service Test (Optional)

```bash
# Create systemd service file
# Start as service
systemctl start jarvis

# Check status
systemctl status jarvis

# View logs
journalctl -u jarvis -f
```

**Tests:**
- [ ] Service starts and stays running
- [ ] Graceful stop on `systemctl stop jarvis`
- [ ] Restarts on crash (if configured)

---

## Cross-Platform Integration Tests

### Scenario 1: Fresh Install → First Skill

1. **Clean system** (new user, no JARVIS installed)
2. **Clone repo** from GitHub
3. **Run setup.sh** (or setup.bat on Windows)
4. **Restart Claude Desktop**
5. **Create account:**
   ```
   "Create account TestCorp. Target market is mid-market.
    ARR goal is $150k. We're competing with Competitor1."
   ```
6. **Run skill:**
   ```
   "Score MEDDPICC for TestCorp"
   ```

**Expected:**
- [ ] Account created with correct files
- [ ] Skill runs without error
- [ ] Output saved and readable
- [ ] Evolution log shows entry with timestamp

### Scenario 2: Multi-Deal Pipeline

1. **Create 3 accounts** (different stages)
2. **Run different skills** on each:
   - Account 1: get_account_summary
   - Account 2: track_meddpicc
   - Account 3: get_proposal
3. **Check parallel execution** (all 3 in queue simultaneously)

**Expected:**
- [ ] All skills queue and execute
- [ ] Queue shows priority order
- [ ] Skills don't interfere with each other
- [ ] All outputs generated correctly

### Scenario 3: File Drop → Auto-Processing

1. **Create account with minimal discovery.md**
2. **Drop a meeting transcript** (.txt file) into account folder
3. **Trigger:** `"Process meeting transcript for Account1"`

**Expected:**
- [ ] File detected by watcher
- [ ] Intelligence extracted
- [ ] discovery.md updated with new signals
- [ ] Cascade fires automatically

### Scenario 4: Error Recovery

1. **Simulate network error** (disconnect internet mid-skill)
2. **Resume:**
   ```
   "Retry the last skill for TestCorp"
   ```

**Expected:**
- [ ] Retry engine kicks in
- [ ] Attempts up to 3 times with exponential backoff
- [ ] Either succeeds or creates a TODO item

### Scenario 5: Rate Limit Handling

1. **Add only 1 NVIDIA key** (rate limit scenario)
2. **Queue 5 skills** simultaneously on different accounts
3. **Observe queue behavior**

**Expected:**
- [ ] First key rate limited, others continue
- [ ] No hanging or timeouts
- [ ] Automatic key rotation to alternate keys
- [ ] All skills eventually complete

---

## Performance Baselines

Measure and document baseline performance:

| Operation | Target | Acceptable Range |
|---|---|---|
| First skill generation | < 30s | 20-45s |
| Skill with cascade | < 2 min | 1.5-3 min |
| Queue processing (5 skills) | < 5 min | 4-7 min |
| Account creation | < 1s | 0.5-2s |
| CRM dashboard load | < 2s | 1-3s |

**Record on:**
- [ ] Windows (WSL)
- [ ] macOS (Intel)
- [ ] macOS (Apple Silicon)
- [ ] Linux (Ubuntu)

---

## Browser/CLI Verification

### CRM Dashboard

1. Open http://localhost:8000 in browser
2. Check all UI elements:
   - [ ] Pipeline metrics display
   - [ ] Deal list loads
   - [ ] Click deal → detail view loads
   - [ ] MEDDPICC scores visible
   - [ ] Risk badges show (RED/AMBER/GREEN)
   - [ ] Export to PDF works

### Claude Desktop Integration

1. Check for tools icon (hammer ⚒️) in chat bar
2. Click it:
   - [ ] 26+ tools listed
   - [ ] Descriptions match documentation
   - [ ] No duplicate tools
   - [ ] Tools organized by category

---

## Regression Testing

Run these test suites before every release:

### Core Functionality

```bash
# Run critical skill tests
pytest tests/test_meddpicc.py tests/test_proposal.py tests/test_risk_report.py -v
```

- [ ] All skill tests pass
- [ ] No new warnings in output
- [ ] Execution time within baselines

### Safety & Security

```bash
# Run security-focused tests
pytest tests/test_config.py tests/test_safety.py -v
```

- [ ] Path traversal blocked
- [ ] Config validation passes
- [ ] Input sanitization works
- [ ] Error messages don't expose sensitive info

### Integration

```bash
# Run integration tests
pytest tests/test_integration.py -v
```

- [ ] Skill execution end-to-end
- [ ] Cascade triggers correctly
- [ ] Learning system records data
- [ ] Error recovery works

---

## Release Checklist

Before releasing version X.Y.Z:

### Code Quality
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No critical security issues (manual audit of config, file I/O, subprocess handling)
- [ ] Code coverage ≥ 70% on critical modules
- [ ] No lint errors (`flake8 jarvis_mcp/`)
- [ ] Type hints correct (`mypy jarvis_mcp/`)

### Documentation
- [ ] README.md up to date
- [ ] TESTING_CHECKLIST.md (this file) up to date
- [ ] Inline code comments for complex logic
- [ ] API documentation generated (`pdoc jarvis_mcp/`)

### Platform Support
- [ ] Windows (WSL) tested and working
- [ ] macOS (Intel) tested and working
- [ ] macOS (Apple Silicon) tested and working
- [ ] Linux (Ubuntu 20.04+) tested and working

### Deployment
- [ ] GitHub release tag created (`git tag vX.Y.Z`)
- [ ] Release notes written (new features, fixes, breaking changes)
- [ ] PyPI package ready (if applicable)

---

## Known Limitations (Document Here)

### Windows Limitations
- WSL required (native Windows support not yet available)
- Signal handling via atexit instead of POSIX signals

### macOS Limitations
- Apple Silicon (M1/M2) may have slower performance due to emulation of some Python packages

### Linux Limitations
- Requires glibc 2.31+ (Ubuntu 20.04 LTS or newer)

---

## Issues & Workarounds

### "Python not found" on Windows
**Fix:** Use WSL (Windows Subsystem for Linux) or Git Bash, not native Windows PowerShell

### "JARVIS_HOME not set"
**Fix:** Run `bash setup.sh` again to initialize environment variables

### "Port 8000 in use"
**Fix:** Change `CRM_PORT=8001` in `.env`, restart Claude Desktop

### "API key exhausted"
**Fix:** Add more keys to `.env`:
```
NVIDIA_API_KEY=nvapi-key1
NVIDIA_API_KEY_2=nvapi-key2
NVIDIA_API_KEY_3=nvapi-key3
```

---

**Last Updated:** April 2026
**Test Coverage:** 4 test files, 80+ test cases
**Maintainer:** JARVIS Team
