@echo off
REM JARVIS MCP — Windows Setup (Sales People Edition)
REM No terminal knowledge required. Just click and follow prompts.

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║           JARVIS for Sales — Setup                ║
echo ║                                                    ║
echo ║  Don't worry, this is automated. Just follow      ║
echo ║  the prompts. Takes about 2 minutes.              ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM STEP 1: Check Python
REM ────────────────────────────────────────────────────────────────────────────
echo Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python not found. Installing...
    echo.
    echo Opening Microsoft Store to install Python 3.11...
    echo.
    timeout /t 2 /nobreak >nul
    start ms-windows-store://pdp/?productid=9NRWMJP3717K
    echo.
    echo After installing Python, close this window and run setup.bat again.
    pause
    exit /b 1
)

echo ✅ Python found:
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

REM ────────────────────────────────────────────────────────────────────────────
REM STEP 2: Setup .env with API Key
REM ────────────────────────────────────────────────────────────────────────────
echo.
echo Setting up API key...
echo.

if exist .env (
    echo ✅ .env already exists
) else (
    echo ⚠️  Need NVIDIA API key (free, takes 1 minute):
    echo.
    echo 1. Go to: https://build.nvidia.com
    echo 2. Sign up (free tier - no credit card needed)
    echo 3. Click profile → API Keys → Generate Key
    echo 4. Copy the key (starts with nvapi-)
    echo.

    set /p API_KEY="Paste your NVIDIA API key here: "

    if not "!API_KEY!"=="" (
        (
            echo # JARVIS - Sales Intelligence Assistant
            echo NVIDIA_API_KEY=!API_KEY!
        ) > .env
        echo ✅ API key saved
    ) else (
        (
            echo # JARVIS - Sales Intelligence Assistant
            echo NVIDIA_API_KEY=nvapi-your-key-here
        ) > .env
        echo ⚠️  No key entered. Edit .env later with your key.
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

REM ────────────────────────────────────────────────────────────────────────────
REM DONE
REM ────────────────────────────────────────────────────────────────────────────
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║              ✅ SETUP COMPLETE!                   ║
echo ║                                                    ║
echo ║  NEXT STEPS:                                      ║
echo ║  1. Close Claude Desktop completely              ║
echo ║     (Right-click icon → Quit)                    ║
echo ║  2. Wait 3 seconds                               ║
echo ║  3. Reopen Claude Desktop                        ║
echo ║  4. Look for 🔨 icon in chat                    ║
echo ║  5. Type: "Create account Acme Corp"            ║
echo ║  6. You're ready to use JARVIS!                 ║
echo ║                                                    ║
echo ║  Your deal files are in:                         ║
echo ║  %USERPROFILE%\JARVIS\ACCOUNTS\                ║
echo ║                                                    ║
echo ║  For help: Read README.md in the folder          ║
echo ╚════════════════════════════════════════════════════╝
echo.
pause
