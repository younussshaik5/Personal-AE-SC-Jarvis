#!/usr/bin/env python3
"""Account Dashboard Skill - Master CRM-style HTML view with export capabilities."""

import asyncio, json, re, os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.data_aggregator import read_all_skill_data
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.identity import get_professional_identity
from jarvis.services.research_service import DynamicResearchService
from jarvis.llm.llm_client import LLMManager, Message


class AccountDashboardSkill:
    """Generates comprehensive HTML dashboard for each account with export to PDF/Excel/PPT/Word."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.dashboard")
        self.workspace_root = Path(config_manager.config.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._last_updates: Dict[str, datetime] = {}
        self._update_interval = 60
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self.research_service: Optional[DynamicResearchService] = None
        self.llm_manager: Optional[LLMManager] = None

    async def start(self):
        self.logger.info("Starting account dashboard skill")
        self._running = True
        self._main_loop = asyncio.get_running_loop()
        try:
            self.research_service = DynamicResearchService(self.config_manager, None)
            await self.research_service.start()
        except Exception as e:
            self.logger.warning("Research service unavailable", error=str(e))

        # Initialize LLM manager for content formatting
        try:
            self.llm_manager = LLMManager(self.config_manager)
            await self.llm_manager.initialize()
        except Exception as e:
            self.logger.warning("LLM manager initialization failed", error=str(e))

        # Subscribe to all skill updates
        self.event_bus.subscribe("account.initialized", self._on_account_initialized)
        self.event_bus.subscribe("file.modified", self._on_file_modified)
        self.event_bus.subscribe("risk.assessment.updated", self._on_risk_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)
        self.event_bus.subscribe("meddpicc.updated", self._on_meddpicc_updated)
        self.event_bus.subscribe("battlecards.updated", self._on_battlecards_updated)
        self.event_bus.subscribe("value_architecture.updated", self._on_value_arch_updated)
        self.event_bus.subscribe("risk.report.updated", self._on_risk_report_updated)
        self.event_bus.subscribe("demo.strategy.updated", self._on_demo_strategy_updated)
        self.event_bus.subscribe("tech_utilities.updated", self._on_tech_utilities_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Skill started - Dashboard active")

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

    def _on_meddpicc_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    def _on_battlecards_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    def _on_value_arch_updated(self, event: Event):
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

    def _on_demo_strategy_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    def _on_tech_utilities_updated(self, event: Event):
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
                return parts[-2] if parts[-1] in ('index.json', 'notes.json', 'activities.jsonl', 'summary.md', 'deals', 'discovery', 'meddpicc', 'tech_utilities', 'battlecards', 'value_architecture', 'risk_reports', 'demo_strategy', 'DASHBOARD.html') else parts[-1]
            elif len(parts) == 1:
                return parts[0]
        except:
            pass
        return None

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has:
            return False
        return has

    async def _debounced_update(self, account_name: str, delay_seconds: int):
        now = datetime.now()
        last = self._last_updates.get(account_name)
        if last and (now - last).total_seconds() < delay_seconds:
            return
        self._last_updates[account_name] = now
        await self._update_dashboard(account_name)

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
                        await self._update_dashboard(account_dir.name)

    async def _update_dashboard(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_all_data(account_folder)
            if not data:
                return

            html_content = self._generate_html_dashboard(account_name, data)
            dashboard_file = account_folder / "DASHBOARD.html"
            dashboard_file.write_text(html_content, encoding='utf-8')

            self.logger.info("Updated Dashboard", account=account_name)

            # Generate individual opportunity dashboards
            deals_dir = account_folder / "deals"
            for deal in data.get('deals', []):
                try:
                    opportunity_name = deal.get('name') or deal.get('opportunity_name') or deal.get('title') or 'Untitled'
                    safe_name = "".join(c for c in opportunity_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                    safe_name = safe_name.replace(' ', '_')
                    opportunity_folder = deals_dir / safe_name
                    opportunity_folder.mkdir(parents=True, exist_ok=True)
                    
                    # Overlay opportunity-specific data
                    opp_data = data.copy()
                    opp_data['opportunity_name'] = opportunity_name
                    opp_data['opportunity_stage'] = deal.get('stage', '')
                    opp_data['opportunity_amount'] = deal.get('amount') or deal.get('value') or 0
                    opp_data['opportunity_close_date'] = deal.get('close_date') or deal.get('closeDate') or ''
                    opp_data['opportunity_owner'] = deal.get('owner') or deal.get('owner_name') or ''
                    opp_data['opportunity_description'] = deal.get('description') or ''
                    opp_data['deal_json'] = deal
                    
                    opp_html = self._generate_html_dashboard(account_name, opp_data)
                    opp_dashboard = opportunity_folder / "DASHBOARD.html"
                    opp_dashboard.write_text(opp_html, encoding='utf-8')
                except Exception as e:
                    self.logger.warning("Failed to generate opp dashboard", opp=opportunity_name, error=str(e))

        except Exception as e:
            self.logger.error("Failed to update Dashboard", account=account_name, error=str(e))

    async def _find_account_folder(self, account_name: str) -> Optional[Path]:
        for team_dir in self.accounts_dir.iterdir():
            if team_dir.is_dir():
                candidate = team_dir / account_name
                if candidate.exists() and candidate.is_dir():
                    return candidate
        return None

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has_smartness = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    async def _gather_all_data(self, account_folder: Path) -> Dict[str, Any]:
        data = {
            'account_name': account_folder.name,
            'generated_at': datetime.now().isoformat(),
            'summary': '',
            'summary_json': {},
            'deals': [],
            'notes': {},
            'risk_assessment': '',
            'risk_assessment_html': '',
            'risk_assessment_json': {},
            'discovery': {'internal': '', 'final': '', 'q2a': ''},
            'discovery_html': {'internal': '', 'final': '', 'q2a': ''},
            'discovery_json': {'internal': {}, 'final': {}, 'q2a': {}},
            'meddpicc': {'qualification': '', 'stakeholders': ''},
            'meddpicc_html': {'qualification': '', 'stakeholders': ''},
            'meddpicc_json': {'qualification': {}, 'stakeholders': {}},
            'tech_utilities': {'emails': '', 'objections': ''},
            'tech_utilities_html': {'emails': '', 'objections': ''},
            'tech_utilities_json': {'emails': {}, 'objections': {}},
            'battlecards': {'intel': '', 'pricing': '', 'questions': ''},
            'battlecards_html': {'intel': '', 'pricing': '', 'questions': ''},
            'battlecards_json': {'intel': {}, 'pricing': {}, 'questions': {}},
            'value_architecture': {'roi': '', 'tco': ''},
            'value_architecture_html': {'roi': '', 'tco': ''},
            'value_architecture_json': {'roi': {}, 'tco': {}},
            'risk_report': '',
            'risk_report_html': '',
            'risk_report_json': {},
            'demo_strategy': {'strategy': '', 'talking_points': '', 'script': ''},
            'demo_strategy_html': {'strategy': '', 'talking_points': '', 'script': ''},
            'demo_strategy_json': {'strategy': {}, 'talking_points': {}, 'script': {}},
            'research': {},
            'competitors': set()
        }

        # Core files
        summary_file = account_folder / "summary.md"
        if summary_file.exists():
            raw_summary = summary_file.read_text(encoding='utf-8')
            data['summary'] = raw_summary[:2000]
            data['summary_html'] = self._markdown_to_html(raw_summary)
            data['summary_json'] = {}

        deals_dir = account_folder / "deals"
        if deals_dir.exists():
            for deal_file in deals_dir.glob("*.json"):
                try:
                    with open(deal_file) as f:
                        data['deals'].append(json.load(f))
                except:
                    pass
        
        # If no deal files, check index.json for opportunity
        if not data['deals']:
            index_file = account_folder / "index.json"
            if index_file.exists():
                try:
                    with open(index_file) as f:
                        index = json.load(f)
                        if 'opportunity' in index:
                            opp = index['opportunity']
                            # Convert to deal format
                            deal = {
                                'name': opp.get('product', 'Opportunity'),
                                'stage': opp.get('stage', ''),
                                'amount': opp.get('value_estimate', 0),
                                'close_date': opp.get('close_date_estimate', ''),
                                'win_probability': opp.get('win_probability', ''),
                                'currency': opp.get('currency', 'USD')
                            }
                            data['deals'].append(deal)
                except:
                    pass

        # Generate HTML table for deals
        deals = data.get('deals', [])
        if deals:
            deals_html = '<table style="width:100%; border-collapse: collapse; font-size:14px;">'
            deals_html += '<thead><tr style="background:var(--gray-100);"><th style="text-align:left;padding:8px;">Opportunity</th><th style="text-align:left;padding:8px;">Stage</th><th style="text-align:right;padding:8px;">Amount</th><th style="text-align:left;padding:8px;">Close Date</th><th style="text-align:center;padding:8px;">Win %</th></tr></thead><tbody>'
            for deal in deals:
                name = deal.get('name') or deal.get('opportunity_name') or deal.get('title') or 'Unnamed'
                stage = deal.get('stage', '')
                amount = deal.get('amount') or deal.get('value') or 0
                close_date = deal.get('close_date') or deal.get('closeDate') or ''
                win_prob = deal.get('win_probability') or deal.get('win_prob') or deal.get('probability') or ''
                try:
                    amount_val = float(amount)
                    amount_str = f'${amount_val:,.0f}'
                except:
                    amount_str = str(amount)
                deals_html += f'<tr><td style="padding:8px;border-bottom:1px solid var(--gray-200);">{name}</td><td style="padding:8px;border-bottom:1px solid var(--gray-200);">{stage}</td><td style="text-align:right;padding:8px;border-bottom:1px solid var(--gray-200);">{amount_str}</td><td style="padding:8px;border-bottom:1px solid var(--gray-200);">{close_date}</td><td style="text-align:center;padding:8px;border-bottom:1px solid var(--gray-200);">{win_prob}</td></tr>'
            deals_html += '</tbody></table>'
            data['deals_html'] = deals_html
        else:
            data['deals_html'] = '<p style="color:var(--gray-500);padding:8px;">No opportunities found.</p>'
        notes_file = account_folder / "notes.json"
        if notes_file.exists():
            try:
                with open(notes_file) as f:
                    data['notes'] = json.load(f)
            except:
                pass

        # Generate individual opportunity dashboards
        deals_dir = account_folder / "deals"
        for deal in data.get('deals', []):
            try:
                # Create opportunity-specific dashboard
                opportunity_name = deal.get('name') or deal.get('opportunity_name') or deal.get('title') or 'Untitled'
                # Sanitize name for folder
                safe_name = "".join(c for c in opportunity_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                safe_name = safe_name.replace(' ', '_')
                opportunity_folder = deals_dir / safe_name
                opportunity_folder.mkdir(parents=True, exist_ok=True)
                
                # Use the same aggregated data but overlay this specific deal's info
                opp_data = data.copy()
                opp_data['opportunity_name'] = opportunity_name
                opp_data['opportunity_stage'] = deal.get('stage', '')
                opp_data['opportunity_amount'] = deal.get('amount') or deal.get('value') or 0
                opp_data['opportunity_close_date'] = deal.get('close_date') or deal.get('closeDate') or ''
                opp_data['opportunity_owner'] = deal.get('owner') or deal.get('owner_name') or ''
                opp_data['opportunity_description'] = deal.get('description') or ''
                opp_data['deal_json'] = deal
                
                opp_html = self._generate_html_dashboard(account_name, opp_data)
                opp_dashboard = opportunity_folder / "DASHBOARD.html"
                opp_dashboard.write_text(opp_html, encoding='utf-8')
            except Exception as e:
                self.logger.warning("Failed to generate dashboard for opportunity", opp=opportunity_name, error=str(e))

        # Technical Risk Assessment
        risk_file = account_folder / "TECHNICAL_RISK_ASSESSMENT.md"
        if risk_file.exists():
            raw_risk = risk_file.read_text(encoding='utf-8')
            data['risk_assessment'] = raw_risk[:2000]
            data['risk_assessment_html'] = self._markdown_to_html(raw_risk)
            data['risk_assessment_json'] = {}

        # Discovery
        discovery_dir = account_folder / "discovery"
        if discovery_dir.exists():
            for doc in ['internal_discovery.md', 'final_discovery.md', 'Q2A.md']:
                fpath = discovery_dir / doc
                if fpath.exists():
                    key = doc.replace('.md', '')
                    raw_content = fpath.read_text(encoding='utf-8')
                    data['discovery'][key] = raw_content[:1500]
                    data['discovery_html'][key] = self._markdown_to_html(raw_content)
                    data['discovery_json'][key] = {}

        # MEDDPICC
        meddpicc_dir = account_folder / "meddpicc"
        if meddpicc_dir.exists():
            qual = meddpicc_dir / "qualification_report.md"
            if qual.exists():
                raw_qual = qual.read_text(encoding='utf-8')
                data['meddpicc']['qualification'] = raw_qual[:2000]
                data['meddpicc_html']['qualification'] = self._markdown_to_html(raw_qual)
                data['meddpicc_json']['qualification'] = {}
            stakeholders = meddpicc_dir / "stakeholder_analysis.md"
            if stakeholders.exists():
                raw_stake = stakeholders.read_text(encoding='utf-8')
                data['meddpicc']['stakeholders'] = raw_stake[:1500]
                data['meddpicc_html']['stakeholders'] = self._markdown_to_html(raw_stake)
                data['meddpicc_json']['stakeholders'] = {}

        # Tech Utilities
        utils_dir = account_folder / "tech_utilities"
        if utils_dir.exists():
            email_gen = utils_dir / "email_generation.md"
            if email_gen.exists():
                raw_email = email_gen.read_text(encoding='utf-8')
                data['tech_utilities']['emails'] = raw_email[:1500]
                data['tech_utilities_html']['emails'] = self._markdown_to_html(raw_email)
                data['tech_utilities_json']['emails'] = {}
            objections = utils_dir / "objection_handling.md"
            if objections.exists():
                raw_objection = objections.read_text(encoding='utf-8')
                data['tech_utilities']['objections'] = raw_objection[:1500]
                data['tech_utilities_html']['objections'] = self._markdown_to_html(raw_objection)
                data['tech_utilities_json']['objections'] = {}

        # Battlecards
        bc_dir = account_folder / "battlecards"
        if bc_dir.exists():
            intel = bc_dir / "competitive_intel.md"
            if intel.exists():
                raw_intel = intel.read_text(encoding='utf-8')
                data['battlecards']['intel'] = raw_intel[:2000]
                data['battlecards_html']['intel'] = self._markdown_to_html(raw_intel)
                data['battlecards_json']['intel'] = {}
            pricing = bc_dir / "pricing_comparison.md"
            if pricing.exists():
                raw_pricing = pricing.read_text(encoding='utf-8')
                data['battlecards']['pricing'] = raw_pricing[:1500]
                data['battlecards_html']['pricing'] = self._markdown_to_html(raw_pricing)
                data['battlecards_json']['pricing'] = {}
            questions = bc_dir / "discovery_questions.md"
            if questions.exists():
                raw_questions = questions.read_text(encoding='utf-8')
                data['battlecards']['questions'] = raw_questions[:1500]
                data['battlecards_html']['questions'] = self._markdown_to_html(raw_questions)
                data['battlecards_json']['questions'] = {}

        # Value Architecture
        va_dir = account_folder / "value_architecture"
        if va_dir.exists():
            roi = va_dir / "roi_model.md"
            if roi.exists():
                raw_roi = roi.read_text(encoding='utf-8')
                data['value_architecture']['roi'] = raw_roi[:2000]
                data['value_architecture_html']['roi'] = self._markdown_to_html(raw_roi)
                data['value_architecture_json']['roi'] = {}
            tco = va_dir / "tco_analysis.md"
            if tco.exists():
                raw_tco = tco.read_text(encoding='utf-8')
                data['value_architecture']['tco'] = raw_tco[:2000]
                data['value_architecture_html']['tco'] = self._markdown_to_html(raw_tco)
                data['value_architecture_json']['tco'] = {}

        # Risk Report
        risk_report_dir = account_folder / "risk_reports"
        if risk_report_dir.exists():
            risk_rpt = risk_report_dir / "deal_risk_assessment.md"
            if risk_rpt.exists():
                raw_risk_report = risk_rpt.read_text(encoding='utf-8')
                data['risk_report'] = raw_risk_report[:2000]
                data['risk_report_html'] = self._markdown_to_html(raw_risk_report)
                data['risk_report_json'] = {}

        # Demo Strategy
        demo_dir = account_folder / "demo_strategy"
        if demo_dir.exists():
            strategy = demo_dir / "demo_strategy.md"
            if strategy.exists():
                raw_strategy = strategy.read_text(encoding='utf-8')
                data['demo_strategy']['strategy'] = raw_strategy[:2000]
                data['demo_strategy_html']['strategy'] = self._markdown_to_html(raw_strategy)
                data['demo_strategy_json']['strategy'] = {}
            talking = demo_dir / "tech_talking_points.md"
            if talking.exists():
                raw_talking = talking.read_text(encoding='utf-8')
                data['demo_strategy']['talking_points'] = raw_talking[:1500]
                data['demo_strategy_html']['talking_points'] = self._markdown_to_html(raw_talking)
                data['demo_strategy_json']['talking_points'] = {}
            script = demo_dir / "demo_script.md"
            if script.exists():
                raw_script = script.read_text(encoding='utf-8')
                data['demo_strategy']['script'] = raw_script[:2000]
                data['demo_strategy_html']['script'] = self._markdown_to_html(raw_script)
                data['demo_strategy_json']['script'] = {}

        # Extract deal info and competitors
        for deal in data['deals']:
            data['competitors'].update(deal.get('competitors', []))
        facts = data['notes'].get('facts', [])
        for fact in facts:
            if 'competitor' in fact.lower():
                data['competitors'].add(fact)

        # Enrich with research if available
        if self.research_service:
            try:
                company = account_folder.name.split('::')[0].strip()
                company_data = await self.research_service.research_company(company)
                data['research'] = company_data
            except:
                pass

        return data

    async def _gather_opportunity_data(self, account_folder: Path, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all data for a specific opportunity, including opportunity-specific context."""
        data = await self._gather_all_data(account_folder)
        
        # Overlay opportunity-specific details
        data['opportunity_name'] = deal_data.get('name') or deal_data.get('opportunity_name') or deal_data.get('title', 'Unknown Opportunity')
        data['opportunity_stage'] = deal_data.get('stage', '')
        data['opportunity_amount'] = deal_data.get('amount') or deal_data.get('value') or 0
        data['opportunity_close_date'] = deal_data.get('close_date') or deal_data.get('closeDate') or ''
        data['opportunity_owner'] = deal_data.get('owner') or deal_data.get('owner_name') or ''
        data['opportunity_description'] = deal_data.get('description') or deal_data.get('description', '')[:500]
        data['deal_json'] = deal_data
        
        return data

    async def _llm_format(self, title: str, content: str) -> str:
        """Use LLM to convert markdown content into concise HTML for dashboard sections."""
        if not content:
            return ''
        system_msg = f"You are an assistant that converts the following markdown into clean, concise HTML suitable for a dashboard section titled '{title}'. Preserve headings, lists, tables, and links. Use inline styles matching the dashboard's CSS variables where appropriate. Return only an HTML fragment (no <html> wrapper)."
        messages = [Message(role='system', content=system_msg), Message(role='user', content=content)]
        try:
            result = await self.llm_manager.generate(messages)
            return result.strip()
        except Exception as e:
            self.logger.warning('LLM formatting failed', title=title, error=str(e))
            # Fallback to simple markdown conversion
            return self._markdown_to_html(content)

    async def _llm_structure(self, title: str, content: str) -> dict:
        """Use LLM to extract structured JSON from markdown."""
        if not content:
            return {}
        system_msg = f"You are a data extraction assistant. Extract the key information from the markdown document titled '{title}'. Return a JSON object with appropriate keys (use lists for repeated items, nested objects where needed). Do not add any explanatory text, only valid JSON."
        messages = [Message(role='system', content=system_msg), Message(role='user', content=content)]
        try:
            result = await self.llm_manager.generate(messages)
            result = result.strip()
            if result.startswith('```json'):
                result = result.split('```json')[1].split('```')[0].strip()
            elif result.startswith('```'):
                result = result.split('```')[1].split('```')[0].strip()
            if not result.startswith('{'):
                import re
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    result = match.group()
            return json.loads(result)
        except Exception as e:
            self.logger.warning('LLM structuring failed', title=title, error=str(e))
            return {}

    def _json_to_html(self, obj):
        """Render a JSON object as HTML (tables/lists)."""
        if isinstance(obj, dict):
            rows = ''
            for k, v in obj.items():
                rows += f'<tr><td style="font-weight:600; vertical-align:top;">{k}</td><td>{self._json_to_html(v)}</td></tr>'
            return f'<table class="comp-table">{rows}</table>'
        if isinstance(obj, list):
            if all(isinstance(i, dict) for i in obj):
                headers = obj[0].keys()
                header_html = ''.join(f'<th>{h}</th>' for h in headers)
                rows_html = ''
                for item in obj:
                    row = ''.join(f'<td>{self._json_to_html(item[h])}</td>' for h in headers)
                    rows_html += f'<tr>{row}</tr>'
                return f'<table class="comp-table"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>'
            else:
                items_html = ''.join(f'<li>{self._json_to_html(i)}</li>' for i in obj)
                return f'<ul>{items_html}</ul>'
        return str(obj)

    def _render_json_section(self, title, content, section_id=None):
        """Render a section as a widget. Shows HTML content or JSON tables."""
        if not content:
            return ''
        # If content looks like HTML, render it directly
        if isinstance(content, str) and content.startswith('<'):
            html_body = content
        else:
            html_body = self._json_to_html(content)
        id_attr = f' id="{section_id}"' if section_id else ''
        return f'''<div class="widget"{id_attr}>
            <div class="widget-header"><span class="widget-title">{title}</span></div>
            <div class="widget-body">{html_body}</div>
        </div>'''

    def _generate_html_dashboard(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate premium single-column article-style dashboard."""
        identity = get_professional_identity(self.config_manager)
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        parsed = self._parse_all_data(data)
        
        # Build deals table
        deals = data.get('deals', [])
        deals_rows = []
        for deal in deals:
            name = deal.get('name') or deal.get('opportunity_name') or deal.get('title') or 'Untitled'
            stage = deal.get('stage', '')
            amount = deal.get('amount') or deal.get('value') or 0
            close_date = deal.get('close_date') or deal.get('closeDate') or ''
            win_prob = deal.get('win_probability') or deal.get('win_prob') or ''
            try:
                amount_str = f'${float(amount):,.0f}'
            except:
                amount_str = str(amount)
            deals_rows.append(f'<tr><td style="padding:14px 16px;border-bottom:1px solid #e2e8f0;font-weight:500;color:#334155;">{name}</td><td style="padding:14px 16px;border-bottom:1px solid #e2e8f0;"><span style="background:#dbeafe;color:#1d4ed8;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;">{stage}</span></td><td style="padding:14px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;color:#111827;text-align:right;">{amount_str}</td><td style="padding:14px 16px;border-bottom:1px solid #e2e8f0;color:#475569;">{close_date}</td><td style="padding:14px 16px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#059669;text-align:center;">{win_prob}</td></tr>')
        deals_table = '<table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f8fafc;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;font-weight:600;"><th style="text-align:left;padding:14px 16px;border-bottom:2px solid #e2e8f0;">Opportunity</th><th style="text-align:left;padding:14px 16px;border-bottom:2px solid #e2e8f0;">Stage</th><th style="text-align:right;padding:14px 16px;border-bottom:2px solid #e2e8f0;">Amount</th><th style="text-align:left;padding:14px 16px;border-bottom:2px solid #e2e8f0;">Close Date</th><th style="text-align:center;padding:14px 16px;border-bottom:2px solid #e2e8f0;">Win %</th></tr></thead><tbody>' + ''.join(deals_rows) + '</tbody></table>' if deals_rows else '<div style="padding:60px 20px;text-align:center;color:#94a3b8;background:#f8fafc;border-radius:12px;border:2px dashed #e2e8f0;">No opportunities tracked yet</div>'
        
        # Sections to include
        sections = [
            ('summary', '📄 Account Summary', 'summary_html'),
            ('risk', '⚠️ Technical Risk Assessment', 'risk_assessment_html'),
            ('discovery-internal', '🔍 Internal Discovery', 'discovery_html', 'internal_discovery'),
            ('discovery-final', '🎯 Final Discovery', 'discovery_html', 'final_discovery'),
            ('discovery-q2a', '❓ Q2A Discovery', 'discovery_html', 'Q2A'),
            ('meddpicc-qualification', '📊 MEDDPICC Qualification', 'meddpicc_html', 'qualification'),
            ('meddpicc-stakeholders', '👥 MEDDPICC Stakeholder Analysis', 'meddpicc_html', 'stakeholders'),
            ('bc-intel', '🕵️ Competitive Intelligence', 'battlecards_html', 'intel'),
            ('bc-pricing', '💵 Pricing Comparison', 'battlecards_html', 'pricing'),
            ('bc-questions', '💬 Discovery Questions', 'battlecards_html', 'questions'),
            ('value-roi', '📈 ROI Model', 'value_architecture_html', 'roi'),
            ('value-tco', '💸 TCO Analysis', 'value_architecture_html', 'tco'),
            ('risk-report', '📋 Deal Risk Assessment', 'risk_report_html'),
            ('demo-strategy', '🎤 Demo Strategy', 'demo_strategy_html', 'strategy'),
            ('demo-talking', '🗣️ Demo Talking Points', 'demo_strategy_html', 'talking_points'),
            ('demo-script', '📝 Demo Script', 'demo_strategy_html', 'script'),
            ('tech-emails', '📧 Email Generation', 'tech_utilities_html', 'emails'),
            ('tech-objections', '🛡️ Objection Handling', 'tech_utilities_html', 'objections'),
        ]
        
        # Collect sections with actual content
        sections_content = []
        for section in sections:
            section_id, title, source_key = section[0], section[1], section[2]
            subkey = section[3] if len(section) > 3 else None
            
            if subkey:
                content = data.get(source_key, {}).get(subkey, '')
            else:
                content = data.get(source_key, '')
            
            if content and content.strip() and not content.strip().startswith('<div class="section-empty">'):
                sections_content.append((section_id, title, content))
        
        # Build HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">')
        html_parts.append(f'<title>{account_name} | JARVIS Intelligence</title>')
        html_parts.append('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">')
        html_parts.append('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
        html_parts.append('<style>')
        html_parts.append(':root{--primary:#2563eb;--success:#10b981;--warning:#f59e0b;--danger:#ef4444;--bg:#f8fafc;--card:#ffffff;--text:#1e293b;--muted:#64748b;--border:#e2e8f0;}')
        html_parts.append('body{font-family:Inter,-apple-system,sans-serif;margin:0;padding:0;background:var(--bg);color:var(--text);line-height:1.7;-webkit-font-smoothing:antialiased;}')
        html_parts.append('.container{max-width:900px;margin:0 auto;padding:0 20px;}')
        html_parts.append('.hero{background:linear-gradient(135deg,#1e293b 0%,#334155 100%);color:white;padding:60px 0;margin-bottom:40px;}')
        html_parts.append('.hero h1{font-size:32px;font-weight:800;margin:0 0 8px 0;letter-spacing:-0.5px;}')
        html_parts.append('.hero p{font-size:16px;opacity:0.9;margin:0;}')
        html_parts.append('.kpi-bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:0 20px 40px;}')
        html_parts.append('.kpi{background:white;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08);text-align:center;}')
        html_parts.append('.kpi-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;font-weight:600;}')
        html_parts.append('.kpi-value{font-size:24px;font-weight:800;color:var(--text);}')
        html_parts.append('.card{background:white;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:40px;overflow:hidden;}')
        html_parts.append('.card-header{background:#f8fafc;padding:20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;}')
        html_parts.append('.card-title{font-size:18px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:10px;margin:0;}')
        html_parts.append('.card-body{padding:28px;font-size:15px;line-height:1.75;}')
        html_parts.append('.card-body h1,.card-body h2,.card-body h3,.card-body h4{margin:28px 0 14px;color:var(--text);font-weight:700;}')
        html_parts.append('.card-body h1{font-size:26px;}')
        html_parts.append('.card-body h2{font-size:22px;padding-bottom:10px;border-bottom:2px solid var(--border);}')
        html_parts.append('.card-body h3{font-size:18px;}')
        html_parts.append('.card-body p{margin-bottom:18px;}')
        html_parts.append('.card-body ul,.card-body ol{margin:18px 0;padding-left:28px;}')
        html_parts.append('.card-body li{margin-bottom:10px;}')
        html_parts.append('.card-body table{width:100%;border-collapse:collapse;margin:20px 0;}')
        html_parts.append('.card-body th,.card-body td{padding:12px 16px;text-align:left;border-bottom:1px solid var(--border);}')
        html_parts.append('.card-body th{background:#f8fafc;font-weight:600;color:#475569;}')
        html_parts.append('.card-body img{max-width:100%;height:auto;border-radius:8px;}')
        html_parts.append('.btn{background:var(--primary);color:white;border:none;padding:8px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:6px;transition:all 0.2s;}')
        html_parts.append('.btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(37,99,235,0.3);}')
        html_parts.append('@media(max-width:768px){.kpi-bar{grid-template-columns:repeat(2,1fr);}.hero{padding:40px 0;}.hero h1{font-size:24px;}.card-body{padding:20px;}}')
        html_parts.append('</style></head><body>')
        
        # Hero
        html_parts.append(f'<div class="hero"><div class="container"><h1>{account_name}</h1><p>AI-Generated Account Intelligence - Auto-refresh: 60s</p></div></div>')
        
        # KPI bar
        kpis = [
            ('Win Probability', parsed.get('win_prob', '--')),
            ('Deal Risk', f"{parsed.get('risk_score', 50)}/100"),
            ('Competitors', str(len(parsed.get('competitors', [])))),
            ('Pipeline', f"${parsed.get('pipeline_value', '0')}M"),
            ('Discovery', f"{parsed.get('discovery_pct', 0)}%"),
        ]
        html_parts.append('<div class="kpi-bar">')
        for label, value in kpis:
            html_parts.append(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>')
        html_parts.append('</div>')
        
        # Opportunities table
        html_parts.append(f'<div class="card" style="margin:0 20px 40px;"><div class="card-header"><h2 class="card-title">📋 Opportunities</h2><span class="badge badge-info">{len(deals)} active</span></div><div class="card-body" style="padding:0;overflow-x:auto;">{deals_table}</div></div>')
        
        # Sections with export buttons
        for section_id, title, content in sections_content:
            html_parts.append(f'<div class="card" id="{section_id}" style="margin:0 20px 40px;"><div class="card-header"><h2 class="card-title">{title}</h2><button class="btn" onclick="exportSection(\'{section_id}\', \'pdf\')">PDF</button><button class="btn" onclick="exportSection(\'{section_id}\', \'word\')">Word</button><button class="btn" onclick="exportSection(\'{section_id}\', \'excel\')">Excel</button></div><div class="card-body article-content">{content}</div></div>')
        
        # Footer
        html_parts.append(f'<div style="text-align:center;padding:40px 20px;color:var(--muted);font-size:12px;"><div style="font-weight:600;margin-bottom:8px;">JARVIS Intelligence Platform</div><div>Auto-generated • {len(sections_content)} intelligence modules • Professional: {identity.full_display} • Last: {today}</div></div>')
        
        # JavaScript
        html_parts.append('<script>')
        html_parts.append('document.querySelectorAll("a[href^=\"#\"]").forEach(a=>a.addEventListener("click",e=>{e.preventDefault();const t=document.querySelector(a.getAttribute("href"));if(t){t.scrollIntoView({behavior:"smooth",block:"start"});}}));')
        html_parts.append('function exportSection(sectionId, format) {')
        html_parts.append('const section = document.getElementById(sectionId);')
        html_parts.append('if (!section) return;')
        html_parts.append('const content = section.querySelector(".article-content") || section;')
        html_parts.append('const title = section.querySelector("h2")?.textContent || sectionId;')
        html_parts.append('const filename = `${document.title.split("|")[0].trim()}_${sectionId}_${new Date().toISOString().slice(0,10)}`;')
        html_parts.append('if (format === "pdf") {')
        html_parts.append('const opt = {margin:1,filename:filename+".pdf",image:{type:"jpeg",quality:0.98},html2canvas:{scale:2},jsPDF:{unit:"in",format:"letter",orientation:"portrait"}};')
        html_parts.append('html2pdf().set(opt).from(content).save();')
        html_parts.append('} else if (format === "word") {')
        html_parts.append('const html = `<html><head><meta charset="UTF-8"><title>${title}</title></head><body style="font-family:Inter,sans-serif;padding:20px;">${content.innerHTML}</body></html>`;')
        html_parts.append('const blob = new Blob([html],{type:"text/html"});')
        html_parts.append('saveAs(blob, filename+".doc");')
        html_parts.append('} else if (format === "excel") {')
        html_parts.append('const ws = XLSX.utils.json_to_sheet({title: title, content: content.innerText});')
        html_parts.append('const wb = XLSX.utils.book_new();')
        html_parts.append('XLSX.utils.book_append_sheet(wb, ws, "Section");')
        html_parts.append('XLSX.writeFile(wb, filename+".xlsx");')
        html_parts.append('}')
        html_parts.append('}')
        html_parts.append('</script></body></html>')
        
        return ''.join(html_parts)



    def _parse_all_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured insights from all skill outputs."""
        parsed = {
            'company': data.get('account_name', 'Unknown'),
            'opportunity_name': data.get('opportunity_name', ''),
            'opportunity_stage': data.get('opportunity_stage', ''),
            'opportunity_amount': data.get('opportunity_amount', 0),
            'opportunity_close_date': data.get('opportunity_close_date', ''),
            'opportunity_owner': data.get('opportunity_owner', ''),
            'opportunity_description': data.get('opportunity_description', ''),
            'industry': 'Unknown',
            'employee_count': 'Unknown',
            'growth_rate': 'Unknown',
            'win_prob': None,
            'win_prob_color': '#6b7280',
            'win_prob_trend': 'neutral',
            'risk_score': 50,
            'risk_category': 'Unknown',
            'risk_trend': 'stable',
            'top_risk': 'None',
            'competitors': list(data.get('competitors', [])),
            'primary_competitor': 'None',
            'deal_count': len(data.get('deals', [])),
            'pipeline_value': '0',
            'weighted_pipeline': '0',
            'discovery_pct': 0,
            'discovery_completed': 0,
            'internal_disc': False,
            'final_disc': False,
            'q2a_disc': False,
            'radar_data': [5]*8,
            'risk_factors': [],
            'activities': [],
            'next_action': 'No upcoming actions',
            'next_action_date': '',
            'comp_data': {},
        }
        
        # Extract research data
        research = data.get('research', {})
        if research:
            parsed['industry'] = research.get('industry', 'Unknown')
            k10 = research.get('k10_metrics', {})
            if k10:
                parsed['employee_count'] = k10.get('employee_count', 'Unknown')
                parsed['growth_rate'] = k10.get('growth_rate', 'Unknown')
        
        # Extract MEDDPICC scores
        meddpicc = data.get('meddpicc', {})
        if isinstance(meddpicc, dict):
            qual_text = meddpicc.get('qualification', '')
            if qual_text:
                prob = self._extract_win_prob(qual_text)
                if prob:
                    parsed['win_prob'] = prob
                    try:
                        num_str = ''.join(filter(str.isdigit, prob.split('%')[0]))
                        num = int(num_str) if num_str else 50
                        parsed['win_prob_color'] = self._score_color(num, 30, 60)
                    except (ValueError, IndexError):
                        parsed['win_prob'] = None
                # Extract radar data from MEDDPICC text (simple extraction)
                radar_scores = self._extract_meddpicc_scores(qual_text)
                if radar_scores:
                    parsed['radar_data'] = radar_scores
        
        # Extract Risk Report
        risk_report = data.get('risk_report', '')
        if risk_report:
            score = self._extract_risk_score(risk_report)
            if score:
                parsed['risk_score'] = score
                parsed['risk_category'] = self._extract_risk_category(risk_report) or 'Medium'
                # Extract top risk factor
                parsed['top_risk'] = self._extract_top_risk(risk_report)
        
        # Extract Value Architecture for pipeline value
        va = data.get('value_architecture', {})
        if isinstance(va, dict):
            roi_text = va.get('roi', '')
            if roi_text:
                parsed['pipeline_value'] = self._extract_dollar_value(roi_text)
        
        # Calculate discovery completion
        discovery = data.get('discovery', {})
        if isinstance(discovery, dict):
            internal = discovery.get('internal_discovery', '')
            final = discovery.get('final_discovery', '')
            q2a = discovery.get('Q2A', '')
            parsed['internal_disc'] = bool(internal and len(str(internal)) > 50)
            parsed['final_disc'] = bool(final and len(str(final)) > 50)
            parsed['q2a_disc'] = bool(q2a and len(str(q2a)) > 50)
            completed = sum([parsed['internal_disc'], parsed['final_disc'], parsed['q2a_disc']])
            parsed['discovery_completed'] = completed
            parsed['discovery_pct'] = int(completed / 3 * 100)
        
        # Get activities timeline
        conversations = data.get('conversations', [])
        if conversations:
            parsed['activities'] = self._format_activities(conversations[:10])
        
        # Primary competitor
        if parsed['competitors']:
            parsed['primary_competitor'] = parsed['competitors'][0]
            parsed['comp_data'] = {
                c: {'threat_level': 'High' if i == 0 else 'Medium'}
                for i, c in enumerate(parsed['competitors'][:3])
            }
        
        return parsed

    def _extract_win_prob(self, text: str) -> Optional[str]:
        """Extract win probability percentage from MEDDPICC text."""
        import re
        patterns = [
            r'win probability[:\s]+(\d+%)',
            r'win prob[:\s]+(\d+%)',
            r'probability[:\s]+(\d+%)',
            r'qualification score[:\s]+(\d+%)',
            r'score[:\s]+(\d+%)',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_meddpicc_scores(self, text: str) -> List[int]:
        """Extract numeric MEDDPICC dimension scores (1-10 scale)."""
        # Simple regex to find score patterns like "Metrics: 8/10" or "Score: 7"
        import re
        scores = []
        patterns = [
            r'Metrics:?\s*(\d+)',
            r'Economic Buyer:?\s*(\d+)',
            r'Decision Criteria:?\s*(\d+)',
            r'Paper Process:?\s*(\d+)',
            r'Identify Pain:?\s*(\d+)',
            r'Champion:?\s*(\d+)',
            r'Competition:?\s*(\d+)',
            r'Risk:?\s*(\d+)'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            scores.append(int(match.group(1)) if match else 5)
        return scores[:8] if len(scores) >= 8 else [5]*8
    
    def _extract_top_risk(self, text: str) -> str:
        """Extract the top mentioned risk factor."""
        import re
        # Look for "Top risks:" or numbered list items
        match = re.search(r'Top risks?:(.+?)(?:\n\n|\n\d\.)', text, re.DOTALL | re.IGNORECASE)
        if match:
            risk = match.group(1).strip()[:50]
            return risk + ('...' if len(risk) >= 50 else '')
        return 'Review full risk report'
    
    def _extract_dollar_value(self, text: str) -> str:
        """Extract dollar amount from text like $2.5M or 3.2 million."""
        import re
        match = re.search(r'\$?\s*(\d+(?:\.\d+)?)\s*(?:M|million|Million)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        # Try to find ROI percentage and calculate estimate
        match2 = re.search(r'(\d+)%\s*ROI', text, re.IGNORECASE)
        if match2:
            return f"ROI {match2.group(1)}%"
        return 'TBD'
    
    def _activity_timeline(self, activities: List) -> str:
        """Render activities as timeline - wrapper for backward compatibility."""
        if not activities:
            return '<div class="timeline-item"><div class="timeline-dot"></div><div class="timeline-text">No recent activities</div></div>'
        if isinstance(activities, str):
            return activities
        items = []
        for act in activities[:5]:
            if isinstance(act, dict):
                summary = act.get('summary', act.get('text', ''))
                date = act.get('timestamp', '')[:10] if act.get('timestamp') else 'Recent'
                items.append(f'<div class="timeline-item"><div class="timeline-dot"></div><div class="timeline-date">{date}</div><div class="timeline-text">{summary[:100]}</div></div>')
        return ''.join(items) if items else '<div class="timeline-item"><div class="timeline-dot"></div><div class="timeline-text">No recent activities</div></div>'
    
    def _format_activities(self, conversations: List[Dict]) -> str:
        """Format conversation snippets as timeline items."""
        items = []
        for conv in conversations[:5]:
            summary = conv.get('summary', conv.get('insights', {}).get('summary', ''))
            if summary:
                date = conv.get('timestamp', '')[:10] if conv.get('timestamp') else 'Recent'
                items.append(f'<div class="timeline-item"><div class="timeline-dot"></div><div class="timeline-date">{date}</div><div class="timeline-text">{summary[:100]}...</div></div>')
        return ''.join(items) if items else '<div class="timeline-item"><div class="timeline-dot"></div><div class="timeline-text">No recent activities</div></div>'
    
    def _competitor_chips(self, competitors: List[str]) -> str:
        """Render competitor chips with initials."""
        html = ''
        for c in competitors[:3]:
            initial = c[0].upper() if c else '?'
            html += f'<div class="meta-chip" style="margin-right: 6px; margin-bottom: 6px; display: inline-flex; align-items: center; gap: 6px; background: var(--gray-200);"><span style="width: 20px; height: 20px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600;">{initial}</span>{c}</div>'
        return html
    
    def _competitor_table(self, competitors: List[str], comp_data: Dict) -> str:
        """Build competitor comparison table."""
        if not competitors:
            return '<div class="empty-state">No competitors identified</div>'
        
        rows = ''
        for comp in competitors[:5]:
            data = comp_data.get(comp, {})
            threat = data.get('threat_level', 'Medium')
            win_rate_class = 'win-med' if threat == 'Medium' else 'win-low' if threat == 'High' else 'win-high'
            win_rate_text = threat
            rows += f'''
            <tr>
                <td><strong>{comp}</strong></td>
                <td><span class="win-rate {win_rate_class}">{win_rate_text}</span></td>
                <td>Displacing</td>
                <td>YourCompany advantage in unified platform</td>
            </tr>
            '''
        
        return f'''
        <table class="comp-table">
            <thead>
                <tr>
                    <th>Competitor</th>
                    <th>Threat Level</th>
                    <th>Position</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        '''
    
    def _risk_breakdown_chart(self, risk_factors: List[Dict]) -> str:
        """Bar chart for risk factors."""
        if not risk_factors:
            return '<div class="empty-state">No risk factors parsed</div>'
        
        # Simple HTML bar chart
        html = '<div style="display: flex; flex-direction: column; gap: 12px;">'
        for rf in risk_factors[:5]:
            factor = rf.get('factor', 'Unknown')
            impact = rf.get('impact', 'Medium')
            score = 8 if impact == 'High' else 5 if impact == 'Medium' else 2
            color = 'var(--danger)' if impact == 'High' else 'var(--warning)' if impact == 'Medium' else 'var(--gray-300)'
            html += f'''
            <div style="display: grid; grid-template-columns: 1fr 80px; gap: 12px; align-items: center;">
                <div style="font-size: 13px; color: var(--gray-700);">{factor}</div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="flex: 1; height: 8px; background: var(--gray-200); border-radius: 4px; overflow: hidden;">
                        <div style="width: {score*10}%; height: 100%; background: {color}; border-radius: 4px;"></div>
                    </div>
                    <span style="font-size: 12px; font-weight: 600; color: var(--gray-600); width: 40px; text-align: right;">{score}/10</span>
                </div>
            </div>
            '''
        html += '</div>'
        return html
    
    def _insights_panel(self, parsed: Dict) -> str:
        """Generate AI-style insights based on parsed data."""
        insights = []
        
        # Win probability insight
        win_prob = parsed.get('win_prob')
        if win_prob:
            num = int(''.join(filter(str.isdigit, win_prob.split('%')[0])))
            if num < 40:
                insights.append({'icon': '🔴', 'text': f'Win probability low ({win_prob}). Focus on MEDDPICC gaps.'})
            elif num > 70:
                insights.append({'icon': '🟢', 'text': f'Strong win probability ({win_prob}). Push to close.'})
            else:
                insights.append({'icon': '🟡', 'text': f'Moderate win probability ({win_prob}). Improve discovery.'})
        
        # Risk insight
        risk_score = parsed.get('risk_score', 50)
        if risk_score > 70:
            insights.append({'icon': '⚠️', 'text': f'High risk score ({risk_score}/100). Mitigation plan required.'})
        
        # Discovery insight
        disc_pct = parsed.get('discovery_pct', 0)
        if disc_pct < 50:
            insights.append({'icon': '📝', 'text': f'Discovery incomplete ({disc_pct}%). Schedule follow-up sessions.'})
        
        # Competitor insight
        comp_count = len(parsed.get('competitors', []))
        if comp_count > 3:
            insights.append({'icon': '⚔️', 'text': f'{comp_count} competitors detected. Differentiation critical.'})
        
        if not insights:
            insights.append({'icon': '✅', 'text': 'All systems green. Proceed with standard playbook.'})
        
        html = ''
        for i in insights[:5]:
            html += f'''
            <div class="insight-card" style="margin-bottom: 12px; padding: 12px; border-radius: var(--radius-sm); background: var(--gray-50); border-left: 3px solid var(--primary);">
                <div style="display: flex; align-items: flex-start; gap: 10px;">
                    <span style="font-size: 18px;">{i['icon']}</span>
                    <span style="font-size: 13px; color: var(--gray-700);">{i['text']}</span>
                </div>
            </div>
            '''
        return html
    
    def _score_color(self, score: int, medium_thresh: int = 4, high_thresh: int = 7) -> str:
        """Return color class for score."""
        if score >= high_thresh:
            return 'var(--success)'
        elif score >= medium_thresh:
            return 'var(--warning)'
        else:
            return 'var(--danger)'
    
    def _risk_widget_class(self, risk_score: int) -> str:
        """Return widget class based on risk."""
        if risk_score > 70:
            return 'danger'
        elif risk_score > 40:
            return 'warning'
        else:
            return 'success'
    
    def _trend_icon(self, trend: str) -> str:
        """Return trend arrow icon."""
        if trend == 'up':
            return '↗️'
        elif trend == 'down':
            return '↘️'
        else:
            return '→'
    
    def _html_snippet(self, text: str, max_len: int = 800) -> str:
        """Convert markdown-like text to HTML snippet with better formatting."""
        if not text or text.strip().startswith('Not'):
            return f"<em style='color: var(--gray-400);'>{text}</em>"
        html = self._markdown_to_html(text[:max_len])
        return html
    
    def _markdown_to_html(self, text: str) -> str:
        """Simple markdown to HTML converter."""
        import re
        # Escape HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Headers
        text = re.sub(r'^### (.+)$', r'<h3 style="margin: 16px 0 8px; color: var(--gray-900); font-size: 15px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2 style="margin: 20px 0 12px; color: var(--gray-900); font-size: 17px;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h1 style="margin: 24px 0 16px; color: var(--gray-900); font-size: 20px;">\1</h1>', text, flags=re.MULTILINE)
        # Lists
        text = re.sub(r'^- (.+)$', r'<li style="margin-left: 16px; padding-left: 8px; margin-bottom: 4px;">\1</li>', text, flags=re.MULTILINE)
        # Tables (simple)
        text = re.sub(r'\|(.+)\|', lambda m: '<tr>' + ''.join(f'<td>{c.strip()}</td>' for c in m.group(1).split('|')) + '</tr>', text)
        # Line breaks
        text = text.replace('\n\n', '</p><p style="margin: 12px 0;">')
        return f'<p style="margin: 0;">{text}</p>'

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has_smartness = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    def _extract_risk_score(self, text: str) -> int:
        if not text:
            return 0
        import re
        match = re.search(r'Overall Risk Score:?\s*(\d+)', text, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def _extract_risk_category(self, text: str) -> str:
        if not text:
            return ''
        import re
        for level in ['Critical', 'High', 'Medium', 'Low']:
            if re.search(rf'Risk Category:?\s*{level}', text, re.IGNORECASE):
                return level
            # Also check for "Risk Level"
            if re.search(rf'Risk Level:?\s*{level}', text, re.IGNORECASE):
                return level
        return ''
