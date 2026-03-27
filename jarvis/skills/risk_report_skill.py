#!/usr/bin/env python3
"""Deal Risk Report Skill - Comprehensive risk assessment with real-time signals."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.data_aggregator import read_all_skill_data
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.identity import get_se_identity
from jarvis.llm.llm_client import LLMManager
from jarvis.services.research_service import DynamicResearchService


class DealRiskReportSkill:
    """Dynamic deal risk assessment with live company risk signals and financial health."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.risk_report")
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
        self.logger.info("Starting deal risk report skill")
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
        self.event_bus.subscribe("meddpicc.updated", self._on_meddpicc_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Skill started - Risk Report active")

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

    def _on_meddpicc_updated(self, event: Event):
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
        try:
            rel = path.resolve().relative_to(self.accounts_dir.resolve())
            parts = rel.parts
            if len(parts) >= 2:
                return parts[-2] if parts[-1] in ('index.json', 'notes.json', 'activities.jsonl', 'summary.md', 'deals', 'discovery', 'meddpicc', 'tech_utilities', 'battlecards', 'value_architecture', 'risk_reports', 'demo_strategy') else parts[-1]
            elif len(parts) == 1:
                return parts[0]
        except:
            pass
        return None

    async def _debounced_update(self, account_name: str, delay_seconds: int):
        now = datetime.now()
        last = self._last_updates.get(account_name)
        if last and (now - last).total_seconds() < delay_seconds:
            return
        self._last_updates[account_name] = now
        await self._update_risk_report(account_name)

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
                        await self._update_risk_report(account_dir.name)

    async def _update_risk_report(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_account_data(account_folder)
            if not data:
                return

            # Create risk_reports folder
            risk_dir = account_folder / "risk_reports"
            risk_dir.mkdir(exist_ok=True)

            # Generate comprehensive risk report
            report_content = await self._generate_risk_report(account_name, data)
            (risk_dir / "deal_risk_assessment.md").write_text(report_content, encoding='utf-8')

            self.logger.info("Updated Risk Report", account=account_name)
            self.event_bus.publish(Event("risk.report.updated", "skill.risk_report", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update Risk Report", account=account_name, error=str(e))

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
        """Add real-time research data and risk signals."""
        try:
            company = account_name.split('::')[0].strip()
            company_data = await self.research_service.research_company(company)
            data['research'] = company_data

            # Get risk signals
            risks = await self.research_service.check_company_risks(company)
            data['risk_signals'] = risks

            # Extract financial health indicators
            k10 = company_data.get('k10_metrics', {})
            if k10:
                data['financial_health'] = {
                    'revenue': k10.get('revenue', 0),
                    'growth_rate': k10.get('growth_rate', 0),
                    'profitability': k10.get('net_income', 0) / max(k10.get('revenue', 1), 1),
                    'debt_ratio': k10.get('total_debt', 0) / max(k10.get('total_assets', 1), 1)
                }

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
        """Parse MEDDPICC report for risk indicators."""
        # Simple parsing; could enhance with regex/NLP
        return {
            'win_probability': self._extract_win_prob(content),
            'risk_level': self._extract_risk_level(content)
        }

    def _extract_win_prob(self, text: str) -> str:
        if 'Win Probability' in text:
            # Extract percentage
            import re
            match = re.search(r'Win Probability:\s*(\d+)%', text)
            if match:
                return match.group(1) + '%'
        return 'Unknown'

    def _extract_risk_level(self, text: str) -> str:
        for level in ['Critical', 'High', 'Medium', 'Low']:
            if level in text:
                return level
        return 'Unknown'

    async def _generate_risk_report(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        research = data.get('research', {})
        meddpicc = data.get('meddpicc', {})
        risk_signals = data.get('risk_signals', [])
        financial_health = data.get('financial_health', {})
        deals = data.get('deals', [])
        discovery = data.get('discovery', {})

        # Build risk assessment prompt
        risk_prompt = f"""
        Conduct comprehensive deal risk assessment for {account_name}.

        Account Context:
        - Industry: {research.get('industry', 'Unknown')}
        - Company Size: {research.get('k10_metrics', {}).get('employee_count', 'Unknown')}
        - Financial Health: Revenue ${financial_health.get('revenue', 0):,.0f}, Growth: {financial_health.get('growth_rate', 0)}%, Profit Margin: {financial_health.get('profitability', 0)*100:.1f}%

        Risk Signals Detected:
        {json.dumps(risk_signals, indent=2) if risk_signals else 'None identified'}

        Current Deal:
        {json.dumps(deals[0] if deals else {}, indent=2)}

        MEDDPICC Health:
        - Win Probability: {meddpicc.get('win_probability', 'Unknown')}
        - Risk Level: {meddpicc.get('risk_level', 'Unknown')}

        Discovery Coverage:
        - Internal: {'Completed' if discovery.get('internal') else 'Missing'}
        - Final: {'Completed' if discovery.get('final') else 'Missing'}
        - Q2A: {'Completed' if discovery.get('q2a') else 'Missing'}

        Analyze and assign:
        1. Overall deal risk score (0-100)
        2. Risk category (Financial, Competitive, Deal Complexity, Stakeholder, Timing)
        3. Top 5 risk factors with likelihood and impact
        4. Mitigation strategies for each major risk
        5. Go/No-Go recommendation with conditions

        Return JSON:
        {{
          "overall_risk_score": 0-100,
          "risk_category": "Low/Medium/High/Critical",
          "win_probability_adjusted": "0-100%",
          "risk_factors": [
            {{
              "factor": "...",
              "category": "...",
              "likelihood": "High/Med/Low",
              "impact": "High/Med/Low",
              "evidence": "..."
            }}
          ],
          "mitigation_strategies": [
            {{
              "risk": "...",
              "action": "...",
              "owner": "...",
              "timeline": "..."
            }}
          ],
          "go_no_go": "Go/Conditional Go/No-Go",
          "conditions": ["...", "..."]
        }}
        """

        if self.llm:
            try:
                response = await self.llm.generate([
                    Message(role="system", content="You are a risk assessment expert. Output only JSON."),
                    Message(role="user", content=risk_prompt)
                ])
                content = response.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                risk_data = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM risk generation failed", error=str(e))
                risk_data = self._fallback_risk(data)
        else:
            risk_data = self._fallback_risk(data)

        return self._format_risk_report(account_name, identity, today, risk_data, research, risk_signals, financial_health)

    def _fallback_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "overall_risk_score": 40,
            "risk_category": "Medium",
            "win_probability_adjusted": "50%",
            "risk_factors": [
                {"factor": "Incomplete discovery", "category": "Deal Complexity", "likelihood": "Medium", "impact": "High", "evidence": "Discovery docs incomplete"}
            ],
            "mitigation_strategies": [
                {"risk": "Incomplete discovery", "action": "Complete discovery sessions", "owner": "SE", "timeline": "1 week"}
            ],
            "go_no_go": "Conditional Go",
            "conditions": ["Complete technical discovery", "Confirm economic buyer"]
        }

    def _format_risk_report(self, account_name: str, identity, today: str, risk_data: Dict[str, Any], research: Dict, risk_signals: List, financial_health: Dict) -> str:
        risk_factors_md = ""
        for rf in risk_data.get('risk_factors', []):
            likelihood_icon = "🔴" if rf.get('likelihood') == 'High' else "🟡" if rf.get('likelihood') == 'Med' else "🟢"
            impact_icon = "🔴" if rf.get('impact') == 'High' else "🟡" if rf.get('impact') == 'Med' else "🟢"
            risk_factors_md += f"- **{rf.get('factor')}** ({rf.get('category')})\n  - Likelihood: {likelihood_icon} {rf.get('likelihood')}\n  - Impact: {impact_icon} {rf.get('impact')}\n  - Evidence: {rf.get('evidence', 'N/A')}\n"

        mitigation_md = ""
        for m in risk_data.get('mitigation_strategies', []):
            mitigation_md += f"- **{m.get('risk')}**: {m.get('action')} (Owner: {m.get('owner')}, Due: {m.get('timeline')})\n"

        signals_md = "\n".join([f"- {s.get('type')}: {s.get('signal')}" for s in risk_signals]) if risk_signals else "- None"

        go_icon = "🟢" if risk_data.get('go_no_go') == 'Go' else "🟡" if 'Conditional' in risk_data.get('go_no_go', '') else "🔴"

        return f"""# Deal Risk Assessment - {account_name}

**Generated:** {today} | **Analyst:** {identity.full_display}

---

## Executive Summary

- **Overall Risk Score:** {risk_data.get('overall_risk_score', 0)}/100
- **Risk Category:** {risk_data.get('risk_category', 'Unknown')}
- **Adjusted Win Probability:** {risk_data.get('win_probability_adjusted', 'Unknown')}
- **Go/No-Go Recommendation:** {go_icon} {risk_data.get('go_no_go', 'Unknown')}

---

## Risk Factors

{risk_factors_md if risk_factors_md else "- No significant risk factors identified"}

---

## Mitigation Strategies

{mitigation_md if mitigation_md else "- Continue monitoring"}

---

## Conditions for Proceeding

{chr(10).join([f'- {c}' for c in risk_data.get('conditions', [])]) if risk_data.get('conditions') else '- No special conditions'}

---

## Real-Time Risk Signals

{signals_md}

---

## Financial Health Snapshot

- **Revenue:** ${financial_health.get('revenue', 0):,.0f}
- **Growth Rate:** {financial_health.get('growth_rate', 0)}%
- **Profit Margin:** {financial_health.get('profitability', 0)*100:.1f}%
- **Debt Ratio:** {financial_health.get('debt_ratio', 0):.2f}

---

## Research Context

**Company:** {research.get('company', account_name)}
**Industry:** {research.get('industry', 'Unknown')}
**Leadership:** {len(research.get('leadership', []))} executives profiled

---

*Report dynamically generated with real-time risk intelligence. Update frequency: every 60 seconds.*
"""
