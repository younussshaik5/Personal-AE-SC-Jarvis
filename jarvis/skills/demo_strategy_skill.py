#!/usr/bin/env python3
"""Demo Strategy Skill - Demo intelligence, tech stack analysis, and strategic positioning."""

import asyncio, json, re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.data_aggregator import read_all_skill_data
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.identity import get_se_identity
from jarvis.llm.llm_client import LLMManager, Message
from jarvis.services.research_service import DynamicResearchService
from jarvis.utils.account_utils import extract_account_name


class DemoStrategySkill:
    """Dynamic demo strategy with live tech stack analysis, competitive landmines, and personalized narrative."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.demo_strategy")
        self.workspace_root = Path(config_manager.config.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._last_updates: Dict[str, datetime] = {}
        self._update_interval = 60
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.llm: Optional[LLMManager] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self.research_service: Optional[DynamicResearchService] = None

    async def start(self):
        self.logger.info("Starting demo strategy skill")
        self._running = True
        self._main_loop = asyncio.get_running_loop()
        try:
            self.llm = LLMManager(self.config_manager)
            await self.llm.initialize()
        except Exception as e:
            self.logger.warning("LLM unavailable", error=str(e))
            self.llm = None
        try:
            self.research_service = DynamicResearchService(self.config_manager, self.llm)
            await self.research_service.start()
        except Exception as e:
            self.logger.warning("Research service unavailable", error=str(e))

        self.event_bus.subscribe("account.initialized", self._on_account_initialized)
        self.event_bus.subscribe("file.modified", self._on_file_modified)
        self.event_bus.subscribe("conversation.stored", self._on_conversation_stored)
        self.event_bus.subscribe("battlecards.updated", self._on_battlecards_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)
        self.event_bus.subscribe("risk.report.updated", self._on_risk_report_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Skill started - Demo Strategy active")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.research_service:
            await self.research_service.stop()
        self.logger.info("Skill stopped")

    # Event handlers
    def _on_account_initialized(self, event: Event):
        account_name = event.data.get("account_name")
        if account_name:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account_name, 30))
            )

    def _on_file_modified(self, event: Event):
        path = Path(event.data.get("path", ""))
        if not self._is_account_file(path):
            return
        account_name = self._extract_account_name(path)
        if account_name:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account_name, 15))
            )

    def _on_conversation_stored(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 20))
            )

    def _on_battlecards_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    def _on_discovery_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    def _on_risk_report_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    # Utility methods
    def _is_account_file(self, path: Path) -> bool:
        try:
            rel = path.resolve().relative_to(self.accounts_dir.resolve())
            return True
        except ValueError:
            return False

    def _extract_account_name(self, path: Path) -> Optional[str]:
        return extract_account_name(path, self.accounts_dir)

    async def _debounced_update(self, account_name: str, delay_seconds: int):
        now = datetime.now()
        last = self._last_updates.get(account_name)
        if last and (now - last).total_seconds() < delay_seconds:
            return
        self._last_updates[account_name] = now
        await self._update_demo_strategy(account_name)

    async def _periodic_scan(self):
        while self._running:
            try:
                await asyncio.sleep(self._update_interval)
                await self._scan_all_accounts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Periodic scan error", error=str(e))

    async def _scan_all_accounts(self):
        if not self.accounts_dir.exists():
            return
        for team_dir in self.accounts_dir.iterdir():
            if team_dir.is_dir() and not team_dir.name.startswith('.'):
                for account_dir in team_dir.iterdir():
                    if account_dir.is_dir() and not account_dir.name.startswith('.'):
                        if not self._is_valid_account_folder(account_dir):
                            continue
                        await self._update_demo_strategy(account_dir.name)

    async def _update_demo_strategy(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_account_data(account_folder)
            if not data:
                return

            # Create demo_strategy folder
            demo_dir = account_folder / "demo_strategy"
            demo_dir.mkdir(exist_ok=True)

            # Generate demo strategy document
            strategy_content = await self._generate_demo_strategy(account_name, data)
            (demo_dir / "demo_strategy.md").write_text(strategy_content, encoding='utf-8')

            # Generate technical talking points
            tech_points = self._generate_tech_talking_points(account_name, data)
            (demo_dir / "tech_talking_points.md").write_text(tech_points, encoding='utf-8')

            # Generate demo script with narrative
            script_content = self._generate_demo_script(account_name, data)
            (demo_dir / "demo_script.md").write_text(script_content, encoding='utf-8')

            self.logger.info("Updated Demo Strategy", account=account_name)
            self.event_bus.publish(Event("demo.strategy.updated", "skill.demo_strategy", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update Demo Strategy", account=account_name, error=str(e))

    async def _find_account_folder(self, account_name: str) -> Optional[Path]:
        for team_dir in self.accounts_dir.iterdir():
            if team_dir.is_dir():
                candidate = team_dir / account_name
                if candidate.exists() and candidate.is_dir():
                    return candidate
        return None

    async def _gather_account_data(self, account_folder: Path) -> Dict[str, Any]:
        """Gather comprehensive data from all skill outputs + live research."""
        data = {
            'account_name': account_folder.name,
            'deals': [],
            'notes': {},
            'competitors': set()
        }

        # Core data
        deals_dir = account_folder / "deals"
        if deals_dir.exists():
            for deal_file in deals_dir.glob("*.json"):
                try:
                    with open(deal_file) as f:
                        data['deals'].append(json.load(f))
                except:
                    pass

        notes_file = account_folder / "notes.json"
        if notes_file.exists():
            try:
                with open(notes_file) as f:
                    data['notes'] = json.load(f)
            except:
                pass

        # Competitors from deals and notes
        for deal in data['deals']:
            data['competitors'].update(deal.get('competitors', []))
        facts = data['notes'].get('facts', [])
        for fact in facts:
            if 'competitor' in fact.lower():
                data['competitors'].add(fact)

        # Read ALL skill-generated files (cross-skill context)
        all_skill_data = read_all_skill_data(account_folder)
        data.update(all_skill_data)

        # Real-time research enrichment
        if self.research_service:
            await self._enrich_with_research(account_folder.name, data)

        return data

    async def _enrich_with_research(self, account_name: str, data: Dict[str, Any]):
        """Add real-time research data."""
        try:
            company = account_name.split('::')[0].strip()
            company_data = await self.research_service.research_company(company)
            data['research'] = company_data
            data['tech_stack'] = company_data.get('tech_stack', {})

            # Research each competitor more deeply
            for competitor in list(data['competitors'])[:3]:
                comp_data = await self.research_service.research_competitor(competitor)
                data.setdefault('competitors_research', {})[competitor] = comp_data

        except Exception as e:
            self.logger.debug("Research enrichment failed", error=str(e))

    def _sanitize_name(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_').lower()

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has_smartness = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    def _parse_meddpicc(self, content: str) -> Dict[str, Any]:
        win_prob = 'Unknown'
        risk_level = 'Unknown'
        import re
        match = re.search(r'Win Probability:\s*(\d+%|\?+|Unknown)', content)
        if match:
            win_prob = match.group(1)
        for level in ['Critical', 'High', 'Medium', 'Low']:
            if level in content:
                risk_level = level
                break
        return {'win_probability': win_prob, 'risk_level': risk_level}

    def _parse_battlecards(self, content: str) -> Dict[str, Any]:
        return {'content': content[:500]}

    def _parse_risk_report(self, content: str) -> Dict[str, Any]:
        risk_score = 0
        import re
        match = re.search(r'Overall Risk Score:\s*(\d+)', content)
        if match:
            risk_score = int(match.group(1))
        return {'risk_score': risk_score, 'content': content[:500]}

    async def _generate_demo_strategy(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        research = data.get('research', {})
        battlecards = data.get('battlecards', {})
        risk_report = data.get('risk_report', {})
        meddpicc = data.get('meddpicc', {})
        discovery = data.get('discovery', {})
        competitors = list(data['competitors'])
        comp_research = data.get('competitors_research', {})

        strategy_prompt = f"""
        Create a comprehensive demo strategy for {account_name}.

        Account Context:
        - Industry: {research.get('industry', 'Unknown')}
        - Company Size: {research.get('k10_metrics', {}).get('employee_count', 'Unknown')}
        - Tech Stack: {json.dumps(research.get('tech_stack', {}), indent=2)}
        - Financial Health: {research.get('k10_metrics', {}).get('growth_rate', 'Unknown')}% growth
        - Priorities: {', '.join(research.get('priorities', [])[:5])}

        Competitors: {', '.join(competitors) if competitors else 'None identified'}

        MEDDPICC Status:
        - Win Probability: {meddpicc.get('win_probability', 'Unknown')}
        - Risk Level: {meddpicc.get('risk_level', 'Unknown')}

        Risk Assessment:
        - Risk Score: {risk_report.get('risk_score', 'Unknown')}/100
        - Key concerns: {json.dumps(risk_report.get('top_risks', [])[:3])}

        Discovery Coverage:
        - Internal: {'Yes' if discovery.get('internal') else 'No'}
        - Final: {'Yes' if discovery.get('final') else 'No'}
        - Q2A: {'Yes' if discovery.get('q2a') else 'No'}

        Create a demo strategy JSON with:
        {{
          "narrative_hook": "Personalized opening story about their industry/priorities",
          "core_message": "Single most compelling value proposition",
          "demo_flow": [
            {{
              "section": "Discovery Recap",
              "duration": "5 min",
              "objective": "...",
              "personalization": "Tie to their specific context"
            }},
            ...
          ],
          "personalization_elements": [
            {{
              "element": "Customer logo on screen",
              "source": "notes.json",
              "impact": "Emotional connection"
            }}
          ],
          "competitive_landmines": [
            {{
              "topic": "Integration complexity",
              "competitor": "Salesforce",
              "trap_question": "...",
              "fresh_response": "..."
            }}
          ],
          "technical_showcases": [
            "Freddy AI deflection rates specific to their industry",
            "Time-to-value calculation based on their size",
            "Unified platform vs. competitor stack diagram"
          ],
          "objection_anticipation": [
            {{
              "objection": "We already have X",
              "response": "...",
              "evidence": "Real-time data point"
            }}
          ],
          "next_steps": ["..."]
        }}
        """

        if self.llm:
            try:
                response = await self.llm.generate([
                    Message(role="system", content="You are a demo strategy expert. Output only JSON."),
                    Message(role="user", content=strategy_prompt)
                ])
                content = response.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                strategy = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM strategy generation failed", error=str(e))
                strategy = self._fallback_strategy(account_name, data)
        else:
            strategy = self._fallback_strategy(account_name, data)

        return self._format_demo_strategy(account_name, identity, today, strategy, research, competitors)

    def _fallback_strategy(self, account_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "narrative_hook": f"Help {account_name} achieve their priorities with unified AI",
            "core_message": "Uncomplicated, AI-native unified platform reduces TCO by 30% and improves deflection by 80%",
            "demo_flow": [
                {"section": "Discovery Recap", "duration": "5 min", "objective": "Show we understand their business", "personalization": "Use their actual pain points"},
                {"section": "Platform Overview", "duration": "10 min", "objective": "Demonstrate unified architecture", "personalization": "Highlight relevant modules"},
                {"section": "AI Highlights", "duration": "8 min", "objective": "Show Freddy AI in action", "personalization": "Use their industry examples"},
                {"section": "Competitive Differentiators", "duration": "5 min", "objective": "Address gaps vs competitors", "personalization": f"vs {', '.join(list(data['competitors'])[:2])}"},
                {"section": "ROI & TCO", "duration": "7 min", "objective": "Quantify value", "personalization": "Based on their size"},
                {"section": "Next Steps", "duration": "5 min", "objective": "Agree on path forward", "personalization": "Address MEDDPICC gaps"}
            ],
            "personalization_elements": [
                {"element": "Customer logo", "source": "notes.json", "impact": "Emotional"},
                {"element": "Industry metrics", "source": "Research", "impact": "Relevance"}
            ],
            "competitive_landmines": [
                {"topic": "Complexity", "competitor": "Best-of-breed stack", "trap_question": "How many vendors do you manage?", "fresh_response": "One platform, one vendor, less risk"}
            ],
            "technical_showcases": [
                "Freddy AI with industry-specific deflection rates",
                "Unified data model eliminating integrations",
                "Fast deployment (weeks vs months)"
            ],
            "objection_anticipation": [
                {"objection": "We already have a solution", "response": "Many customers thought so until they saw TCO", "evidence": "Customer case studies"}
            ],
            "next_steps": ["Discovery call with technical team", "ROI workshop", "Pilot proposal"]
        }

    def _format_demo_strategy(self, account_name: str, identity, today: str, strategy: Dict[str, Any], research: Dict, competitors: List[str]) -> str:
        flow_md = ""
        for i, step in enumerate(strategy.get('demo_flow', []), 1):
            flow_md += f"{i}. **{step.get('section')}** ({step.get('duration')})\n   - Objective: {step.get('objective')}\n   - Personalization: {step.get('personalization')}\n\n"

        landmines_md = ""
        for lm in strategy.get('competitive_landmines', []):
            landmines_md += f"- **{lm.get('topic')}** vs {lm.get('competitor')}\n  - Trap: \"{lm.get('trap_question')}\"\n  - Response: \"{lm.get('fresh_response')}\"\n"

        objections_md = ""
        for obj in strategy.get('objection_anticipation', []):
            objections_md += f"- \"{obj.get('objection')}\"\n  - Response: {obj.get('response')}\n  - Evidence: {obj.get('evidence')}\n\n"

        showcases_md = "\n".join([f"- {cs}" for cs in strategy.get('technical_showcases', [])])

        return f"""# Demo Strategy - {account_name}

**Generated:** {today} | **Strategist:** {identity.full_display}

---

## Narrative Hook

> *{strategy.get('narrative_hook')}*

**Core Message:** {strategy.get('core_message')}

---

## Demo Flow

{flow_md}

---

## Competitive Landmines

{landmines_md if landmines_md else "- No specific landmines identified"}

---

## Technical Showcases

{showcases_md if showcases_md else "- Standard platform demonstration"}

---

## Objection Anticipation

{objections_md if objections_md else "- Prepare for standard objections"}

---

## Personalization Checklist

{chr(10).join([f'- [{x}] {x.get("element")} (Source: {x.get("source")})' for x in strategy.get('personalization_elements', [])]) if strategy.get('personalization_elements') else '- Standard demo'}

---

## Next Steps

{chr(10).join([f'- {ns}' for ns in strategy.get('next_steps', [])])}

---

## Research Context

**Industry:** {research.get('industry', 'Unknown')}
**Tech Stack:** {', '.join(list(research.get('tech_stack', {}).keys())[:5]) if research.get('tech_stack') else 'Unknown'}
**Competitors:** {', '.join(competitors[:3]) if competitors else 'None'}

---

*Dynamic demo strategy updated every 60 seconds based on latest intelligence.*
"""

    def _generate_tech_talking_points(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate technical talking points for SE."""
        research = data.get('research', {})
        tech_stack = data.get('tech_stack', {})
        competitors = list(data['competitors'])
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)

        points = f"""# Technical Talking Points - {account_name}

**Prepared:** {today} | {identity.full_display}

---

## Current Tech Stack (Inferred)

"""
        if tech_stack:
            for tool, category in tech_stack.items():
                points += f"- {tool} ({category})\n"
        else:
            points += "- Not yet identified. Research in progress.\n"

        points += f"""

## Key Differentiators vs Competitors

"""
        for comp in competitors[:3]:
            points += f"""### vs {comp}

- **Integration:** Our unified platform vs {comp} point solutions
- **AI:** Freddy embedded vs {comp} add-on or none
- **Deployment:** Weeks vs months
- **TCO:** 30% lower 3-year cost

"""
        points += """## Technical Discovery Questions

1. What's your current integration landscape?
2. How many vendors do you manage today?
3. What's your total annual spend on customer service tools?
4. What's your implementation timeline?
5. How do you handle AI/ML today?

## Risk Mitigation Talking Points

- Unified platform reduces vendor sprawl and security exposure
- Built-in AI means no additional licensing
- Fast deployment minimizes project risk
- Multi-tenancy reduces maintenance overhead

---

*Update these talking points as you learn more about their environment.*
"""
        return points

    def _generate_demo_script(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate a demo script with narrative."""
        research = data.get('research', {})
        strategy = data.get('strategy', {})
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)

        script = f"""# Demo Script - {account_name}

**Prepared:** {today} | {identity.full_display}

---

## Opening (2 minutes)

*"I've been reading about {research.get('industry', 'your industry')} and the challenges {research.get('priorities', ['operational efficiency'])[0] if research.get('priorities') else 'teams like yours'} face. Today I'm going to show you how [Customer Similar to You] achieved [Specific Outcome] in just [Timeframe]."*

---

## Discovery Recap (5 minutes)

**Script:** "Based on our conversations, I understand you're focused on:"

- {research.get('priorities', ['Improving customer experience'])[0] if research.get('priorities') else 'Customer experience improvement'}
- {research.get('priorities', ['Operational efficiency'])[1] if len(research.get('priorities', [])) > 1 else 'Cost reduction'}
- {research.get('priorities', ['Scalability'])[2] if len(research.get('priorities', [])) > 2 else 'Scalability'}

**Questions to ask:**
- "Can you walk me through your current escalation process?"
- "What's your biggest bottleneck in handling volume spikes?"

---

## Platform Overview (10 minutes)

**Narrative:** "What if you could have one platform that does it all..."

**Key slides to personalize:**
1. Unified architecture diagram (emphasize single vendor)
2. AI-native foundation (Freddy explanation)
3. Deployment timeline (weeks, not months)

---

## Competitive Positioning (5 minutes)

**Trap-setting:** "Some vendors you're probably evaluating take a different approach..."

| Area | Our Platform | Competitor |
|------|-----------|------------|
| AI | Built-in | Add-on or none |
| Deployment | Weeks | Months |
| TCO | 30% lower | Higher |

---

## ROI Story (7 minutes)

**Calculation:** "Based on your size (~{research.get('k10_metrics', {}).get('employee_count', '500')} employees), here's your 3-year TCO..."

- License savings: $X
- Implementation savings: $Y
- Productivity gains: $Z
- **Total: $TOTAL**

---

## Closing (3 minutes)

**Ask:** "What's the one thing that would make this an easy yes for you?"

**Next steps proposal:**
1. Technical deep dive with your team
2. Pilot program (30-day trial)
3. Contract and legal review

---

*Customize this script before each demo. Use actual customer names and specific outcomes.*
"""
        return script
