#!/usr/bin/env python3
"""
Quick API Key Checker
Run this to verify NVIDIA API key is properly configured.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path.cwd() / '.env'
load_dotenv(env_path)

print("=" * 70)
print("API KEY CONFIGURATION CHECK")
print("=" * 70)

# Check .env existence
if not env_path.exists():
    print(f"\n❌ .env file not found at {env_path}")
    print("   Run: bash setup.sh")
    sys.exit(1)

print(f"\n✅ .env file found")

# Check NVIDIA_API_KEY
nvidia_key = os.getenv('NVIDIA_API_KEY')

if not nvidia_key:
    print(f"\n❌ NVIDIA_API_KEY is empty or not set")
    print(f"   Action: Edit .env and add your NVIDIA API key")
    print(f"   Get free key: https://build.nvidia.com/")
    sys.exit(1)

if 'your_nvidia_api_key_here' in nvidia_key.lower() or 'placeholder' in nvidia_key.lower():
    print(f"\n❌ NVIDIA_API_KEY is still a placeholder")
    print(f"   Current value: {nvidia_key[:30]}...")
    print(f"   Action: Replace with your actual API key from https://build.nvidia.com/")
    sys.exit(1)

if not nvidia_key.startswith('nvapi-'):
    print(f"\n⚠️  NVIDIA_API_KEY doesn't look right")
    print(f"   Should start with 'nvapi-'")
    print(f"   Current: {nvidia_key[:20]}...")
    sys.exit(1)

print(f"\n✅ NVIDIA_API_KEY is configured")
print(f"   Key (truncated): {nvidia_key[:20]}...{nvidia_key[-15:]}")
print(f"   Length: {len(nvidia_key)} characters")

# Check for multiple API keys (recommended to avoid rate limits)
print("\n📋 Checking for multiple API keys...")
additional_keys = 0
for i in range(2, 10):
    key_name = f"NVIDIA_API_KEY_{i}"
    key_value = os.getenv(key_name)
    if key_value and key_value.startswith('nvapi-'):
        additional_keys += 1
        print(f"   ✅ Found {key_name}")

if additional_keys == 0:
    print(f"   ⚠️  Only 1 API key configured")
    print(f"   JARVIS runs 9 parallel LLM calls (MEDDPICC scoring)")
    print(f"   Recommendation: Add 3-6 keys to .env to avoid rate limits")
    print(f"\n   How to add more keys:")
    print(f"   1. Edit .env file")
    print(f"   2. Add: NVIDIA_API_KEY_2=nvapi-YOUR-SECOND-KEY")
    print(f"   3. Add: NVIDIA_API_KEY_3=nvapi-YOUR-THIRD-KEY")
    print(f"   4. Save and restart Claude Desktop")
else:
    print(f"\n✅ Multiple API keys configured ({1 + additional_keys} total)")
    print(f"   JARVIS will distribute requests across keys automatically")

# Try to initialize LLM Manager
try:
    sys.path.insert(0, str(Path.cwd()))
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.llm.llm_manager import LLMManager

    config = ConfigManager()
    llm = LLMManager(config)

    print(f"\n✅ LLM Manager initialized successfully")
    print(f"   JARVIS is ready to use!")

except Exception as e:
    print(f"\n⚠️  LLM Manager test failed: {e}")
    print(f"   The key might be invalid or NVIDIA service is down")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL CHECKS PASSED - READY TO USE")
print("=" * 70)
print("\nNext: Restart Claude Desktop")
print("      • macOS: Press Cmd+Q to quit, then reopen")
print("      • Windows: Right-click Claude in taskbar → Quit → Reopen")
print("      • Linux: Close and reopen Claude Desktop")
print("\n      JARVIS tools will be available when you ask for skills")
