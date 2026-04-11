@echo off
echo ===== Current Claude Desktop Config =====
echo.
set CONFIG=%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
echo Path: %CONFIG%
echo.
type "%CONFIG%"
echo.
echo ===== Python Test =====
python -c "import sys; print('Python:', sys.executable, sys.version)"
echo.
echo ===== Test JARVIS Server Starts =====
python "C:\Users\Shaik Younus\Documents\Personal-AE-SC-Jarvis-main\jarvis_mcp_server.py" --help 2>&1 | head -5
echo.
pause
