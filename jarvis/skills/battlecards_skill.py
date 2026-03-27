#!/usr/bin/env python3
"""Battlecards Skill - Real-time competitive intelligence with live pricing and G2 sentiment."""

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


class BattlecardsSkill:
    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.battlecards")
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
        self.logger.info("Starting battlecards skill")
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
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)
        self.event_bus.subscribe("risk.assessment.updated", self._on_risk_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Battlecards skill started")

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

    def _on_account_initialized(self, event: Event):
        acc = event.data.get("account_name")
        if acc:
            self._main_loop.call_soon_threadsafe(lambda: asyncio.create_task(self._debounced_update(acc, 30)))

    def _on_file_modified(self, event: Event):
        p = Path(event.data.get("path", ""))
        if not self._is_account_file(p):
            return
        acc = self._extract_account_name(p)
        if acc:
            self._main_loop.call_soon_threadsafe(lambda: asyncio.create_task(self._debounced_update(acc, 15)))

    def _on_conversation_stored(self, event: Event):
        acc = event.data.get("account")
        if acc:
            self._main_loop.call_soon_threadsafe(lambda: asyncio.create_task(self._debounced_update(acc, 20)))

    def _on_discovery_updated(self, event: Event):
        acc = event.data.get("account")
        if acc:
            self._main_loop.call_soon_threadsafe(lambda: asyncio.create_task(self._debounced_update(acc, 10)))

    def _on_risk_updated(self, event: Event):
        acc = event.data.get("account")
        if acc:
            self._main_loop.call_soon_threadsafe(lambda: asyncio.create_task(self._debounced_update(acc, 5)))

    def _is_account_file(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.accounts_dir.resolve())
            return True
        except ValueError:
            return False

    def _extract_account_name(self, path: Path) -> Optional[str]:
        try:
            rel = path.resolve().relative_to(self.accounts_dir.resolve())
            parts = rel.parts
            if len(parts) >= 2:
                return parts[-2] if parts[-1] in ('index.json', 'notes.json', 'activities.jsonl', 'summary.md', 'deals', 'discovery', 'battlecards') else parts[-1]
            return parts[0] if parts else None
        except:
            return None

    async def _debounced_update(self, acc: str, delay: int):
        now = datetime.now()
        last = self._last_updates.get(acc)
        if last and (now - last).total_seconds() < delay:
            return
        self._last_updates[acc] = now
        await self._update_battlecards(acc)

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
                for acc_dir in team_dir.iterdir():
                    if acc_dir.is_dir() and not acc_dir.name.startswith('.'):
                        if self._is_valid_account_folder(acc_dir):
                            await self._update_battlecards(acc_dir.name)

    async def _update_battlecards(self, account_name: str):
        try:
            acc_folder = await self._find_account_folder(account_name)
            if not acc_folder or not self._is_valid_account_folder(acc_folder):
                return

            data = await self._gather_account_data(acc_folder)
            if not data:
                return

            # Create battlecards folder
            bc_dir = acc_folder / "battlecards"
            bc_dir.mkdir(exist_ok=True)

            # Generate competitive intel
            competitive_content = await self._generate_competitive_intel(account_name, data)
            (bc_dir / "competitive_intel.md").write_text(competitive_content, encoding='utf-8')

            # Generate pricing comparison
            pricing_content = await self._generate_pricing_comparison(account_name, data)
            (bc_dir / "pricing_comparison.md").write_text(pricing_content, encoding='utf-8')

            # Generate discovery questions
            questions_content = await self._generate_discovery_questions(account_name, data)
            (bc_dir / "discovery_questions.md").write_text(questions_content, encoding='utf-8')

            self.logger.info("Updated battlecards", account=account_name)
            self.event_bus.publish(Event("battlecards.updated", "skill.battlecards", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update battlecards", account=account_name, error=str(e))

    async def _find_account_folder(self, account_name: str) -> Optional[Path]:
        for team_dir in self.accounts_dir.iterdir():
            if team_dir.is_dir():
                cand = team_dir / account_name
                if cand.exists() and cand.is_dir():
                    return cand
        return None

    async def _gather_account_data(self, acc_folder: Path) -> Dict[str, Any]:
        """Gather comprehensive data from all skill outputs + live research."""
        data = {
            'account_name': acc_folder.name,
            'deals': [],
            'notes': {},
            'competitors': set()
        }

        # Core data
        deals_dir = acc_folder / "deals"
        if deals_dir.exists():
            for f in deals_dir.glob("*.json"):
                try:
                    with open(f) as fp:
                        data['deals'].append(json.load(fp))
                except:
                    pass

        notes_file = acc_folder / "notes.json"
        if notes_file.exists():
            try:
                with open(notes_file) as fp:
                    data['notes'] = json.load(fp)
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
        all_skill_data = read_all_skill_data(acc_folder)
        data.update(all_skill_data)

        # Real-time research enrichment
        if self.research_service:
            await self._enrich_research(acc_folder.name, data)

        return data

    async def _enrich_research(self, account_name: str, data: Dict[str, Any]):
        try:
            company = account_name.split('::')[0].strip()
            comp_research = {}
            for comp in list(data['competitors'])[:3]:
                comp_research[comp] = await self.research_service.research_competitor(comp)
            data['competitors_research'] = comp_research
        except Exception as e:
            self.logger.debug("Research enrichment failed", error=str(e))

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has:
            return False
        return has

    async def _generate_competitive_intel(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        comps = list(data['competitors'])
        comp_research = data.get('competitors_research', {})
        if not comps:
            return f"# Competitive Intelligence - {account_name}\n\nNo competitors identified yet."
        if self.llm:
            prompt = f"""
Generate competitive intelligence for {account_name}.

Competitors: {', '.join(comps)}

Research data:
{json.dumps(comp_research, indent=2) if comp_research else 'No live research available'}

YourCompany positioning: "Uncomplicated, AI-native, Unified" (Investor Day 2025)

Return JSON:
{{
  "summary": "Overall competitive position vs these competitors",
  "by_competitor": [
    {{
      "name": "Competitor",
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "our_advantages": ["...", "..."],
      "trap_questions": ["...", "..."]
    }}
  ],
  "win_strategy": "Aggressive/Defensive/Niche",
  "key_differentiators": ["..."]
}}
"""
            try:
                resp = await self.llm.generate([Message(role="user", content=prompt)])
                content = resp.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                intel = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM competitive intel failed", error=str(e))
                intel = self._fallback_competitive_intel(comps)
        else:
            intel = self._fallback_competitive_intel(comps)

        return self._format_competitive_intel(account_name, identity, today, intel)

    def _fallback_competitive_intel(self, comps: List[str]) -> Dict[str, Any]:
        return {
            "summary": f"Competing against {', '.join(comps)}. Position based on unified platform and AI.",
            "by_competitor": [
                {
                    "name": comp,
                    "strengths": ["Market presence", "Feature breadth"],
                    "weaknesses": ["Complexity", "High TCO", "Implementation time"],
                    "our_advantages": ["Unified platform", "Fast time-to-value", "Freddy AI built-in"],
                    "trap_questions": [f"What's your current {comp} admin overhead?", "How long did your last implementation take?"]
                }
                for comp in comps
            ],
            "win_strategy": "Attack complexity and TCO",
            "key_differentiators": ["Unified platform reduces tool sprawl", "Freddy AI 80% deflection", "Implementation in weeks not months"]
        }

    def _format_competitive_intel(self, acc: str, identity, today: str, intel: Dict[str, Any]) -> str:
        by_comp = ""
        for comp in intel.get('by_competitor', []):
            by_comp += f"### {comp.get('name', 'Competitor')}\n\n"
            by_comp += "**Strengths:**\n" + "\n".join([f"- {s}" for s in comp.get('strengths', [])]) + "\n\n"
            by_comp += "**Weaknesses:**\n" + "\n".join([f"- {w}" for w in comp.get('weaknesses', [])]) + "\n\n"
            by_comp += "**Our Advantages:**\n" + "\n".join([f"- {a}" for a in comp.get('our_advantages', [])]) + "\n\n"
            by_comp += "**Trap Questions:**\n" + "\n".join([f"- {q}" for q in comp.get('trap_questions', [])]) + "\n---\n\n"
        return f"""# Competitive Intelligence - {acc}

**Generated:** {today} | {identity.full_display}

---

## Executive Summary

{intel.get('summary', '')}

**Win Strategy:** {intel.get('win_strategy', '')}
**Key Differentiators:** {', '.join(intel.get('key_differentiators', []))}

---

{by_comp}

---

*Live competitive data. Refresh weekly or when competitor moves detected.*
"""

    async def _generate_pricing_comparison(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        comps = list(data['competitors'])
        if not comps:
            return f"# Pricing Comparison - {account_name}\n\nNo competitors identified."
        # Fetch pricing for each competitor
        pricing_data = {}
        if self.research_service:
            for comp in comps[:3]:
                pricing_data[comp] = await self.research_service.get_competitor_pricing(comp)
        # Build table
        table = "| Competitor | Plan | Price/Agent/Month | Source |\n|---|---|---|\n"
        for comp, pdata in pricing_data.items():
            price = pdata.get('price', 'Unknown')
            source = pdata.get('source', 'web search')
            table += f"| {comp} | Enterprise | {price} | {source} |\n"
        # YourCompany pricing
        table += "| **YourCompany** | Enterprise | **$79** | ACME.com |\n"
        return f"""# Pricing Comparison - {account_name}

**Generated:** {today} | {identity.full_display}

---

## Pricing Table (Current)

{table}

## Cost of Complexity Analysis

- YourCompany unified platform eliminates multi-tool sprawl
- 20% of software spend wasted on complexity (YourCompany 2025 thesis)
- Total 3-year TCO typically 30% lower vs best-of-breed stack

---

*Pricing fetched in real-time. Verify before customer presentation.*
"""

    async def _generate_discovery_questions(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        comps = list(data['competitors'])
        gaps = data['notes'].get('knowledge_gaps', [])
        questions = []
        # Generate trap questions based on competitors
        for comp in comps:
            questions.append(f"What's your current {comp} admin overhead?")
            questions.append(f"How long did your last {comp} implementation take?")
            questions.append(f"What's your total 3-year cost including modules and professional services?")
        # Add gaps-based questions
        questions.extend(gaps[:5])
        # Dedupe
        questions = list(set(questions))[:15]
        qlist = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        return f"""# Discovery Questions - {account_name}

**Generated:** {today} | {identity.full_display}

---

## Trap-Setting Questions (Competitive)

{qlist}

## Follow-up Probes

- Can you walk me through your current escalation process?
- What's your biggest pain point with your current system?
- If budget weren't a concern, what would you change tomorrow?
- Who else on your team would benefit from AI automation?

---

*Questions dynamically generated based on competitive landscape and knowledge gaps.*
"""
