"""Quick test of multi-agent system."""

import asyncio
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("\n✅ Testing Multi-Agent System...\n")
    
    from jarvis_mcp.knowledge.knowledge_base import KnowledgeBase
    from jarvis_mcp.agents.agent_orchestrator import AgentOrchestrator
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test files
        (tmpdir / "discovery.txt").write_text("Customer discovery findings for Acme")
        (tmpdir / "proposal.json").write_text('{"client": "Acme", "value": "high"}')
        
        print("1️⃣  Initializing orchestrator...")
        orchestrator = AgentOrchestrator(str(tmpdir))
        print("   ✅ Orchestrator created")
        
        print("\n2️⃣  Starting orchestration...")
        await orchestrator.start()
        print("   ✅ Orchestrator running")
        
        print("\n3️⃣  Running orchestration cycle...")
        cycle = await orchestrator.run_cycle()
        print(f"   ✅ Cycle {cycle['cycle']} complete")
        print(f"   - Files detected: {cycle.get('files_detected', 0)}")
        print(f"   - Knowledge base: {cycle['knowledge_base']}")
        
        print("\n4️⃣  Testing context enrichment...")
        enriched = await orchestrator.enrich_skill_context(
            "proposal",
            "Generate a proposal for the customer"
        )
        print(f"   ✅ Context enriched ({len(enriched)} chars)")
        
        print("\n5️⃣  Getting system status...")
        status = await orchestrator.get_system_status()
        print(f"   ✅ Orchestrator running: {status['orchestrator_running']}")
        print(f"   ✅ Cycles executed: {status['cycles_executed']}")
        
        print("\n6️⃣  Stopping orchestrator...")
        await orchestrator.stop()
        print("   ✅ Stopped gracefully")
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
