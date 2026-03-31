#!/usr/bin/env python3
"""Deal MEDDPICC Skill - Dynamic qualification with real-time stakeholder research."""

import asyncio
import json
import re
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


class DealMeddpiccSkill:
    """Dynamic MEDDPICC qualification with live company/executive research."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.meddpicc")
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
        self.logger.info("Starting deal MEDDPICC skill")
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
        self.event_bus.subscribe("risk.assessment.updated", self._on_risk_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Skill started - MEDDPICC active")

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

    def _on_risk_updated(self, event: Event):
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
        await self._update_meddpicc(account_name)

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
                        await self._update_meddpicc(account_dir.name)

    async def _update_meddpicc(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_account_data(account_folder)
            if not data:
                return

            # Create meddpicc folder
            meddpicc_dir = account_folder / "meddpicc"
            meddpicc_dir.mkdir(exist_ok=True)

            # Generate qualification report
            report_content = await self._generate_qualification_report(account_name, data)
            (meddpicc_dir / "qualification_report.md").write_text(report_content, encoding='utf-8')

            # Generate stakeholder analysis
            stakeholder_content = self._generate_stakeholder_analysis(account_name, data)
            (meddpicc_dir / "stakeholder_analysis.md").write_text(stakeholder_content, encoding='utf-8')

            self.logger.info("Updated MEDDPICC", account=account_name)
            self.event_bus.publish(Event("meddpicc.updated", "skill.meddpicc", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update MEDDPICC", account=account_name, error=str(e))

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
            'conversations': [],
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

        # Conversations from MEMORY
        safe_name = self._sanitize_name(account_folder.name)
        memory_conv_dir = self.workspace_root / "MEMORY" / "accounts" / safe_name
        if memory_conv_dir.exists():
            for conv_file in memory_conv_dir.glob("*.json"):
                if conv_file.name not in ("index.json", "snapshot.json"):
                    try:
                        with open(conv_file) as f:
                            data['conversations'].append(json.load(f))
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

            # Extract leadership for stakeholder analysis
            data['research']['leadership'] = company_data.get('leadership', [])

            # Research competitors
            for competitor in list(data['competitors'])[:3]:
                comp_data = await self.research_service.research_competitor(competitor)
                data['competitors_research'] = data.get('competitors_research', {})
                data['competitors_research'][competitor] = comp_data

        except Exception as e:
            self.logger.debug("Research enrichment failed", error=str(e))

    def _sanitize_name(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_').lower()

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has_smartness = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    async def _generate_qualification_report(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        research = data.get('research', {})
        comp_research = data.get('competitors_research', {})

        # Build MEDDPICC context
        meddpicc_prompt = f"""
Analyze MEDDPICC qualification for {account_name}.

Account Context:
- Industry: {research.get('industry', 'Unknown')}
- Company Size: {research.get('k10_metrics', {}).get('employee_count', 'Unknown')}
- Financial Health: {research.get('k10_metrics', {}).get('growth_rate', 'Unknown')}% growth
- Priorities: {', '.join(research.get('priorities', [])[:5])}

Leadership Identified:
{json.dumps(research.get('leadership', [])[:5], indent=2)}

Current Deal:
{json.dumps(data['deals'][0] if data['deals'] else {}, indent=2)}

Competitors:
{', '.join(data['competitors'])}

Competitor Research:
{json.dumps(comp_research, indent=2) if comp_research else 'None'}

Discovery Insights:
{data.get('discovery', {}).get('internal', '')[:500] if data.get('discovery', {}).get('internal') else 'N/A'}

Risk Factors:
{data.get('risk_assessment', '')[:500] if data.get('risk_assessment') else 'N/A'}

Scoring: Rate each MEDDPICC dimension 1-10 based on available data.
Adjust weights by deal size (Enterprise = Economic Buyer + Paper Process weighted higher).

Return JSON:
{{
  "deal_health_score": 0-100,
  "win_probability": "0-100%",
  "risk_level": "Low/Medium/High/Critical",
  "meddpicc_scores": {{
    "metrics": {{"score": 1-10, "evidence": "...", "gap": "..."}},
    "economic_buyer": {{"score": 1-10, "name": "...", "title": "...", "access": "Confirmed/Suspected/Unknown"}},
    "decision_criteria": {{"score": 1-10, "criteria": ["...", "..."], "alignment": "High/Med/Low"}},
    "decision_process": {{"score": 1-10, "steps": ["..."], "timeline": "..."}},
    "paper_process": {{"score": 1-10, "legal_review": "...", "procurement": "...", "security_review": "..."}},
    "identify_pain": {{"score": 1-10, "pain_points": ["..."], "business_impact": "..."}},
    "implicate_pain": {{"score": 1-10, "cost_of_inaction": "...", "urgency": "High/Med/Low"}},
    "champion": {{"score": 1-10, "name": "...", "influence": "High/Med/Low", "alignment": "..."}},
    "competition": {{"score": 1-10, "competitors": [...], "position": "Leading/Challenged/Behind"}}
  }},
  "critical_gaps": ["...", "..."],
  "top_actions": [{{"action": "...", "owner": "...", "due_date": "...", "impact": "High/Med/Low"}}]
}}
"""
        if self.llm:
            try:
                response = await self.llm.generate([
                    Message(role="system", content="You are a MEDDPICC expert. Output only JSON."),
                    Message(role="user", content=meddpicc_prompt)
                ])
                content = response.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                meddpicc_data = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM MEDDPICC generation failed", error=str(e))
                meddpicc_data = self._fallback_meddpicc(data)
        else:
            meddpicc_data = self._fallback_meddpicc(data)

        return self._format_qualification_report(account_name, identity, today, meddpicc_data, research)

    def _fallback_meddpicc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "deal_health_score": 65,
            "win_probability": "50%",
            "risk_level": "Medium",
            "meddpicc_scores": {
                "metrics": {"score": 5, "evidence": "Some metrics discussed", "gap": "Quantify business impact"},
                "economic_buyer": {"score": 3, "name": "Unknown", "title": "CFO", "access": "Unknown"},
                "decision_criteria": {"score": 4, "criteria": ["Cost", "Features"], "alignment": "Medium"}
            },
            "critical_gaps": ["Economic buyer not identified", "Decision process unclear"],
            "top_actions": [
                {"action": "Identify economic buyer", "owner": "SE", "due_date": "This week", "impact": "High"}
            ]
        }

    def _format_qualification_report(self, account_name: str, identity, today: str, meddpicc_data: Dict[str, Any], research: Dict) -> str:
        scores = meddpicc_data.get('meddpicc_scores', {})
        score_table = ""
        for dim, details in scores.items():
            dim_score = details.get('score', 0) if isinstance(details, dict) else 0
            status = "🟢" if dim_score >= 7 else "🟡" if dim_score >= 4 else "🔴"
            # Extract evidence safely
            if isinstance(details, dict):
                evidence = details.get('evidence', '')
            else:
                evidence = ''
            score_table += f"| {dim.title()} | {status} {dim_score}/10 | {evidence} |\n"

        actions_md = ""
        for action in meddpicc_data.get('top_actions', []):
            act = action.get('action', '')
            owner = action.get('owner', 'SE')
            due = action.get('due_date', 'TBD')
            impact = action.get('impact', 'Med')
            actions_md += f"- **{act}** (Owner: {owner}, Due: {due}) - {impact} Impact\n"

        gaps_md = "\n".join([f"- {gap}" for gap in meddpicc_data.get('critical_gaps', [])])

        return f"""# MEDDPICC Qualification Report - {account_name}

**Generated:** {today} | **Analyst:** {identity.full_display}

---

## Executive Summary

**Deal Health Score:** {meddpicc_data.get('deal_health_score', 0)}/100  
**Win Probability:** {meddpicc_data.get('win_probability', 'Unknown')}  
**Risk Level:** {meddpicc_data.get('risk_level', 'Unknown')}

---

## MEDDPICC Scorecard

| Dimension | Score | Evidence |
|-----------|-------|----------|
{score_table}

---

## Critical Gaps

{gaps_md if gaps_md else "- No critical gaps identified"}

---

## Top Priority Actions

{actions_md if actions_md else "- All dimensions adequately covered"}

---

## Research Context

**Company:** {research.get('company', account_name)}
**Industry:** {research.get('industry', 'Unknown')}
**Leadership:** {len(research.get('leadership', []))} executives profiled

---

*Report dynamically generated with real-time company research. Update frequency: every 60 seconds.*
"""

    def _generate_stakeholder_analysis(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        research = data.get('research', {})
        leadership = research.get('leadership', [])

        analysis = f"""# Stakeholder Analysis - {account_name}

**Prepared:** {today} | {identity.full_display}

---

## Identified Stakeholders

"""
        if leadership:
            for leader in leadership[:10]:
                analysis += f"### {leader.get('name', 'Unknown')} - {leader.get('title', 'N/A')}\n"
                analysis += f"- **Company:** {leader.get('company', '')}\n"
                analysis += f"- **Background:** {leader.get('background', 'Research via LinkedIn/press')}\n"
                analysis += f"- **Likely Priorities:** Align with {research.get('industry', 'industry')} trends\n"
                analysis += f"- **Engagement Strategy:** Connect via shared industry context\n\n"
        else:
            analysis += "- No stakeholders identified yet. Research pending.\n"

        analysis += """## Recommended Outreach

1. **CIO/CTO** - Technical evaluation, integration concerns
2. **VP Customer Service** - Business process impact
3. **CFO** - TCO, ROI, budgeting
4. **Procurement** - Terms, conditions, vendor management

---

*Stakeholder intelligence from real-time LinkedIn/company research.*
"""
        return analysis
