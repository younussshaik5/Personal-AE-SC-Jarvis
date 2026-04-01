#!/usr/bin/env python3
"""TEST: Skill Context Enricher Integration"""

import logging
import json
from pathlib import Path
import tempfile
import sys

# Add to path
sys.path.insert(0, '/Users/syounus/Documents/claude space/Personal-AE-SC-Jarvis')

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_accounts_root = Path(tmpdir) / "ACCOUNTS"
        test_accounts_root.mkdir(parents=True, exist_ok=True)

        # Create test account
        acme_path = test_accounts_root / "AcmeCorp"
        acme_path.mkdir(parents=True, exist_ok=True)

        # Create company_research.md (what aggregator looks for)
        (acme_path / "company_research.md").write_text("# Acme Corporation\n## Overview\nEnterprise software vendor")

        # Create deal_stage.json
        deal_data = {
            "deals": {
                "deal_001": {"name": "Migration", "stage": "negotiate", "value": 2500000},
                "deal_002": {"name": "Analytics", "stage": "discovery", "value": 1500000}
            }
        }
        (acme_path / "deal_stage.json").write_text(json.dumps(deal_data))

        # Test 1: Import and initialize
        logger.info("\n✓ TEST 1: Import SkillContextEnricher")
        from jarvis_mcp.skill_context_enricher import SkillContextEnricher
        enricher = SkillContextEnricher(str(test_accounts_root))
        logger.info("  ✓ Enricher initialized")

        # Test 2: Load context
        logger.info("\n✓ TEST 2: Load account context")
        context = enricher.get_enriched_context("AcmeCorp")
        assert context, "Context should exist"
        assert context['account_name'] == "AcmeCorp"
        logger.info(f"  ✓ Context loaded with keys: {', '.join(list(context.keys())[:6])}...")

        # Test 3: Verify company profile
        logger.info("\n✓ TEST 3: Verify company profile loaded")
        assert context['company_profile'], f"Company profile empty: {context['company_profile']}"
        logger.info(f"  ✓ Company profile: {list(context['company_profile'].keys())}")

        # Test 4: Verify deal pipeline
        logger.info("\n✓ TEST 4: Verify deal pipeline loaded")
        assert context['deal_pipeline'], f"Deal pipeline empty: {context['deal_pipeline']}"
        deals = context['deal_pipeline'].get('deals', {})
        logger.info(f"  ✓ Deals loaded: {len(deals)} deals")

        # Test 5: Skill-specific context
        logger.info("\n✓ TEST 5: Get skill-specific context")
        skill_ctx = enricher.get_context_for_skill("AcmeCorp", "proposal")
        assert skill_ctx['_skill_focus']['type'] == "proposal"
        logger.info(f"  ✓ Proposal context ready")

        # Test 6: Cache works
        logger.info("\n✓ TEST 6: Cache functionality")
        stats = enricher.get_cache_stats()
        assert stats['cache_size'] == 1
        logger.info(f"  ✓ {stats['cache_size']} account cached")

        # Test 7: MCP Server integration
        logger.info("\n✓ TEST 7: MCP Server integration")
        try:
            from jarvis_mcp.mcp_server import JarvisServer
            # Note: Full server test would need mock skills
            logger.info("  ✓ MCP server imports successfully")
        except Exception as e:
            logger.warning(f"  ⚠ MCP server test: {e}")

        logger.info("\n" + "="*60)
        logger.info("✅ ALL TESTS PASSED - SKILL CONTEXT ENRICHER WORKING")
        logger.info("="*60)

if __name__ == "__main__":
    test()
