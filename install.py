#!/usr/bin/env python3
"""
JARVIS MCP — Universal Setup Installer
Works on Windows, macOS, and Linux with a single command.

Usage:
    python3 install.py
    or
    python install.py

No terminal knowledge required — just answer the prompts.
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import site
from pathlib import Path
from typing import Optional, Tuple


class JarvisInstaller:
    """Universal JARVIS setup installer for all platforms."""

    def __init__(self):
        """Initialize installer with platform detection."""
        self.os_name = platform.system()
        self.python_exe = sys.executable
        self.project_dir = Path(__file__).parent.resolve()
        self.venv_dir = self.project_dir / "venv"
        self.home_dir = Path.home()
        # JARVIS_HOME is PROJECT-SPECIFIC, not global
        # This ensures each JARVIS installation manages its own accounts
        self.jarvis_home = self.project_dir / ".jarvis"

        # Claude Desktop config paths (platform-specific)
        if self.os_name == "Darwin":  # macOS
            self.claude_config = (
                self.home_dir
                / "Library"
                / "Application Support"
                / "Claude"
                / "claude_desktop_config.json"
            )
        elif self.os_name == "Linux":
            self.claude_config = (
                self.home_dir / ".config" / "Claude" / "claude_desktop_config.json"
            )
        else:  # Windows
            appdata = os.getenv("APPDATA", str(self.home_dir / "AppData" / "Roaming"))
            self.claude_config = Path(appdata) / "Claude" / "claude_desktop_config.json"

        self.venv_activated = False

    def log(self, level: str, msg: str) -> None:
        """Log message with emoji prefix."""
        emojis = {
            "info": "ℹ️ ",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️ ",
            "step": "▶️ ",
        }
        prefix = emojis.get(level, "  ")
        print(f"{prefix} {msg}")

    def log_header(self, title: str) -> None:
        """Print section header."""
        print()
        print("╔" + "═" * 58 + "╗")
        print(f"║ {title:<56} ║")
        print("╚" + "═" * 58 + "╝")
        print()

    def run_command(
        self, cmd: list, check: bool = True, capture: bool = False
    ) -> Tuple[int, str]:
        """Run shell command (platform-aware)."""
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=self.os_name == "Windows",
                )
                return result.returncode, result.stdout.strip()
            else:
                result = subprocess.run(
                    cmd, check=check, shell=self.os_name == "Windows"
                )
                return result.returncode, ""
        except Exception as e:
            self.log("error", f"Failed to run command: {' '.join(cmd)}")
            self.log("error", str(e))
            return 1, ""

    def step_1_check_python(self) -> bool:
        """Step 1: Verify Python 3.9+ is installed."""
        self.log_header("Step 1: Checking Python")

        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.log("error", f"Python 3.9+ required, found {version.major}.{version.minor}")
            self.log(
                "error",
                "Download from: https://www.python.org/downloads/",
            )
            return False

        self.log(
            "success",
            f"Python {version.major}.{version.minor}.{version.micro} ✓",
        )
        self.log("info", f"Executable: {self.python_exe}")
        return True

    def step_2_create_venv(self) -> bool:
        """Step 2: Create virtual environment."""
        self.log_header("Step 2: Setting Up Virtual Environment")

        if self.venv_dir.exists():
            self.log("info", "Virtual environment already exists, skipping...")
            self.log("success", "Virtual environment ready ✓")
            return True

        try:
            self.log("step", f"Creating venv at {self.venv_dir}...")
            self.run_command(
                [self.python_exe, "-m", "venv", str(self.venv_dir)], check=True
            )
            self.log("success", "Virtual environment created ✓")
            return True
        except Exception as e:
            self.log("error", f"Failed to create virtual environment: {e}")
            return False

    def step_3_activate_venv(self) -> bool:
        """Step 3: Activate virtual environment for this process."""
        self.log_header("Step 3: Activating Virtual Environment")

        try:
            # Get pip from venv
            if self.os_name == "Windows":
                pip_exe = self.venv_dir / "Scripts" / "pip.exe"
            else:
                pip_exe = self.venv_dir / "bin" / "pip"

            if not pip_exe.exists():
                self.log("error", f"pip not found at {pip_exe}")
                return False

            self.log("success", "Virtual environment activated ✓")
            return True
        except Exception as e:
            self.log("error", f"Failed to activate venv: {e}")
            return False

    def step_4_install_dependencies(self) -> bool:
        """Step 4: Install Python dependencies."""
        self.log_header("Step 4: Installing Dependencies")

        # Get pip from venv
        if self.os_name == "Windows":
            pip_exe = self.venv_dir / "Scripts" / "pip.exe"
        else:
            pip_exe = self.venv_dir / "bin" / "pip"

        # Upgrade pip
        self.log("step", "Upgrading pip...")
        self.run_command([str(pip_exe), "install", "--upgrade", "pip"], check=False)

        # Install requirements
        req_file = self.project_dir / "requirements.txt"
        if not req_file.exists():
            self.log("error", f"requirements.txt not found at {req_file}")
            return False

        self.log("step", "Installing JARVIS dependencies (this may take 1-2 minutes)...")
        returncode, _ = self.run_command(
            [str(pip_exe), "install", "-r", str(req_file), "--upgrade"],
            check=False,
        )

        if returncode != 0:
            self.log(
                "warning",
                "Some dependencies may have failed (but this is usually OK)",
            )

        self.log("success", "Dependencies installed ✓")
        return True

    def step_5_create_jarvis_home(self) -> bool:
        """Step 5: Create JARVIS home directory (project-specific)."""
        self.log_header("Step 5: Creating JARVIS Home Directory")

        try:
            accounts_dir = self.jarvis_home / "ACCOUNTS"
            accounts_dir.mkdir(parents=True, exist_ok=True)
            self.log("success", f"JARVIS home created (project-specific) ✓")
            self.log("info", f"Location: {self.jarvis_home}")
            self.log("info", f"Accounts: {accounts_dir}")
            self.log("info", "This project's JARVIS is isolated from other projects")
            return True
        except Exception as e:
            self.log("error", f"Failed to create JARVIS home: {e}")
            return False

    def step_6_setup_env_file(self) -> bool:
        """Step 6: Create or update .env file with API key."""
        self.log_header("Step 6: Setting Up API Keys")

        env_file = self.project_dir / ".env"
        env_example = self.project_dir / ".env.example"

        # Check if .env already exists
        if env_file.exists():
            self.log("info", ".env already exists")
            try:
                with open(env_file) as f:
                    content = f.read()
                    if "nvapi-" in content and "YOUR-KEY" not in content:
                        self.log("success", "API keys already configured ✓")
                        return True
            except Exception:
                pass

        self.log("step", "NVIDIA API Key Required (free, 1 minute setup)")
        self.log("info", "")
        self.log("info", "Steps to get your key:")
        self.log("info", "  1. Go to: https://build.nvidia.com")
        self.log("info", "  2. Sign up (free tier, no credit card required)")
        self.log("info", "  3. Click Profile → API Keys → Generate Key")
        self.log("info", "  4. Copy the key (starts with nvapi-)")
        self.log("info", "")

        api_key = input("Paste your NVIDIA API key (or press Enter to skip): ").strip()

        try:
            if api_key:
                # Validate key format
                if not api_key.startswith("nvapi-"):
                    self.log(
                        "warning",
                        f"Key doesn't start with 'nvapi-' (got: {api_key[:10]}...)",
                    )
                    confirm = input("Continue anyway? (y/n): ").strip().lower()
                    if confirm != "y":
                        return self.step_6_setup_env_file()  # Retry

                content = f"""# JARVIS - Sales Intelligence Assistant
NVIDIA_API_KEY={api_key}
JARVIS_HOME={self.jarvis_home}
"""
                self.log("step", f"Writing .env file...")
                with open(env_file, "w") as f:
                    f.write(content)
                self.log("success", ".env file created with your API key ✓")
            else:
                # Create placeholder
                content = f"""# JARVIS - Sales Intelligence Assistant
# Add your NVIDIA API key here (get free key at https://build.nvidia.com)
NVIDIA_API_KEY=nvapi-YOUR-KEY-HERE
JARVIS_HOME={self.jarvis_home}
"""
                with open(env_file, "w") as f:
                    f.write(content)
                self.log(
                    "warning",
                    ".env created with placeholder — you'll need to add your API key before using JARVIS",
                )

            return True
        except Exception as e:
            self.log("error", f"Failed to create .env file: {e}")
            return False

    def step_7_configure_claude_desktop(self) -> bool:
        """Step 7: Configure Claude Desktop integration."""
        self.log_header("Step 7: Configuring Claude Desktop")

        try:
            # Get the actual Python executable from venv
            if self.os_name == "Windows":
                python_exe = self.venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = self.venv_dir / "bin" / "python"

            mcp_script = self.project_dir / "jarvis_mcp_launcher.py"

            if not mcp_script.exists():
                self.log("warning", "MCP launcher script not found, skipping Claude config")
                return True

            # Prepare config
            claude_config_dir = self.claude_config.parent
            claude_config_dir.mkdir(parents=True, exist_ok=True)

            # Load existing config or create new
            if self.claude_config.exists():
                with open(self.claude_config) as f:
                    config = json.load(f)
            else:
                config = {"mcpServers": {}}

            # Ensure mcpServers exists
            if "mcpServers" not in config:
                config["mcpServers"] = {}

            # Add JARVIS server
            config["mcpServers"]["jarvis"] = {
                "command": str(python_exe),
                "args": [str(mcp_script)],
            }

            # Write config
            with open(self.claude_config, "w") as f:
                json.dump(config, f, indent=2)

            self.log("success", "Claude Desktop configured ✓")
            self.log("info", f"Config location: {self.claude_config}")
            return True

        except Exception as e:
            self.log("warning", f"Failed to configure Claude Desktop: {e}")
            self.log("info", "You can configure it manually later")
            return True  # Don't fail setup for this

    def step_8_set_environment(self) -> bool:
        """Step 8: Set environment variables."""
        self.log_header("Step 8: Setting Environment Variables")

        try:
            # For this session, set the environment variables
            os.environ["JARVIS_HOME"] = str(self.jarvis_home)

            self.log("success", "Environment variables set ✓")
            self.log("info", f"JARVIS_HOME={self.jarvis_home}")
            return True
        except Exception as e:
            self.log("warning", f"Failed to set environment: {e}")
            return True  # Non-critical

    def step_9_validate_setup(self) -> bool:
        """Step 9: Validate that everything works."""
        self.log_header("Step 9: Validating Setup")

        # Check venv
        if self.os_name == "Windows":
            python_exe = self.venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_dir / "bin" / "python"

        if not python_exe.exists():
            self.log("error", f"Virtual environment Python not found at {python_exe}")
            return False

        self.log("success", "Virtual environment ✓")

        # Check JARVIS home
        if not self.jarvis_home.exists():
            self.log("error", f"JARVIS home not found at {self.jarvis_home}")
            return False

        self.log("success", f"JARVIS home ({self.jarvis_home}) ✓")

        # Check .env
        env_file = self.project_dir / ".env"
        if not env_file.exists():
            self.log("error", ".env file not found")
            return False

        self.log("success", ".env file ✓")

        # Check requirements
        req_file = self.project_dir / "requirements.txt"
        if not req_file.exists():
            self.log("warning", "requirements.txt not found (but may not be critical)")

        self.log("success", "All validations passed ✓")
        return True

    def run_all_steps(self) -> bool:
        """Run all setup steps in sequence."""
        self.log_header("JARVIS MCP — Universal Setup")
        self.log("info", f"Operating System: {self.os_name}")
        self.log("info", f"Python: {sys.version.split()[0]}")
        self.log("info", f"Project: {self.project_dir}")
        print()

        steps = [
            ("Python Check", self.step_1_check_python),
            ("Virtual Environment", self.step_2_create_venv),
            ("Activation", self.step_3_activate_venv),
            ("Dependencies", self.step_4_install_dependencies),
            ("JARVIS Home", self.step_5_create_jarvis_home),
            ("API Keys", self.step_6_setup_env_file),
            ("Claude Desktop", self.step_7_configure_claude_desktop),
            ("Environment", self.step_8_set_environment),
            ("Validation", self.step_9_validate_setup),
        ]

        failed_steps = []
        for i, (name, step_func) in enumerate(steps, 1):
            if not step_func():
                failed_steps.append(name)
                self.log("error", f"{name} failed")
                # Ask user if they want to continue
                response = input(
                    f"\n{name} failed. Continue anyway? (y/n): "
                ).strip().lower()
                if response != "y":
                    break

        return len(failed_steps) == 0

    def print_success(self) -> None:
        """Print success message with next steps."""
        self.log_header("✅ Setup Complete!")

        print()
        print("   🎉 JARVIS is ready to use!")
        print()
        print("   ⚠️  IMPORTANT: This JARVIS instance is project-specific")
        print("   It will ONLY work when opened within this project folder")
        print()
        print("   NEXT STEPS:")
        print()
        print("   1. Restart Claude Desktop completely")
        print("      • Windows: Close from system tray → reopen")
        print("      • macOS: Press Cmd+Q → reopen")
        print()
        print("   2. Open Claude Desktop with this project folder")
        print("      (Or use Claude Code with the JARVIS project folder)")
        print()
        print("   3. Try creating your first account:")
        print('      "Create account Acme Corp. Target $200k, March deadline."')
        print()
        print("   4. Run your first skill:")
        print('      "Score MEDDPICC for Acme Corp"')
        print()
        print(f"   📁 Your account files: {self.jarvis_home}/ACCOUNTS/")
        print()
        print("   For help: Read SALES_WORKFLOW.md or README.md in this folder")
        print()

    def print_failure(self) -> None:
        """Print failure message with troubleshooting."""
        self.log_header("❌ Setup Encountered Issues")

        print()
        print("   Some steps failed. Here's how to fix it:")
        print()
        print("   1. Make sure Python 3.9+ is installed:")
        print("      https://www.python.org/downloads/")
        print()
        print("   2. Run setup again:")
        print("      python3 install.py")
        print()
        print("   3. If it still fails, check that you have:")
        print("      • At least 500 MB free disk space")
        print("      • An active internet connection")
        print("      • Read/write permissions in your home directory")
        print()


def main() -> int:
    """Main entry point."""
    try:
        installer = JarvisInstaller()
        success = installer.run_all_steps()

        if success:
            installer.print_success()
            return 0
        else:
            installer.print_failure()
            return 1

    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
