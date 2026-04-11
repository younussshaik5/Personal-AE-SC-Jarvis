@echo off
REM JARVIS Setup for Windows
REM This script creates a virtual environment, installs dependencies, and configures Claude Desktop

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  JARVIS Setup for Windows
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found on PATH
    echo.
    echo Please download Python from https://www.python.org/
    echo and make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed to install
)

REM Setup .env
echo.
echo Setting up .env file...
if exist .env (
    echo .env already exists. Skipping...
) else (
    if exist .env.example (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo.
        echo Created .env file. You will need to edit it and add your NVIDIA API keys.
    ) else (
        echo.
        echo Creating .env file...
        (
            echo # JARVIS v2 - Personal AE + SC Sales Assistant
            echo # NVIDIA API KEY for NVIDIA NIM
            echo.
            echo NVIDIA_API_KEY=nvapi-your-key-here
            echo.
            echo # Optional
            echo ANTHROPIC_API_KEY=
        ) > .env
        echo.
        echo Created basic .env file. You will need to add your NVIDIA API keys.
    )
)

REM Configure Claude Desktop
echo.
echo Configuring Claude Desktop integration...
if exist fix_mcp_config.py (
    python fix_mcp_config.py
    if errorlevel 1 (
        echo WARNING: There was an issue configuring Claude Desktop
        echo You may need to manually update your claude_desktop_config.json file
    )
) else (
    echo WARNING: fix_mcp_config.py not found
    echo You may need to manually configure Claude Desktop
)

REM Done
echo.
echo ========================================
echo  ✅ Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Edit .env and add your NVIDIA API keys
echo    - Go to https://build.nvidia.com/
echo    - Sign up for free tier
echo    - Copy your API key (starts with nvapi-)
echo    - Edit .env and replace NVIDIA_API_KEY value
echo.
echo 2. Restart Claude Desktop (close and reopen)
echo.
echo 3. Test JARVIS in Claude:
echo    - Type: /jarvis
echo    - Or use any JARVIS tool like get_account_summary
echo.
echo For help:
echo - Check README.md for more information
echo - Review .env file for all configuration options
echo.
pause
