import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime

class AgentOrchestrator:
    """Master orchestrator - coordinates all agents and evolution for full autonomy."""

    def __init__(self, account_path: str):
        """Initialize orchestrator with all agents AND evolution system."""
        from .file_monitor_agent import FileMonitorAgent
        from .vectorizer_agent import VectorizerAgent
        from .context_aggregator_agent import ContextAggregatorAgent
        from .outcome_predictor_agent import OutcomePredictorAgent
        from .bottleneck_detector_agent import BottleneckDetectorAgent
        from .evolution_optimizer_agent import EvolutionOptimizerAgent
        from ..knowledge.knowledge_base import KnowledgeBase
        from ..evolution.file_evolver import FileEvolver
        from ..evolution.conversation_analyzer import ConversationAnalyzer
        from ..evolution.outcome_recorder import OutcomeRecorder
        from ..evolution.cowork_integrator import CoworkIntegrator

        self.account_path = Path(account_path)
        self.orchestration_log = self.account_path / ".orchestration_log.json"
        self.kb = KnowledgeBase(str(self.account_path))
        
        # LEARNING AGENTS
        self.file_monitor = FileMonitorAgent(str(self.account_path))
        self.vectorizer = VectorizerAgent(self.kb)
        self.context_aggregator = ContextAggregatorAgent(self.kb)
        self.outcome_predictor = OutcomePredictorAgent(str(self.account_path))
        self.bottleneck_detector = BottleneckDetectorAgent(str(self.account_path))
        self.evolution_optimizer = EvolutionOptimizerAgent(str(self.account_path))
        
        # EVOLUTION/AUTONOMY SYSTEM
        self.file_evolver = FileEvolver(str(self.account_path))
        self.conversation_analyzer = ConversationAnalyzer(str(self.account_path))
        self.outcome_recorder = OutcomeRecorder(str(self.account_path))
        self.cowork_integrator = CoworkIntegrator(str(self.account_path))

        self.running = False
        self.cycle_count = 0

        if not self.orchestration_log.exists():
            with open(self.orchestration_log, "w") as f:
                json.dump([], f, indent=2)

    async def start(self):
        self.running = True
        print("[ORCHESTRATOR] 🚀 Starting autonomous AI employee system...")

    async def stop(self):
        self.running = False
        print("[ORCHESTRATOR] 🛑 Stopping autonomous system...")

    async def run_full_cycle(self) -> Dict[str, Any]:
        """Run complete autonomous cycle - learning + evolution + optimization."""
        self.cycle_count += 1
        cycle_result = {
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "phases": {}
        }

        try:
            # PHASE 1: FILE MONITORING & LEARNING
            print(f"\n[CYCLE {self.cycle_count}] Phase 1: Document Learning...")
            files_detected = await self.file_monitor.scan_for_changes()
            cycle_result["phases"]["file_monitoring"] = {
                "files_detected": len(files_detected),
                "status": "complete"
            }
            
            # PHASE 2: VECTORIZATION
            print(f"[CYCLE {self.cycle_count}] Phase 2: Knowledge Vectorization...")
            unprocessed = await self.file_monitor.get_unprocessed_files()
            for file_path in unprocessed[:3]:  # Process up to 3 per cycle
                doc_id = await self.vectorizer.vectorize_document(file_path)
                if doc_id:
                    await self.file_monitor.mark_processed(file_path)
                    print(f"  ✓ Vectorized: {Path(file_path).name}")
            
            # PHASE 3: KNOWLEDGE BASE STATUS
            kb_status = await self.kb.get_account_summary()
            cycle_result["phases"]["knowledge_base"] = kb_status
            
            # PHASE 4: OUTCOME ANALYSIS
            print(f"[CYCLE {self.cycle_count}] Phase 3: Outcome Analysis...")
            effectiveness = await self.outcome_recorder.get_effectiveness_report()
            cycle_result["phases"]["skill_effectiveness"] = {
                "skills_tracked": len(effectiveness["skills"]),
                "top_performer": effectiveness["top_performers"][0][0] if effectiveness["top_performers"] else None
            }
            
            # PHASE 5: BOTTLENECK DETECTION
            print(f"[CYCLE {self.cycle_count}] Phase 4: Process Analysis...")
            bottlenecks = await self.bottleneck_detector.analyze_process_health()
            cycle_result["phases"]["bottleneck_analysis"] = bottlenecks
            
            # PHASE 6: CONVERSATION LEARNING
            print(f"[CYCLE {self.cycle_count}] Phase 5: Conversation Intelligence...")
            conv_insights = await self.conversation_analyzer.extract_learning_data()
            cycle_result["phases"]["conversation_learning"] = {
                "conversations_analyzed": conv_insights.get("total_conversations", 0),
                "pain_points_identified": len(conv_insights.get("common_pain_points", []))
            }
            
            # PHASE 7: FILE EVOLUTION - ACTUALLY MODIFY FILES
            print(f"[CYCLE {self.cycle_count}] Phase 6: System Evolution...")
            ready_insights = await self.conversation_analyzer.get_ready_to_learn_insights()
            if ready_insights.get("ready_to_learn"):
                evolution_changes = await self.file_evolver.evolve_from_conversation({
                    "pain_points": ready_insights.get("pain_points", []),
                    "objections": ready_insights.get("objections", []),
                    "success_pattern": "Enriched with learnings",
                    "skill": "general"
                })
                cycle_result["phases"]["file_evolution"] = {
                    "files_modified": evolution_changes.get("files_modified", []),
                    "changes_applied": len(evolution_changes.get("changes", [])),
                    "status": "evolved"
                }
                print(f"  ✓ Files evolved: {', '.join(evolution_changes.get('files_modified', []))}")
            else:
                cycle_result["phases"]["file_evolution"] = {
                    "status": "no_learning_yet"
                }
            
            # PHASE 8: COWORK INTEGRATION
            print(f"[CYCLE {self.cycle_count}] Phase 7: Cowork Integration...")
            cowork_status = await self.cowork_integrator.get_integrator_status()
            cycle_result["phases"]["cowork_integration"] = cowork_status

            self._log_cycle(cycle_result)
            print(f"[CYCLE {self.cycle_count}] ✅ Cycle complete\n")

        except Exception as e:
            cycle_result["error"] = str(e)
            print(f"[CYCLE {self.cycle_count}] ❌ Error: {e}\n")

        return cycle_result

    async def record_skill_outcome(self, skill_name: str, opportunity_id: str, result: Dict[str, Any]):
        """Record outcome of skill execution for learning."""
        await self.outcome_recorder.record_outcome(skill_name, opportunity_id, result)
        
        # If high quality outcome, trigger file evolution
        if result.get("quality_score", 0) >= 4.0:
            await self.file_evolver.evolve_from_outcomes(result)

    async def analyze_user_chat(self, user_message: str, assistant_response: str, skill_used: Optional[str] = None):
        """Analyze chat and extract learnings."""
        await self.conversation_analyzer.analyze_chat(
            user_message,
            assistant_response,
            {"skill": skill_used}
        )

    async def process_cowork_upload(self, file_path: str, file_name: str):
        """Process file uploaded from cowork."""
        await self.cowork_integrator.process_cowork_upload(file_path, file_name)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        return {
            "orchestrator_running": self.running,
            "cycles_executed": self.cycle_count,
            "evolution_ready": True,
            "full_autonomy_enabled": True
        }

    async def enrich_skill_context(self, skill_name: str, prompt: str) -> str:
        return await self.context_aggregator.enrich_skill_context(skill_name, prompt)

    def _log_cycle(self, result: Dict[str, Any]):
        """Log orchestration cycle."""
        try:
            with open(self.orchestration_log, "r") as f:
                log = json.load(f)
        except Exception:
            log = []

        log.append(result)
        log = log[-100:]

        try:
            with open(self.orchestration_log, "w") as f:
                json.dump(log, f, indent=2)
        except Exception:
            pass
