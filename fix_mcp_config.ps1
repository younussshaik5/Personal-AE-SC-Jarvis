# JARVIS — Fix Claude Desktop MCP Config
# Right-click this file → "Run with PowerShell"

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       JARVIS MCP Config Fixer                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. JARVIS project path (same folder as this script) ─────────────────
$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ProjectPath "jarvis_mcp_server.py"
$CrmScript    = Join-Path $ProjectPath "crm_sidecar.py"

if (-not (Test-Path $ServerScript)) {
    Write-Host "❌  Cannot find jarvis_mcp_server.py in: $ProjectPath" -ForegroundColor Red
    Write-Host "    Make sure you run this from inside the JARVIS project folder." -ForegroundColor Red
    pause; exit 1
}

Write-Host "  Project : $ProjectPath" -ForegroundColor Gray

# ── 2. Find Python ────────────────────────────────────────────────────────
$Python = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python 3\.(1[0-9]|[2-9]\d)") {
            $Python = (Get-Command $candidate).Source
            break
        }
    } catch {}
}

if (-not $Python) {
    Write-Host "❌  Python 3.10+ not found. Install from https://python.org" -ForegroundColor Red
    pause; exit 1
}

Write-Host "  Python  : $Python" -ForegroundColor Gray

# ── 3. Find Claude Desktop config (Store app path first, then classic) ───
$StoreConfigPath  = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json"
$ClassicConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"

if (Test-Path (Split-Path $StoreConfigPath -Parent)) {
    $ConfigPath = $StoreConfigPath
    Write-Host "  Config  : Store app path (UWP)" -ForegroundColor Gray
} elseif (Test-Path (Split-Path $ClassicConfigPath -Parent)) {
    $ConfigPath = $ClassicConfigPath
    Write-Host "  Config  : Classic install path" -ForegroundColor Gray
} else {
    # Create the classic path
    $ConfigDir = Split-Path $ClassicConfigPath -Parent
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    $ConfigPath = $ClassicConfigPath
    Write-Host "  Config  : Created new config directory" -ForegroundColor Yellow
}

# ── 4. Load existing config ───────────────────────────────────────────────
if (Test-Path $ConfigPath) {
    $BackupPath = $ConfigPath -replace "\.json$", ".json.bak"
    Copy-Item $ConfigPath $BackupPath -Force
    Write-Host "  Backup  : $BackupPath" -ForegroundColor Gray
    $Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json -AsHashtable
} else {
    $Config = @{}
}

# ── 5. Patch mcpServers ───────────────────────────────────────────────────
if (-not $Config.ContainsKey("mcpServers")) { $Config["mcpServers"] = @{} }

$Config["mcpServers"]["jarvis"] = @{
    command  = $Python
    args     = @($ServerScript)
    disabled = $false
}

if (Test-Path $CrmScript) {
    $Config["mcpServers"]["jarvis-crm"] = @{
        command  = $Python
        args     = @($CrmScript)
        disabled = $false
    }
}

# ── 6. Add trusted folders ────────────────────────────────────────────────
if (-not $Config.ContainsKey("preferences")) { $Config["preferences"] = @{} }
if (-not $Config["preferences"].ContainsKey("localAgentModeTrustedFolders")) {
    $Config["preferences"]["localAgentModeTrustedFolders"] = @()
}
foreach ($p in @($ProjectPath, (Join-Path $ProjectPath "ACCOUNTS"))) {
    if ($Config["preferences"]["localAgentModeTrustedFolders"] -notcontains $p) {
        $Config["preferences"]["localAgentModeTrustedFolders"] += $p
    }
}

# ── 7. Write config ───────────────────────────────────────────────────────
$Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8

# ── 8. Done ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        ✅  JARVIS Config Fixed!              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  MCP entries written:" -ForegroundColor White
Write-Host "    ✅  jarvis" -ForegroundColor Green
if (Test-Path $CrmScript) { Write-Host "    ✅  jarvis-crm" -ForegroundColor Green }
Write-Host ""
Write-Host "  ⚡ NEXT STEP: Quit Claude Desktop → reopen it." -ForegroundColor Yellow
Write-Host "     JARVIS tools will appear in the 🔨 Tools panel." -ForegroundColor Yellow
Write-Host ""
pause
