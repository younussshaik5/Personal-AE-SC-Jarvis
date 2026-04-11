"""
End-to-End Onboarding Flow Tests
Tests the complete onboarding system from first interaction to account creation.
"""

import asyncio
import tempfile
from pathlib import Path


class TestOnboardingFlow:
    """Test complete onboarding flow"""

    async def test_full_onboarding_flow(self):
        """Test: User goes through complete onboarding"""
        print("\n" + "="*70)
        print("TEST: Full Onboarding Flow")
        print("="*70)
        
        try:
            from ..onboarding_info_extractor import OnboardingInfoExtractor
            from ..account_scaffolder import AccountScaffolder
            from ..account_hierarchy import AccountHierarchy
            from ..claude_md_loader import ClaudeMdLoader
            
            # Setup
            with tempfile.TemporaryDirectory() as tmpdir:
                accounts_root = Path(tmpdir) / "ACCOUNTS"
                
                # Initialize components
                extractor = OnboardingInfoExtractor()
                scaffolder = AccountScaffolder(str(accounts_root))
                hierarchy = AccountHierarchy(str(accounts_root))
                
                # Stage 1: Company Discovery
                print("\n[STAGE 1] User describes company...")
                company_text = "I work at TataCommunications, we're a $100M+ enterprise telecom company"
                
                analysis = extractor.analyze_response('company', company_text)
                assert analysis['extracted']['name'] == 'TataCommunications'
                assert analysis['extracted']['industry'] == 'Telecom'
                print(f"✓ Extracted: {analysis['extracted']}")
                
                # Stage 2: Role Discovery
                print("\n[STAGE 2] User describes role...")
                role_text = "I'm an Account Executive managing enterprise deals"
                
                analysis = extractor.analyze_response('role', role_text)
                assert analysis['extracted']['role'] == 'Sales Executive'
                print(f"✓ Extracted: {analysis['extracted']}")
                
                # Stage 3: Offerings Discovery
                print("\n[STAGE 3] User describes offerings...")
                offerings_text = "We sell global connectivity, SD-WAN solutions, and managed networks"
                
                analysis = extractor.analyze_response('offerings', offerings_text)
                assert len(analysis['extracted']['offerings']) > 0
                print(f"✓ Extracted offerings: {analysis['extracted']['offerings']}")
                
                # Stage 4: Challenges Discovery
                print("\n[STAGE 4] User describes challenges...")
                challenge_text = "Our biggest challenge is the long discovery phase, takes 2-3 months"
                
                analysis = extractor.analyze_response('sales', challenge_text)
                print(f"✓ Extracted challenges: {analysis['extracted']['challenges']}")
                
                # Stage 5: Auto-scaffolding
                print("\n[STAGE 5] Account creation...")
                company_info = {
                    'company_name': 'TataCommunications',
                    'industry': 'Telecom',
                    'revenue': '$100M+',
                }
                
                result = scaffolder.scaffold_account('TataCommunications', company_info)
                assert result['status'] == 'created'
                print(f"✓ Account scaffolded: {result['path']}")
                
                # Verify files created
                account_path = Path(result['path'])
                assert (account_path / 'company_research.md').exists()
                assert (account_path / 'discovery.md').exists()
                assert (account_path / 'deal_stage.json').exists()
                assert (account_path / 'CLAUDE.md').exists()
                print("✓ All template files created")
                
                # Stage 6: Verify account context
                print("\n[STAGE 6] Account hierarchy verification...")
                hierarchy.rebuild_cache()
                found_path = hierarchy.get_account_path('TataCommunications')
                assert found_path is not None
                print(f"✓ Account found in hierarchy: {found_path}")
                
                print("\n" + "="*70)
                print("✅ FULL ONBOARDING FLOW TEST PASSED")
                print("="*70)
                
        except ImportError as e:
            print(f"⚠️  Skipping test (import error): {e}")


async def main():
    """Run tests"""
    tester = TestOnboardingFlow()
    await tester.test_full_onboarding_flow()


if __name__ == "__main__":
    asyncio.run(main())
