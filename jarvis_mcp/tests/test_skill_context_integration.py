"""
Integration test: Skill Context Enricher with MCP Server
Tests end-to-end flow: Account context → Enricher → Skill execution
"""

import asyncio
import json
import logging
from pathlib import Path
import tempfile
import shutil
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Setup test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_skill_context_enrichment():
    """Test that skills receive full account context automatically"""

    # Create temporary test accounts directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_accounts_root = Path(tmpdir) / "ACCOUNTS"
        test_accounts_root.mkdir(parents=True, exist_ok=True)

        # Create test account: AcmeCorp
        acme_path = test_accounts_root / "AcmeCorp"
        acme_path.mkdir(parents=True, exist_ok=True)

        # Create company profile
        company_profile = {
            "name": "Acme Corporation",
            "industry": "Enterprise Software",
            "size": "enterprise",
            "revenue": "$500M+",
            "headquarters": "San Francisco, CA",
            "founded": 1995,
            "description": "Leading enterprise software solutions provider"
        }
        (acme_path / "company_profile.json").write_text(json.dumps(company_profile, indent=2))

        # Create deal stage
        deal_stage = {
            "deals": {
                "deal_001": {
                    "name": "Enterprise Cloud Migration",
                    "stage": "negotiate",
                    "value": 2500000,
                    "probability": 0.75,
                    "close_date": "2026-06-30"
                },
                "deal_002": {
                    "name": "Data Analytics Platform",
                    "stage": "discovery",
                    "value": 1500000,
                    "probability": 0.45,
                    "close_date": "2026-08-31"
                }
            }
        }
        (acme_path / "deal_stage.json").write_text(json.dumps(deal_stage, indent=2))

        # Create discovery notes
        discovery_notes = """
# AcmeCorp Discovery Notes

## Company Profile
- CEO: Jane Smith (jane.smith@acme.com)
- CTO: Robert Johnson (robert.johnson@acme.com)
- Procurement Lead: Maria Garcia (maria.garcia@acme.com)

## Key Challenges
1. Legacy system integration
2. Cloud migration complexity
3. Data security concerns
4. Budget constraints for Q2

## Competitive Landscape
- Main competitors: CloudTech, DataFlow Solutions
- Lost to CloudTech in RFP last quarter
- Considering multi-vendor approach

## Buying Signals
- Recent budget approval for digital transformation
- CTO visiting industry conferences
- Published RFI for cloud solutions
"""
        (acme_path / "discovery.md").write_text(discovery_notes)

        # Create sample proposal file
        proposal_path = acme_path / "proposals"
        proposal_path.mkdir(exist_ok=True)
        (proposal_path / "cloudmigration_proposal_2026.md").write_text(
            "# Cloud Migration Proposal\n\nValue: $2.5M\nTimeline: 6 months"
        )

        # Create learning history
        learning_history = {
            "interactions": [
                {"date": "2026-03-15", "type": "email", "summary": "Initial contact"},
                {"date": "2026-03-20", "type": "meeting", "summary": "Discovery call with CTO"},
                {"date": "2026-03-25", "type": "demo", "summary": "Technical demo attended by 5 people"}
            ]
        }
        (acme_path / ".learning_history.json").write_text(json.dumps(learning_history, indent=2))

        # Test 1: Load context with enricher
        logger.info("\n=== TEST 1: Load Account Context ===")
        from jarvis_mcp.skill_context_enricher import SkillContextEnricher

        enricher = SkillContextEnricher(str(test_accounts_root))
        context = enricher.get_enriched_context("AcmeCorp")

        assert context is not None, "Context should not be None"
        assert context['account_name'] == "AcmeCorp", "Account name should match"
        assert context['account_path'] is not None, "Account path should be set"
        logger.info(f"✓ Context loaded with {len(context)} keys")
        logger.info(f"  Keys: {', '.join(context.keys())}")

        # Test 2: Check company profile loaded
        logger.info("\n=== TEST 2: Verify Company Profile ===")
        assert context['company_profile'], "Company profile should exist"
        profile = context['company_profile']
        assert profile.get('name') == "Acme Corporation", "Company name should match"
        assert profile.get('revenue') == "$500M+", "Revenue should match"
        logger.info(f"✓ Company profile loaded: {profile.get('name')}")

        # Test 3: Check deal pipeline loaded
        logger.info("\n=== TEST 3: Verify Deal Pipeline ===")
        assert context['deal_pipeline'], "Deal pipeline should exist"
        deals = context['deal_pipeline']
        assert len(deals) >= 2, "Should have multiple deals"
        logger.info(f"✓ Deal pipeline loaded: {len(deals)} deals")
        for deal_id, deal in deals.items():
            logger.info(f"  - {deal.get('name', deal_id)}: ${deal.get('value', 0)}")

        # Test 4: Check relationships loaded
        logger.info("\n=== TEST 4: Verify Relationships ===")
        assert context['relationships'], "Relationships should exist"
        rels = context['relationships']
        assert len(rels) > 0, "Should have relationships extracted"
        logger.info(f"✓ Relationships loaded: {len(rels)} contacts")

        # Test 5: Get skill-specific context
        logger.info("\n=== TEST 5: Get Skill-Specific Context ===")
        skill_context = enricher.get_context_for_skill("AcmeCorp", "proposal")
        assert skill_context['_skill_focus']['type'] == "proposal", "Skill focus should be set"
        logger.info(f"✓ Skill context loaded for 'proposal' skill")
        logger.info(f"  Skill focus: {skill_context['_skill_focus']['type']}")
        logger.info(f"  Relevant data: {', '.join(skill_context['_skill_focus']['relevant_data'])}")

        # Test 6: Get AI-ready summary
        logger.info("\n=== TEST 6: Get AI-Ready Summary ===")
        summary = enricher.get_summary_for_ai_context("AcmeCorp")
        assert summary is not None, "Summary should not be None"
        assert len(summary) > 0, "Summary should have content"
        logger.info(f"✓ AI-ready summary generated ({len(summary)} chars)")

        # Test 7: Cache statistics
        logger.info("\n=== TEST 7: Cache Statistics ===")
        stats = enricher.get_cache_stats()
        assert "AcmeCorp" in stats['cached_accounts'], "AcmeCorp should be cached"
        logger.info(f"✓ Cache stats: {stats['cache_size']} accounts cached")

        # Test 8: Invalidate cache
        logger.info("\n=== TEST 8: Cache Invalidation ===")
        enricher.invalidate_cache("AcmeCorp")
        stats_after = enricher.get_cache_stats()
        assert len(stats_after['cached_accounts']) == 0, "Cache should be cleared"
        logger.info(f"✓ Cache cleared successfully")

        # Test 9: Reload from cache
        logger.info("\n=== TEST 9: Reload After Invalidation ===")
        context_reloaded = enricher.get_enriched_context("AcmeCorp")
        assert context_reloaded is not None, "Should reload context after invalidation"
        assert context_reloaded['account_name'] == "AcmeCorp"
        logger.info(f"✓ Context reloaded after cache invalidation")

        logger.info("\n" + "="*60)
        logger.info("✅ ALL INTEGRATION TESTS PASSED")
        logger.info("="*60)
        logger.info(f"\nSummary:")
        logger.info(f"  ✓ Account context loading works")
        logger.info(f"  ✓ Company profile extraction works")
        logger.info(f"  ✓ Deal pipeline loading works")
        logger.info(f"  ✓ Relationships extraction works")
        logger.info(f"  ✓ Skill-specific context works")
        logger.info(f"  ✓ AI-ready summaries work")
        logger.info(f"  ✓ Context caching works")
        logger.info(f"  ✓ Cache invalidation works")


if __name__ == "__main__":
    asyncio.run(test_skill_context_enrichment())
