#!/usr/bin/env python3
"""
Universal JARVIS Test Suite
Run this to verify all components work correctly
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test all module imports"""
    print("🧪 Testing Imports...")
    
    try:
        from jarvis.autodetect import UniversalWorkspaceDetector, create_platform_safe_config
        print("  ✓ autodetect module")
    except Exception as e:
        print(f"  ✗ autodetect: {e}")
        return False
    
    try:
        from jarvis.account_resolver import SmartAccountResolver, AccountMatch
        print("  ✓ account_resolver module")
    except Exception as e:
        print(f"  ✗ account_resolver: {e}")
        return False
    
    try:
        from jarvis.universal_bridge import RealtimeBridge, ConversationContext
        print("  ✓ universal_bridge module")
    except Exception as e:
        print(f"  ✗ universal_bridge: {e}")
        return False
    
    return True

def test_workspace_detection():
    """Test universal workspace detection"""
    print("\n🎯 Testing Workspace Detection...")
    
    try:
        from jarvis.autodetect import UniversalWorkspaceDetector
        
        detector = UniversalWorkspaceDetector()
        context = detector.get_workspace_context()
        
        print(f"  Platform: {context.platform_name}")
        print(f"  Workspace: {context.root}")
        print(f"  JARVIS Root: {context.javis_root}")
        print(f"  Accounts Dir: {context.accounts_dir}")
        print(f"  Accounts Found: {len(context.accounts_found)}")
        
        assert context.root is not None
        assert context.platform_name in ['macos', 'linux', 'windows', 'wsl', 'unknown']
        
        print("  ✓ Workspace detection works")
        return True
    except Exception as e:
        print(f"  ✗ Workspace detection failed: {e}")
        traceback.print_exc()
        return False

def test_account_resolver():
    """Test account resolver functionality"""
    print("\n🔍 Testing Account Resolver...")
    
    try:
        from jarvis.account_resolver import SmartAccountResolver
        
        resolver = SmartAccountResolver()
        accounts = resolver.load_accounts()
        
        print(f"  Loaded {len(accounts)} accounts")
        
        # Test detection
        test_texts = [
            "Meeting with Microsoft about Teams",
            "Email from Apple security team",
            "Discussion with Google Cloud"
        ]
        
        for text in test_texts:
            result = resolver.detect_account(text)
            if result:
                print(f"  ✓ '{text[:30]}...' → {result.account_name} ({result.confidence:.2f})")
            else:
                print(f"  ○ '{text[:30]}...' → No match")
        
        print("  ✓ Account resolver works")
        return True
    except Exception as e:
        print(f"  ✗ Account resolver failed: {e}")
        traceback.print_exc()
        return False

def test_universal_bridge():
    """Test universal bridge initialization"""
    print("\n🌉 Testing Universal Bridge...")
    
    try:
        from jarvis.universal_bridge import RealtimeBridge, ConversationContext
        
        bridge = RealtimeBridge()
        print(f"  Bridge workspace: {bridge.workspace_root}")
        print(f"  Accounts dir: {bridge.context.accounts_dir}")
        print(f"  Universal sources: {list(bridge.universal_sources.keys())}")
        
        # Test conversation processing
        test_context = ConversationContext(
            source="test",
            text="Meeting with Microsoft tomorrow at 2pm",
            timestamp=0,
            workspace=str(bridge.workspace_root)
        )
        
        result = bridge.process_conversation(test_context)
        print(f"  Processed: account={result.get('account_detected')}, skills={len(result.get('actions_executed', []))}")
        
        print("  ✓ Universal bridge works")
        return True
    except Exception as e:
        print(f"  ✗ Universal bridge failed: {e}")
        traceback.print_exc()
        return False

def test_config_generation():
    """Test configuration generation"""
    print("\n⚙️ Testing Config Generation...")
    
    try:
        from jarvis.autodetect import create_platform_safe_config
        
        config = create_platform_safe_config()
        
        print(f"  Version: {config.get('version', 'unknown')}")
        print(f"  Platform: {config['platform']['name']}")
        print(f"  Universal: {config['features']['universal_workspace']}")
        
        assert config['platform']['platform_safe'] == True
        assert 'workspace_root' in config['paths']
        
        print("  ✓ Config generation works")
        return True
    except Exception as e:
        print(f"  ✗ Config generation failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run complete test suite"""
    print("🚀 JARVIS v3 Universal Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_workspace_detection,
        test_account_resolver,
        test_universal_bridge,
        test_config_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  Test crash: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed! JARVIS v3 is ready.")
        return True
    else:
        print("❌ Some tests failed. Check logs.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)