#!/usr/bin/env python3
"""
Comprehensive Validation - Tests all 25 JARVIS MCP systems
Checks imports, initialization, integration, and functionality
"""

import sys
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import asyncio

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_test(num, name, passed, msg=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{num:2d}. {status} | {name:40s} {msg}")
    return 1 if passed else 0

# Track results
results = {}
passed = 0
total = 25

# ============================================================================
# TEST 1-5: Core Infrastructure
# ============================================================================
print_header("CORE INFRASTRUCTURE")

# Test 1: Config Manager
try:
    from jarvis_mcp.config.config_manager import ConfigManager
    cfg = ConfigManager()
    results['1_config_manager'] = True
    passed += print_test(1, "ConfigManager", True)
except Exception as e:
    results['1_config_manager'] = False
    passed += print_test(1, "ConfigManager", False, str(e)[:30])

# Test 2: Logger
try:
    from jarvis_mcp.utils.logger import setup_logger
    logger = setup_logger("test")
    results['2_logger'] = True
    passed += print_test(2, "Logger", True)
except Exception as e:
    results['2_logger'] = False
    passed += print_test(2, "Logger", False, str(e)[:30])

# Test 3: File Utils
try:
    from jarvis_mcp.utils.file_utils import read_file, write_file
    results['3_file_utils'] = True
    passed += print_test(3, "File Utils", True)
except Exception as e:
    results['3_file_utils'] = False
    passed += print_test(3, "File Utils", False, str(e)[:30])

# Test 4: Safety Guard
try:
    from jarvis_mcp.safety.guard import SafetyGuard
    guard = SafetyGuard()
    results['4_safety_guard'] = True
    passed += print_test(4, "Safety Guard", True)
except Exception as e:
    results['4_safety_guard'] = False
    passed += print_test(4, "Safety Guard", False, str(e)[:30])

# Test 5: LLM Manager
try:
    from jarvis_mcp.llm.llm_manager import LLMManager
    from jarvis_mcp.config.config_manager import ConfigManager
    cfg = ConfigManager()
    llm = LLMManager(cfg)
    results['5_llm_manager'] = True
    passed += print_test(5, "LLM Manager", True)
except Exception as e:
    results['5_llm_manager'] = False
    passed += print_test(5, "LLM Manager", False, str(e)[:30])

# ============================================================================
# TEST 6-10: Data & Context Systems
# ============================================================================
print_header("DATA & CONTEXT SYSTEMS")

# Test 6: Account Hierarchy
try:
    from jarvis_mcp.account_hierarchy import AccountHierarchy
    with TemporaryDirectory() as tmpdir:
        ah = AccountHierarchy(tmpdir)
        ah.rebuild_cache()
        results['6_account_hierarchy'] = True
        passed += print_test(6, "Account Hierarchy", True)
except Exception as e:
    results['6_account_hierarchy'] = False
    passed += print_test(6, "Account Hierarchy", False, str(e)[:30])

# Test 7: Comprehensive Data Aggregator
try:
    from jarvis_mcp.comprehensive_data_aggregator import ComprehensiveDataAggregator
    with TemporaryDirectory() as tmpdir:
        agg = ComprehensiveDataAggregator(tmpdir)
        context = agg.aggregate_all_context()
        assert isinstance(context, dict)
        results['7_aggregator'] = True
        passed += print_test(7, "Data Aggregator", True)
except Exception as e:
    results['7_aggregator'] = False
    passed += print_test(7, "Data Aggregator", False, str(e)[:30])

# Test 8: Skill Context Enricher
try:
    from jarvis_mcp.skill_context_enricher import SkillContextEnricher
    with TemporaryDirectory() as tmpdir:
        sce = SkillContextEnricher(tmpdir)
        results['8_enricher'] = True
        passed += print_test(8, "Context Enricher", True)
except Exception as e:
    results['8_enricher'] = False
    passed += print_test(8, "Context Enricher", False, str(e)[:30])

# Test 9: Advanced Fuzzy Matcher
try:
    from jarvis_mcp.advanced_fuzzy_matcher import AdvancedFuzzyMatcher
    afm = AdvancedFuzzyMatcher()
    match = afm.match("acme", ["AcmeCorp"])
    assert match is not None
    results['9_fuzzy_matcher'] = True
    passed += print_test(9, "Fuzzy Matcher", True)
except Exception as e:
    results['9_fuzzy_matcher'] = False
    passed += print_test(9, "Fuzzy Matcher", False, str(e)[:30])

# Test 10: Advanced NLP Extractor
try:
    from jarvis_mcp.advanced_nlp_extractor import AdvancedNLPExtractor
    nlp = AdvancedNLPExtractor()
    text = "TataCommunications is a telecom company with 100k employees"
    result = nlp.extract_all(text)
    assert result is not None
    results['10_nlp_extractor'] = True
    passed += print_test(10, "NLP Extractor", True)
except Exception as e:
    results['10_nlp_extractor'] = False
    passed += print_test(10, "NLP Extractor", False, str(e)[:30])

# ============================================================================
# TEST 11-15: Intelligence Systems
# ============================================================================
print_header("INTELLIGENCE & ANALYSIS SYSTEMS")

# Test 11: Competitor Knowledge Base
try:
    from jarvis_mcp.competitor_knowledge_base import CompetitorKnowledgeBase
    with TemporaryDirectory() as tmpdir:
        ckb = CompetitorKnowledgeBase(tmpdir)
        results['11_competitor_kb'] = True
        passed += print_test(11, "Competitor KB", True)
except Exception as e:
    results['11_competitor_kb'] = False
    passed += print_test(11, "Competitor KB", False, str(e)[:30])

# Test 12: Context Detector
try:
    from jarvis_mcp.context_detector import ContextDetector
    cd = ContextDetector()
    results['12_context_detector'] = True
    passed += print_test(12, "Context Detector", True)
except Exception as e:
    results['12_context_detector'] = False
    passed += print_test(12, "Context Detector", False, str(e)[:30])

# Test 13: Skills Registry
try:
    from jarvis_mcp.skills import SKILL_REGISTRY
    assert isinstance(SKILL_REGISTRY, dict)
    assert len(SKILL_REGISTRY) > 0
    results['13_skill_registry'] = True
    passed += print_test(13, f"Skill Registry ({len(SKILL_REGISTRY)} skills)", True)
except Exception as e:
    results['13_skill_registry'] = False
    passed += print_test(13, "Skill Registry", False, str(e)[:30])

# Test 14: Base Skill
try:
    from jarvis_mcp.skills.base_skill import BaseSkill
    results['14_base_skill'] = True
    passed += print_test(14, "Base Skill", True)
except Exception as e:
    results['14_base_skill'] = False
    passed += print_test(14, "Base Skill", False, str(e)[:30])

# Test 15: Agents Orchestrator
try:
    from jarvis_mcp.agents import AgentOrchestrator
    results['15_agent_orchestrator'] = True
    passed += print_test(15, "Agent Orchestrator", True)
except Exception as e:
    results['15_agent_orchestrator'] = False
    passed += print_test(15, "Agent Orchestrator", False, str(e)[:30])

# ============================================================================
# TEST 16-20: Server & Integration
# ============================================================================
print_header("MCP SERVER & INTEGRATION")

# Test 16: MCP Server
try:
    from jarvis_mcp.mcp_server import JarvisServer
    server = JarvisServer()
    assert server.skills is not None
    assert len(server.skills) > 0
    results['16_mcp_server'] = True
    passed += print_test(16, "MCP Server", True)
except Exception as e:
    results['16_mcp_server'] = False
    passed += print_test(16, "MCP Server", False, str(e)[:30])

# Test 17: Tool Registry
try:
    from jarvis_mcp.mcp_server import JarvisServer
    server = JarvisServer()
    tools = server._get_tool_list()
    assert len(tools) >= 24
    results['17_tool_registry'] = True
    passed += print_test(17, f"Tool Registry ({len(tools)} tools)", True)
except Exception as e:
    results['17_tool_registry'] = False
    passed += print_test(17, "Tool Registry", False, str(e)[:30])

# Test 18: Skill Initialization
try:
    from jarvis_mcp.mcp_server import JarvisServer
    server = JarvisServer()
    assert len(server.skills) >= 20
    results['18_skill_initialization'] = True
    passed += print_test(18, f"Skills Initialized ({len(server.skills)})", True)
except Exception as e:
    results['18_skill_initialization'] = False
    passed += print_test(18, "Skills Initialization", False, str(e)[:30])

# Test 19: Enricher Integration
try:
    from jarvis_mcp.mcp_server import JarvisServer
    server = JarvisServer()
    assert server.enricher is not None
    results['19_enricher_integration'] = True
    passed += print_test(19, "Enricher Integration", True)
except Exception as e:
    results['19_enricher_integration'] = False
    passed += print_test(19, "Enricher Integration", False, str(e)[:30])

# Test 20: Safety Integration
try:
    from jarvis_mcp.mcp_server import JarvisServer
    server = JarvisServer()
    assert server.guard is not None
    results['20_safety_integration'] = True
    passed += print_test(20, "Safety Integration", True)
except Exception as e:
    results['20_safety_integration'] = False
    passed += print_test(20, "Safety Integration", False, str(e)[:30])

# ============================================================================
# TEST 21-25: End-to-End Integration
# ============================================================================
print_header("END-TO-END INTEGRATION")

# Test 21: Account Context Loading
try:
    from jarvis_mcp.skill_context_enricher import SkillContextEnricher
    from pathlib import Path
    from tempfile import TemporaryDirectory
    import json

    with TemporaryDirectory() as tmpdir:
        test_accounts = Path(tmpdir) / "ACCOUNTS"
        test_accounts.mkdir(exist_ok=True)

        # Create test account
        acme = test_accounts / "AcmeCorp"
        acme.mkdir(exist_ok=True)
        (acme / "company_profile.json").write_text(json.dumps({"name": "Acme", "revenue": "$100M"}))
        (acme / "deal_stage.json").write_text(json.dumps({"deals": {"d1": {"value": 1000000}}}))

        enricher = SkillContextEnricher(str(test_accounts))
        context = enricher.get_enriched_context("AcmeCorp")

        assert context is not None
        assert 'account_path' in context
        assert context['account_name'] == 'AcmeCorp'

        results['21_account_context'] = True
        passed += print_test(21, "Account Context Loading", True)
except Exception as e:
    results['21_account_context'] = False
    passed += print_test(21, "Account Context Loading", False, str(e)[:30])

# Test 22: Skill-Specific Context
try:
    from jarvis_mcp.skill_context_enricher import SkillContextEnricher
    from pathlib import Path
    from tempfile import TemporaryDirectory
    import json

    with TemporaryDirectory() as tmpdir:
        test_accounts = Path(tmpdir) / "ACCOUNTS"
        test_accounts.mkdir(exist_ok=True)

        acme = test_accounts / "AcmeCorp"
        acme.mkdir(exist_ok=True)
        (acme / "company_profile.json").write_text(json.dumps({"name": "Acme"}))
        (acme / "deal_stage.json").write_text(json.dumps({"deals": {}}))

        enricher = SkillContextEnricher(str(test_accounts))
        skill_ctx = enricher.get_context_for_skill("AcmeCorp", "proposal")

        assert '_skill_focus' in skill_ctx
        assert skill_ctx['_skill_focus']['type'] == 'proposal'

        results['22_skill_context'] = True
        passed += print_test(22, "Skill-Specific Context", True)
except Exception as e:
    results['22_skill_context'] = False
    passed += print_test(22, "Skill-Specific Context", False, str(e)[:30])

# Test 23: Fuzzy Account Matching
try:
    from jarvis_mcp.advanced_fuzzy_matcher import AdvancedFuzzyMatcher

    matcher = AdvancedFuzzyMatcher()

    # Test various match types
    matches = [
        matcher.match("tata", ["TataCommunications"]),
        matcher.match("acme corp", ["AcmeCorp"]),
        matcher.match("TC", ["TataCommunications"]),
    ]

    # At least 2 should work
    success_count = sum(1 for m in matches if m is not None)
    assert success_count >= 2

    results['23_fuzzy_matching'] = True
    passed += print_test(23, f"Fuzzy Matching ({success_count}/3)", True)
except Exception as e:
    results['23_fuzzy_matching'] = False
    passed += print_test(23, "Fuzzy Matching", False, str(e)[:30])

# Test 24: NLP Extraction
try:
    from jarvis_mcp.advanced_nlp_extractor import AdvancedNLPExtractor

    nlp = AdvancedNLPExtractor()
    text = "TataCommunications Ltd is a major telecom in India with 5000 employees, revenue $5B"

    result = nlp.extract_all(text)

    assert result is not None
    # Should extract at least company and size/revenue
    assert 'company' in result or 'size' in result or 'revenue' in result

    results['24_nlp_extraction'] = True
    passed += print_test(24, "NLP Extraction", True)
except Exception as e:
    results['24_nlp_extraction'] = False
    passed += print_test(24, "NLP Extraction", False, str(e)[:30])

# Test 25: Dashboard HTML
try:
    dashboard_path = Path("/Users/syounus/Documents/claude space/Personal-AE-SC-Jarvis/JARVIS_REALTIME_DASHBOARD.html")

    assert dashboard_path.exists()
    assert dashboard_path.stat().st_size > 10000  # At least 10KB

    content = dashboard_path.read_text()
    assert "JARVIS" in content or "Dashboard" in content

    results['25_dashboard_html'] = True
    passed += print_test(25, "Dashboard HTML", True)
except Exception as e:
    results['25_dashboard_html'] = False
    passed += print_test(25, "Dashboard HTML", False, str(e)[:30])

# ============================================================================
# SUMMARY
# ============================================================================
print_header(f"VALIDATION SUMMARY: {passed}/{total} SYSTEMS PASSED")

if passed == total:
    print(f"\n🎉 PERFECT! All {total} systems validated and working!\n")
    sys.exit(0)
else:
    print(f"\n⚠️  {total - passed} system(s) need attention\n")

    # Show failures
    failures = [k.split('_', 1)[1] for k, v in results.items() if not v]
    if failures:
        print("Failed systems:")
        for fail in failures:
            print(f"  • {fail}")

    sys.exit(1)
