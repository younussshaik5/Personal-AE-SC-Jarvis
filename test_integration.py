#!/usr/bin/env python3
"""
JARVIS v2.0 Integration Test
Validates all critical functionality before deployment
"""

import json
import sys
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class IntegrationTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0

    def test(self, name: str, fn):
        try:
            fn()
            self.tests_passed += 1
            print(f"{GREEN}✓{RESET} {name}")
        except Exception as e:
            self.tests_failed += 1
            print(f"{RED}✗{RESET} {name}: {e}")

    def report(self):
        total = self.tests_passed + self.tests_failed
        pct = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}INTEGRATION TEST REPORT{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"Passed: {GREEN}{self.tests_passed}{RESET}")
        print(f"Failed: {RED}{self.tests_failed}{RESET}")
        print(f"Total:  {BLUE}{total}{RESET}")
        print(f"Score:  {YELLOW}{pct:.0f}%{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")
        
        return self.tests_failed == 0


# Infrastructure tests
def test_imports():
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.llm.llm_manager import LLMManager
    from jarvis_mcp.utils.logger import setup_logger, JARVISLogger
    from jarvis_mcp.safety.guard import SafetyGuard
    from jarvis_mcp.mcp_server import JarvisServer
    from jarvis_mcp.skills import SKILL_REGISTRY


def test_config_manager():
    from jarvis_mcp.config.config_manager import ConfigManager
    config = ConfigManager()
    tata_path = config.get_account_path("Tata")
    assert "Tata" in str(tata_path)
    accounts_root = config.get_accounts_root()
    assert accounts_root.exists()


def test_account_hierarchy():
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.account_hierarchy import AccountHierarchy
    
    config = ConfigManager()
    hierarchy = AccountHierarchy(config.get_accounts_root())
    
    tata = hierarchy.find_account("Tata")
    assert tata is not None, "Tata not found"
    
    tatat = hierarchy.find_account("TataTele")
    assert tatat is not None, "TataTele not found"
    assert "Tata" in str(tatat)


def test_context_detector():
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.context_detector import ContextDetector
    
    config = ConfigManager()
    detector = ContextDetector(config.get_accounts_root())
    context = detector.detect_account_context()
    assert context is None or isinstance(context, dict)


def test_account_files_tata():
    from jarvis_mcp.config.config_manager import ConfigManager
    config = ConfigManager()
    tata_path = config.get_account_path("Tata")
    
    for filename in ["deal_stage.json", "company_research.md", "discovery.md", "CLAUDE.md", "dashboard.html"]:
        assert (tata_path / filename).exists(), f"Missing: {filename}"


def test_account_files_tatat():
    from jarvis_mcp.config.config_manager import ConfigManager
    config = ConfigManager()
    tata_path = config.get_account_path("Tata")
    tatat_path = tata_path / "TataTele"
    
    for filename in ["deal_stage.json", "discovery.md", "CLAUDE.md", "dashboard.html"]:
        assert (tatat_path / filename).exists(), f"Missing in TataTele: {filename}"


def test_deal_stage_json():
    from jarvis_mcp.config.config_manager import ConfigManager
    config = ConfigManager()
    deal_path = config.get_account_path("Tata") / "deal_stage.json"
    
    deal_data = json.loads(deal_path.read_text())
    for field in ["account_name", "stage", "probability", "deal_size", "stakeholders", "activities"]:
        assert field in deal_data, f"Missing field: {field}"


def test_claude_md_loader():
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.claude_md_loader import ClaudeMdLoader
    
    config = ConfigManager()
    loader = ClaudeMdLoader(config.get_accounts_root())
    
    tata_path = config.get_account_path("Tata")
    settings = loader.load_for_account(tata_path)
    
    assert settings is not None
    assert isinstance(settings, dict)


def test_skill_registry():
    from jarvis_mcp.skills import SKILL_REGISTRY
    assert len(SKILL_REGISTRY) >= 25, f"Only {len(SKILL_REGISTRY)} skills"
    
    for skill in ["scaffold_account", "discovery", "battlecard", "proposal"]:
        assert skill in SKILL_REGISTRY, f"Missing skill: {skill}"


def test_mcp_server_init():
    from jarvis_mcp.mcp_server import JarvisServer
    
    server = JarvisServer()
    assert server is not None
    assert len(server.skills) >= 25
    assert server.config is not None
    assert server.llm is not None
    assert hasattr(server, 'account_hierarchy')
    assert hasattr(server, 'context_detector')


def test_account_hierarchy_depth():
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.account_hierarchy import AccountHierarchy
    
    config = ConfigManager()
    hierarchy = AccountHierarchy(config.get_accounts_root())
    all_accounts = hierarchy.list_all_accounts()
    
    assert len(all_accounts) == 3, f"Expected 3 accounts, found {len(all_accounts)}"


def test_dashboard_html():
    from jarvis_mcp.config.config_manager import ConfigManager
    config = ConfigManager()
    dashboard_path = config.get_account_path("Tata") / "dashboard.html"
    
    assert dashboard_path.exists()
    content = dashboard_path.read_text()
    assert "<html" in content.lower()
    assert "dashboard" in content.lower()


def test_file_structure():
    from jarvis_mcp.config.config_manager import ConfigManager
    config = ConfigManager()
    
    tata_path = config.get_account_path("Tata")
    assert tata_path.exists()
    assert (tata_path / "company_research.md").exists()
    
    tatat_path = tata_path / "TataTele"
    assert tatat_path.exists()
    assert (tatat_path / "discovery.md").exists()


def test_safety_guard():
    from jarvis_mcp.safety.guard import SafetyGuard
    
    guard = SafetyGuard()
    assert guard.is_safe() == True
    assert guard.check_killswitch() == False


def test_llm_manager():
    from jarvis_mcp.config.config_manager import ConfigManager
    from jarvis_mcp.llm.llm_manager import LLMManager
    
    config = ConfigManager()
    llm = LLMManager(config)
    
    assert llm is not None
    assert llm.config is not None
    assert hasattr(llm, 'generate')


def main():
    print(f"\n{BOLD}{BLUE}JARVIS v2.0 Integration Test Suite{RESET}\n")
    
    tester = IntegrationTester()
    
    print(f"{BOLD}Infrastructure:{RESET}")
    tester.test("Imports", test_imports)
    tester.test("ConfigManager", test_config_manager)
    tester.test("SafetyGuard", test_safety_guard)
    tester.test("LLMManager", test_llm_manager)
    
    print(f"\n{BOLD}Account System:{RESET}")
    tester.test("AccountHierarchy", test_account_hierarchy)
    tester.test("Tata account files", test_account_files_tata)
    tester.test("TataTele account files", test_account_files_tatat)
    tester.test("deal_stage.json", test_deal_stage_json)
    tester.test("Hierarchy depth", test_account_hierarchy_depth)
    tester.test("File structure", test_file_structure)
    
    print(f"\n{BOLD}Context & Settings:{RESET}")
    tester.test("ContextDetector", test_context_detector)
    tester.test("ClaudeMdLoader", test_claude_md_loader)
    
    print(f"\n{BOLD}Skills & Server:{RESET}")
    tester.test("SkillRegistry", test_skill_registry)
    tester.test("JarvisServer init", test_mcp_server_init)
    
    print(f"\n{BOLD}User Interface:{RESET}")
    tester.test("Dashboard HTML", test_dashboard_html)
    
    success = tester.report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
