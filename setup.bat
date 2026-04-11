@echo off
REM JARVIS MCP — Setup Wrapper (for backwards compatibility)
REM This script delegates to the universal Python installer.
REM For direct setup, run: python install.py

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║          JARVIS MCP — Universal Setup             ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo.
    echo Please install Python 3.9 or later from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: %PYTHON_VERSION%
echo.
echo Running universal installer...
echo.

REM Run the Python installer
python install.py

exit /b %errorlevel%
