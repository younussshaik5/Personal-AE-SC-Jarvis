@echo off
echo ===== JARVIS MCP Diagnostic =====
echo.
echo [1] Checking Claude config paths...
echo.
set STORE_PATH=%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
set CLASSIC_PATH=%APPDATA%\Claude\claude_desktop_config.json

if exist "%STORE_PATH%" (
    echo FOUND Store app config:
    echo %STORE_PATH%
    echo.
    echo --- Config contents ---
    type "%STORE_PATH%"
) else (
    echo NOT FOUND: %STORE_PATH%
)

echo.
if exist "%CLASSIC_PATH%" (
    echo FOUND Classic config:
    echo %CLASSIC_PATH%
    echo.
    echo --- Config contents ---
    type "%CLASSIC_PATH%"
) else (
    echo NOT FOUND: %CLASSIC_PATH%
)

echo.
echo [2] Python location:
where python
echo.
echo [3] JARVIS server script:
if exist "%~dp0jarvis_mcp_server.py" (
    echo FOUND: %~dp0jarvis_mcp_server.py
) else (
    echo NOT FOUND
)
echo.
pause
