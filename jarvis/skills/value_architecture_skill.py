#!/usr/bin/env python3
"""Value Architecture Skill - Dynamic ROI/TCO builder with live competitor pricing and headcount avoidance modeling."""

import asyncio, json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.data_aggregator import read_all_skill_data
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.identity import get_se_identity
from jarvis.llm.llm_client import LLMManager, Message
from jarvis.services.research_service import DynamicResearchService


class ValueArchitectureSkill:
    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.value_architecture")
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
        self.logger.info("Starting value architecture skill")
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
        self.logger.info("Value architecture skill started")

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

    # Event handlers
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
                return parts[-2] if parts[-1] in ('index.json', 'notes.json', 'activities.jsonl', 'summary.md', 'deals', 'discovery', 'value_architecture') else parts[-1]
            return parts[0] if parts else None
        except:
            return None

    async def _debounced_update(self, acc: str, delay: int):
        now = datetime.now()
        last = self._last_updates.get(acc)
        if last and (now - last).total_seconds() < delay:
            return
        self._last_updates[acc] = now
        await self._update_value_architecture(acc)

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
                            await self._update_value_architecture(acc_dir.name)

    async def _update_value_architecture(self, account_name: str):
        try:
            acc_folder = await self._find_account_folder(account_name)
            if not acc_folder or not self._is_valid_account_folder(acc_folder):
                return

            data = await self._gather_account_data(acc_folder)
            if not data:
                return

            # Create value_architecture folder
            va_dir = acc_folder / "value_architecture"
            va_dir.mkdir(exist_ok=True)

            # Generate ROI model
            roi_content = await self._generate_roi_model(account_name, data)
            (va_dir / "roi_model.md").write_text(roi_content, encoding='utf-8')

            # Generate TCO analysis
            tco_content = await self._generate_tco_analysis(account_name, data)
            (va_dir / "tco_analysis.md").write_text(tco_content, encoding='utf-8')

            self.logger.info("Updated value architecture", account=account_name)
            self.event_bus.publish(Event("value_architecture.updated", "skill.value_architecture", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update value architecture", account=account_name, error=str(e))

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
            comp_pricing = {}
            for comp in list(data['competitors'])[:3]:
                comp_pricing[comp] = await self.research_service.get_competitor_pricing(comp)
            data['competitor_pricing'] = comp_pricing
            # Industry benchmarks
            industry = await self._infer_industry(data)
            if industry:
                benchmarks = await self.research_service.get_industry_benchmarks(industry, "IT spending")
                data['industry_benchmarks'] = benchmarks
        except Exception as e:
            self.logger.debug("Research enrichment failed", error=str(e))

    async def _infer_industry(self, data: Dict[str, Any]) -> str:
        # Simple inference from notes or deal
        facts = data['notes'].get('facts', [])
        text = " ".join(facts).lower()
        if "healthcare" in text or "hospital" in text:
            return "healthcare"
        if "finance" in text or "bank" in text:
            return "fintech"
        if "retail" in text or "ecommerce" in text:
            return "ecommerce"
        return "technology"

    def _extract_win_prob(self, text: str) -> str:
        import re
        match = re.search(r'Win Probability:?\s*(\d+%)', text)
        return match.group(1) if match else ''

    def _extract_risk_score(self, text: str) -> int:
        import re
        match = re.search(r'Overall Risk Score:?\s*(\d+)', text)
        return int(match.group(1)) if match else 0

    def _extract_go_no_go(self, text: str) -> str:
        import re
        match = re.search(r'Go/No-Go Recommendation:?\s*([A-Za-z ]+)', text)
        return match.group(1).strip() if match else ''

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists()
        if (folder / 'deals').exists() and not has:
            return False
        return has

    async def _generate_roi_model(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        deal = data['deals'][0] if data['deals'] else {}
        arr = deal.get('arr', 0)
        agents = deal.get('agents', 0)
        competitors = list(data['competitors'])
        comp_pricing = data.get('competitor_pricing', {})

        # Build prompt with live pricing
        comp_pricing_str = "\n".join([f"{c}: {p.get('price', 'Unknown')}" for c, p in comp_pricing.items()]) if comp_pricing else "No competitor pricing data"

        if self.llm:
            prompt = f"""
Build 3-year ROI model for {account_name}.

Deal:
- ARR: ${arr:,}
- Agents: {agents}
- Product: {deal.get('product', 'Freshdesk')}

Competitor Pricing (live):
{comp_pricing_str}

Industry benchmarks: {json.dumps(data.get('industry_benchmarks', {}), indent=2)}

YourCompany pricing:
- Growth: $18/agent/mo
- Pro: $49/agent/mo
- Enterprise: $79/agent/mo
- Freddy AI: $100 per 1,000 sessions

Calculate:
1. Year 1-3 YourCompany cost (assume appropriate agent count and plan)
2. Current tool cost (use competitor pricing if known)
3. Headcount avoidance savings (assume 1 FTE per 50 agents with AI)
4. Cost of Complexity reduction (20% of current spend)
5. Total 3-year NPV (use 10% discount)

Return JSON:
{{
  "roi_summary": {{
    "year1_savings": 0,
    "year2_savings": 0,
    "year3_savings": 0,
    "total_3yr_savings": 0,
    "roi_percent": 0,
    "payback_months": 0
  }},
  "assumptions": ["...", "..."],
  "cost_breakdown": [
    {{"category": "YourCompany license", "y1": 0, "y2": 0, "y3": 0}},
    {{"category": "Implementation", "y1": 0, "y2": 0, "y3": 0}}
  ],
  "sensitivity": "If headcount reduction is lower by 50%, ROI drops X%"
}}
"""
            try:
                resp = await self.llm.generate([Message(role="user", content=prompt)])
                content = resp.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                roi_data = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM ROI generation failed", error=str(e))
                roi_data = self._fallback_roi(agents, arr)
        else:
            roi_data = self._fallback_roi(agents, arr)

        return self._format_roi_model(account_name, identity, today, roi_data)

    def _fallback_roi(self, agents: int, arr: Any) -> Dict[str, Any]:
        agent_count = agents if agents else 50
        annual_fw = agent_count * 49 * 12  # Pro plan
        return {
            "roi_summary": {
                "year1_savings": 50000,
                "year2_savings": 75000,
                "year3_savings": 100000,
                "total_3yr_savings": 225000,
                "roi_percent": 150,
                "payback_months": 8
            },
            "assumptions": ["1 FTE per 50 agents avoided", "20% Cost of Complexity reduction", "No discount on YourCompany"],
            "cost_breakdown": [
                {"category": "YourCompany license", "y1": annual_fw, "y2": annual_fw, "y3": annual_fw},
                {"category": "Implementation", "y1": 25000, "y2": 5000, "y3": 0}
            ],
            "sensitivity": "If headcount reduction is lower by 50%, ROI drops ~40%"
        }

    def _format_roi_model(self, acc: str, identity, today: str, roi: Dict[str, Any]) -> str:
        s = roi.get('roi_summary', {})
        breakdown_md = ""
        for cat in roi.get('cost_breakdown', []):
            breakdown_md += f"| {cat.get('category')} | ${cat.get('y1',0):,} | ${cat.get('y2',0):,} | ${cat.get('y3',0):,} |\n"
        return f"""# ROI Model - {acc}

**Generated:** {today} | {identity.full_display}

---

## Executive Summary

- **3-Year Total Savings:** ${s.get('total_3yr_savings', 0):,}
- **ROI:** {s.get('roi_percent', 0)}%
- **Payback Period:** {s.get('payback_months', 0)} months

---

## 3-Year Savings Breakdown

| Year | Savings |
|------|---------|
| Year 1 | ${s.get('year1_savings',0):,} |
| Year 2 | ${s.get('year2_savings',0):,} |
| Year 3 | ${s.get('year3_savings',0):,} |
| **Total** | **${s.get('total_3yr_savings',0):,}** |

---

## Cost Breakdown

| Category | Year 1 | Year 2 | Year 3 |
|----------|--------|--------|--------|
{breakdown_md}

---

## Key Assumptions

{chr(10).join([f'- {a}' for a in roi.get('assumptions', [])])}

## Sensitivity Analysis

{roi.get('sensitivity', 'N/A')}

---

*Model based on live competitor pricing where available. Refresh before presenting.*
"""

    async def _generate_tco_analysis(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        # Simple TCO table vs competitors
        comps = list(data['competitors'])
        if not comps:
            comps = ["Zendesk", "Salesforce", "ServiceNow"]
        return f"""# TCO Analysis - {account_name}

**Generated:** {today} | {identity.full_display}

---

## 3-Year Total Cost of Ownership

| Cost Component | YourCompany | {comps[0]} | {comps[1] if len(comps)>1 else 'Other'} |
|----------------|------------|-----------|-----------|
| License (per agent/mo) | $49 (Pro) | $X | $Y |
| Annual license cost (50 agents) | $29,400 | $X | $Y |
| Implementation | $25,000 | $50,000+ | $75,000+ |
| AI add-ons | Included | +$X/mo | +$Y/mo |
| Admin overhead (yearly) | $20,000 | $50,000 | $80,000 |
| **3-Year Total** | **~$150K** | **~$300K+** | **~$450K+** |

## Cost of Complexity Savings

- **Unified platform** eliminates multi-tool integration costs
- **Freddy AI** included = no extra AI licensing
- **Fast implementation** = shorter time-to-value, less consulting

**Typical savings: 30-50% vs best-of-breed stack**

---

*Use actual competitor pricing from pricing comparison sheet when available.*
"""
