@echo off
echo Writing JARVIS MCP config directly...
echo.

:: Find a real Python executable (not the WindowsApps stub)
set PYTHON=
for %%P in (
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Users\Shaik Younus\AppData\Local\Programs\Python\Python313\python.exe"
    "C:\Users\Shaik Younus\AppData\Local\Programs\Python\Python312\python.exe"
    "C:\Users\Shaik Younus\AppData\Local\Programs\Python\Python311\python.exe"
    "C:\Users\Shaik Younus\AppData\Local\Programs\Python\Python310\python.exe"
    "C:\Users\Shaik Younus\AppData\Local\Microsoft\WindowsApps\python.exe"
) do (
    if exist %%P (
        if not defined PYTHON set PYTHON=%%~P
    )
)

:: Also try py launcher
if not defined PYTHON (
    where py >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%i in ('py -c "import sys; print(sys.executable)" 2^>nul') do set PYTHON=%%i
    )
)

if not defined PYTHON (
    echo ERROR: Could not find Python 3.10+
    echo Install Python from https://python.org
    pause
    exit /b 1
)

echo Python found: %PYTHON%
echo.

:: Config file path (Store app)
set CONFIG=%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json

:: JARVIS project path
set JARVIS_PATH=C:\Users\Shaik Younus\Documents\Personal-AE-SC-Jarvis-main

:: Write config using PowerShell (inline — no separate ps1 needed)
PowerShell -ExecutionPolicy Bypass -Command ^
  "$config = Get-Content '%CONFIG%' -Raw | ConvertFrom-Json; ^
   $mcpServers = @{}; ^
   if ($config.PSObject.Properties['mcpServers']) { ^
     $config.mcpServers.PSObject.Properties | ForEach-Object { $mcpServers[$_.Name] = $_.Value } ^
   }; ^
   $mcpServers['jarvis'] = [PSCustomObject]@{ command = '%PYTHON%'; args = @('%JARVIS_PATH%\jarvis_mcp_server.py'); disabled = $false }; ^
   $mcpServers['jarvis-crm'] = [PSCustomObject]@{ command = '%PYTHON%'; args = @('%JARVIS_PATH%\crm_sidecar.py'); disabled = $false }; ^
   $config | Add-Member -Force -NotePropertyName 'mcpServers' -NotePropertyValue ([PSCustomObject]$mcpServers); ^
   $config | ConvertTo-Json -Depth 10 | Set-Content '%CONFIG%' -Encoding UTF8; ^
   Write-Host 'Config written successfully!'"

echo.
echo ===================================
echo  DONE. Now:
echo  1. Quit Claude Desktop (right-click taskbar icon -> Quit)
echo  2. Reopen Claude Desktop
echo  3. JARVIS tools appear in hammer icon
echo ===================================
echo.
pause
