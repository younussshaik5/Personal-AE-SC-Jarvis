"""Simple integration test for Skill Context Enricher"""

import logging
from pathlib import Path
import tempfile
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_skill_context_enrichment():
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
        }
        (acme_path / "company_profile.json").write_text(json.dumps(company_profile, indent=2))

        # Create deal stage
        deal_stage = {
            "deals": {
                "deal_001": {"name": "Migration", "stage": "negotiate", "value": 2500000},
                "deal_002": {"name": "Analytics", "stage": "discovery", "value": 1500000}
            }
        }
        (acme_path / "deal_stage.json").write_text(json.dumps(deal_stage, indent=2))

        logger.info("\n=== TEST 1: Load Account Context ===")
        from jarvis_mcp.skill_context_enricher import SkillContextEnricher

        enricher = SkillContextEnricher(str(test_accounts_root))
        context = enricher.get_enriched_context("AcmeCorp")

        assert context is not None, "Context should not be None"
        assert context['account_name'] == "AcmeCorp", "Account name should match"
        logger.info(f"✓ Context loaded with {len(context)} keys")
        logger.info(f"  Keys: {', '.join(context.keys())}")

        logger.info("\n=== TEST 2: Verify Company Profile ===")
        assert context['company_profile'], "Company profile should exist"
        logger.info(f"✓ Company profile loaded")

        logger.info("\n=== TEST 3: Verify Deal Pipeline ===")
        assert context['deal_pipeline'], "Deal pipeline should exist"
        deals = context['deal_pipeline']
        assert len(deals) >= 2, "Should have multiple deals"
        logger.info(f"✓ Deal pipeline loaded: {len(deals)} deals")

        logger.info("\n=== TEST 4: Get Skill-Specific Context ===")
        skill_context = enricher.get_context_for_skill("AcmeCorp", "proposal")
        assert skill_context['_skill_focus']['type'] == "proposal"
        logger.info(f"✓ Skill context loaded for 'proposal' skill")

        logger.info("\n=== TEST 5: Get AI-Ready Summary ===")
        summary = enricher.get_summary_for_ai_context("AcmeCorp")
        assert summary is not None
        assert len(summary) > 0
        logger.info(f"✓ AI-ready summary generated ({len(summary)} chars)")

        logger.info("\n=== TEST 6: Cache Statistics ===")
        stats = enricher.get_cache_stats()
        assert "AcmeCorp" in stats['cached_accounts']
        logger.info(f"✓ Cache stats: {stats['cache_size']} accounts cached")

        logger.info("\n=== TEST 7: Cache Invalidation ===")
        enricher.invalidate_cache("AcmeCorp")
        stats_after = enricher.get_cache_stats()
        assert len(stats_after['cached_accounts']) == 0
        logger.info(f"✓ Cache cleared successfully")

        logger.info("\n" + "="*60)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("="*60)


if __name__ == "__main__":
    test_skill_context_enrichment()
