#!/usr/bin/env python3
"""
JARVIS v3 Pre-Deployment Validator
Comprehensive checks before committing to git
"""

import sys
import os
from pathlib import Path

def validate_all():
    """Run all validation checks"""
    errors = []
    warnings = []
    
    print("🔍 JARVIS v3 Pre-Deployment Validation")
    print("=" * 50)
    
    # 1. Check for hardcoded paths in Python files
    print("\n1️⃣ Checking for hardcoded absolute paths...")
    py_files = list(Path('jarvis').rglob('*.py'))
    hardcoded = []
    for py_file in py_files:
        content = py_file.read_text()
        if '/Users/' in content or 'C:\\' in content or '/home/' in content:
            hardcoded.append(py_file)
    
    if hardcoded:
        print(f"   ⚠️ Found {len(hardcoded)} files with possible hardcoded paths:")
        for f in hardcoded[:5]:
            print(f"     - {f}")
        warnings.append("Hardcoded paths found - review needed")
    else:
        print("   ✅ No obvious absolute paths detected")
    
    # 2. Check imports are correct (relative within package)
    print("\n2️⃣ Validating module imports...")
    for py_file in py_files:
        content = py_file.read_text()
        lines = content.splitlines()
        for line in lines[:30]:  # Check imports
            if line.startswith('from jarvis.') and '..' in line:
                errors.append(f"Bad relative import in {py_file}: {line}")
    
    if errors:
        print(f"   ❌ Import errors found")
    else:
        print("   ✅ All imports use correct package structure")
    
    # 3. Check config files are portable
    print("\n3️⃣ Checking configuration portability...")
    config_files = list(Path('config').rglob('*.json')) + list(Path('config').rglob('*.yaml'))
    for cfg in config_files:
        content = cfg.read_text()
        if 'home' in content.lower() and '/Users/' in content:
            warnings.append(f"Config may contain user-specific paths: {cfg}")
    
    if warnings:
        print(f"   ⚠️ Config warnings: {len(warnings)}")
    else:
        print("   ✅ Configs appear portable")
    
    # 4. Verify git-ignored files
    print("\n4️⃣ Verifying .gitignore coverage...")
    gitignore = Path('.gitignore').read_text() if Path('.gitignore').exists() else ''
    critical_patterns = ['.env', '__pycache__', 'logs/', 'node_modules/', '.DS_Store']
    missing = [p for p in critical_patterns if p not in gitignore]
    
    if missing:
        warnings.append(f"Missing gitignore patterns: {missing}")
    else:
        print("   ✅ .gitignore covers critical patterns")
    
    # 5. Check for required files
    print("\n5️⃣ Checking required files exist...")
    required_files = [
        'jarvis/autodetect.py',
        'jarvis/account_resolver.py',
        'jarvis/universal_bridge.py',
        'scripts/setup_jarvis_universal.py',
        'start_jarvis.sh',
        'requirements-universal.txt',
        'docker-compose.yml',
        'README.md',
        'CHANGES_JARVIS_v3.md'
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        errors.append(f"Missing required files: {missing_files}")
    else:
        print("   ✅ All required files present")
    
    # 6. Validate entry points
    print("\n6️⃣ Checking executable entry points...")
    execs = ['start_jarvis.sh', 'scripts/setup_jarvis_universal.py']
    for exe in execs:
        if Path(exe).exists():
            mode = Path(exe).stat().st_mode
            if mode & 0o111:
                print(f"   ✓ {exe} is executable")
            else:
                warnings.append(f"{exe} is not executable")
    
    # 7. Quick import test
    print("\n7️⃣ Testing Python imports...")
    try:
        import jarvis.autodetect
        import jarvis.account_resolver
        import jarvis.universal_bridge
        print("   ✅ All modules import successfully")
    except Exception as e:
        errors.append(f"Import test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if errors:
        print("\n❌ DEPLOYMENT BLOCKED - Fix errors before pushing")
        for err in errors:
            print(f"  • {err}")
        return False
    elif warnings:
        print("\n⚠️ DEPLOYMENT WITH CAUTION - Address warnings")
        for warn in warnings:
            print(f"  • {warn}")
        return True
    else:
        print("\n✅ CLEAN FOR DEPLOYMENT - Ready to push to git")
        return True

if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)