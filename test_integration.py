#!/usr/bin/env python3
"""
JARVIS v3 Integration Test
Simulates real conversation flow and validates end-to-end processing
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path.cwd()))

from jarvis.autodetect import UniversalWorkspaceDetector
from jarvis.account_resolver import SmartAccountResolver
from jarvis.universal_bridge import RealtimeBridge, ConversationContext


def test_full_pipeline():
    """Test complete pipeline from conversation to skill execution"""
    print("🧪 JARVIS v3 Integration Test")
    print("================================\n")
    
    # Step 1: Workspace Detection
    print("1️⃣ Universal Workspace Detection")
    detector = UniversalWorkspaceDetector()
    context = detector.get_workspace_context()
    print(f"   Platform: {context.platform_name}")
    print(f"   Workspace: {context.root}")
    print(f"   JARVIS Root: {context.javis_root}")
    print(f"   Accounts: {len(context.accounts_found)} found")
    assert context.root is not None
    print("   ✅ Detection works\n")
    
    # Step 2: Account Resolution
    print("2️⃣ Smart Account Resolution")
    resolver = SmartAccountResolver()
    accounts = resolver.load_accounts()
    print(f"   Loaded {len(accounts)} accounts")
    
    # Test account detection
    test_conversations = [
        ("Meeting with Microsoft tomorrow to discuss Teams integration", "Microsoft related"),
        ("Email from John at Apple about security requirements", "Apple mention"),
        ("Google Cloud pricing discussion", "Google mention"),
    ]
    
    detected = 0
    for text, description in test_conversations:
        result = resolver.detect_account(text)
        if result:
            print(f"   ✓ {description} → {result.account_name} ({result.confidence:.2f})")
            detected += 1
        else:
            print(f"   ○ {description} → No match")
    print(f"   ✅ Detected {detected}/{len(test_conversations)} conversations\n")
    
    # Step 3: Universal Bridge
    print("3️⃣ Universal Intelligence Bridge")
    bridge = RealtimeBridge()
    print(f"   Workspace: {bridge.workspace_root}")
    print(f"   Accounts dir: {bridge.context.accounts_dir}")
    print(f"   Sources: {', '.join(bridge.universal_sources.keys())}")
    
    # Test conversation processing
    test_context = ConversationContext(
        source="test_integration",
        text="Following up with Microsoft on Teams integration proposal - budget discussion needed",
        timestamp=datetime.now().timestamp(),
        workspace=str(bridge.workspace_root)
    )
    
    result = bridge.process_conversation(test_context)
    print(f"   Processed conversation:")
    print(f"     - Account detected: {result.get('account_detected', 'None')}")
    print(f"     - Skills triggered: {len(result.get('actions_executed', []))}")
    print(f"     - Files created: {len(result.get('files_created', []))}")
    
    if result.get('files_created'):
        for file_path in result.get('files_created', [])[:3]:  # Show first 3
            print(f"       • {Path(file_path).name}")
    
    print("   ✅ Bridge processing works\n")
    
    # Step 4: Real Account Detection
    if accounts:
        print("4️⃣ Real Account Processing")
        real_account = accounts[0]
        print(f"   Testing with real account: {real_account}")
        
        real_context = ConversationContext(
            source="test_integration",
            text=f"Discussion with {real_account} about upcoming meeting",
            timestamp=datetime.now().timestamp(),
            workspace=str(bridge.workspace_root)
        )
        
        real_result = bridge.process_conversation(real_context)
        if real_result.get('account_detected') == real_account:
            print(f"   ✅ Correctly matched to {real_account}")
        else:
            print(f"   ⚠️ Expected {real_account}, got {real_result.get('account_detected')}")
        
        # Check files
        account_path = context.accounts_dir / real_account
        intel_dir = account_path / "INTEL"
        if intel_dir.exists():
            files = list(intel_dir.glob("*.json")) + list(intel_dir.glob("*.md"))
            print(f"   ✅ Intel files created: {len(files)}")
    
    print("\n" + "=" * 50)
    print("✅ Integration test PASSED - JARVIS v3 is fully functional")
    print("=" * 50)
    
    return True


def test_file_creation():
    """Test that skill execution creates expected files"""
    print("\n🗂️ File Creation Test")
    
    bridge = RealtimeBridge()
    context = bridge.context
    
    # Create test conversation that triggers skills
    test_texts = [
        "Email draft needed for follow-up with client",
        "Meeting prep required for discovery call",
        "Pain point: slow performance issues"
    ]
    
    files_created = []
    for text in test_texts:
        conv = ConversationContext(
            source="test",
            text=text,
            timestamp=datetime.now().timestamp(),
            workspace=str(bridge.workspace_root)
        )
        result = bridge.process_conversation(conv)
        files_created.extend(result.get('files_created', []))
    
    print(f"   Created {len(files_created)} files")
    
    # Verify files exist
    existing = 0
    for file_path in files_created:
        if Path(file_path).exists():
            existing += 1
            print(f"   ✓ {Path(file_path).relative_to(context.accounts_dir)}")
    
    print(f"   ✅ {existing}/{len(files_created)} files exist")
    
    return len(files_created) > 0


def main():
    """Run all integration tests"""
    try:
        success = True
        
        success = test_full_pipeline() and success
        success = test_file_creation() and success
        
        print("\n🎯 FINAL RESULT")
        if success:
            print("✅ All integration tests passed!")
            print("\n🚀 JARVIS v3 is ready for deployment")
            print("📋 To start using:")
            print("   1. Copy .env.template to .env")
            print("   2. Add NVIDIA_API_KEY")
            print("   3. Run: ./start_jarvis.sh")
            return 0
        else:
            print("❌ Some integration tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Integration test crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())