#!/usr/bin/env python3
"""
JARVIS System Verification - Checks all interconnections and readiness.
"""

import sys
import importlib
from pathlib import Path

def verify_imports():
    """Verify all jarvis modules can be imported."""
    print("="*60)
    print("VERIFYING JARVIS IMPORTS")
    print("="*60)
    
    modules = [
        'jarvis',
        'jarvis.core.orchestrator',
        'jarvis.utils.logger',
        'jarvis.utils.event_bus',
        'jarvis.utils.config',
        'jarvis.observers.file_system',
        'jarvis.observers.conversations',
        'jarvis.learners.pattern_recognition',
        'jarvis.persona.persona_manager',
        'jarvis.safety.guard',
        'jarvis.mcp.context_engine',
        'jarvis.archive.archiver',
        'jarvis.scanner',
        'jarvis.updaters',
        'jarvis.cli',
        'jarvis.api'
    ]
    
    failed = []
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"✓ {mod}")
        except Exception as e:
            print(f"✗ {mod}: {e}")
            failed.append(mod)
    
    if failed:
        print(f"\n❌ {len(failed)} modules failed to import")
        return False
    else:
        print(f"\n✅ All {len(modules)} modules import successfully")
        return True


def verify_file_structure():
    """Verify directory structure and key files."""
    print("\n" + "="*60)
    print("VERIFYING FILE STRUCTURE")
    print("="*60)
    
    base = Path.cwd() / 'jarvis'
    required = [
        base / '__init__.py',
        base / 'core' / '__init__.py',
        base / 'utils' / '__init__.py',
        base / 'observers' / '__init__.py',
        base / 'learners' / '__init__.py',
        base / 'persona' / '__init__.py',
        base / 'safety' / '__init__.py',
        base / 'mcp' / '__init__.py',
        base / 'archive' / '__init__.py',
        base / 'config' / 'jarvis.yaml',
        base / 'data' / 'personas',
        base / 'data' / 'patterns',
        base / 'data' / 'archives',
        base / 'logs',
        base / 'scripts' / 'setup.py'
    ]
    
    missing = []
    for f in required:
        if not f.exists():
            print(f"✗ Missing: {f}")
            missing.append(f)
        else:
            print(f"✓ {f.relative_to(base)}")
    
    if missing:
        print(f"\n❌ {len(missing)} required files/directories missing")
        return False
    else:
        print(f"\n✅ All required files present ({len(required)})")
        return True


def verify_config():
    """Verify configuration files."""
    print("\n" + "="*60)
    print("VERIFYING CONFIGURATION")
    print("="*60)
    
    config_files = [
        Path.cwd() / 'config' / 'jarvis.yaml',
        Path.cwd() / 'OPENCODE_FIREUP_SKILL.md',
        Path.cwd() / 'persona' / 'account_executive' / 'ACCOUNT_EXECUTIVE_SKILL.md',
        Path.cwd() / 'persona' / 'solution_consultant' / 'SOLUTION_CONSULTANT_SKILL.md'
    ]
    
    for f in config_files:
        if f.exists():
            print(f"✓ {f.name}")
        else:
            print(f"✗ Missing: {f}")
    
    return True


def verify_mcp_integration():
    """Verify MCP observer is built and configured."""
    print("\n" + "="*60)
    print("VERIFYING MCP INTEGRATION")
    print("="*60)
    
    mcp_binary = Path.cwd() / 'mcp-opencode-observer' / 'dist' / 'index.js'
    config_paths = [
        Path.home() / '.config' / 'opencode' / 'opencode.jsonc',
        Path.home() / '.local' / 'share' / 'opencode' / 'opencode.json'
    ]
    
    if mcp_binary.exists():
        size = mcp_binary.stat().st_size
        print(f"✓ MCP Observer binary: {mcp_binary} ({size:,} bytes)")
    else:
        print(f"✗ MCP Observer binary missing - run: cd mcp-opencode-observer && npm run build")
        return False
    
    config_found = False
    for p in config_paths:
        if p.exists():
            try:
                import json
                with open(p) as f:
                    cfg = json.load(f)
                if 'jarvis' in cfg.get('mcp', {}):
                    print(f"✓ OpenCode MCP config includes JARVIS")
                    config_found = True
                else:
                    print(f"⚠ OpenCode config exists but JARVIS not configured (run setup.py)")
            except:
                pass
    
    if not config_found:
        print(f"⚠ Run: python jarvis/scripts/setup.py to configure OpenCode integration")
    
    return mcp_binary.exists()


def main():
    print("\n" + " " * 20 + "JARVIS SYSTEM VERIFICATION")
    print("="*60 + "\n")
    
    results = []
    results.append(("Imports", verify_imports()))
    results.append(("File Structure", verify_file_structure()))
    results.append(("Configuration", verify_config()))
    results.append(("MCP Integration", verify_mcp_integration()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n✅ JARVIS system verified and ready!")
        print("\nNext steps:")
        print("  1. Run: python jarvis/scripts/setup.py")
        print("  2. Restart OpenCode")
        print("  3. Test: jarvis status")
    else:
        print("\n⚠ Some checks failed. Review the issues above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())