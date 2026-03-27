#!/usr/bin/env python3
"""Tech Utilities Skill - Email Assist, RFP Helper, Objection Crusher with real-time research."""

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
from jarvis.llm.llm_client import LLMManager
from jarvis.services.research_service import DynamicResearchService


class TechUtilitiesSkill:
    """AI-powered technical communications: email, RFP, objections with live research."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.tech_utilities")
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
        self.logger.info("Starting tech utilities skill")
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
        self.logger.info("Skill started - tech utilities active")

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

    def _on_discovery_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 10))
            )

    def _on_risk_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 5))
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
                return parts[-2] if parts[-1] in ('index.json', 'notes.json', 'activities.jsonl', 'summary.md', 'deals', 'discovery', 'tech_utilities') else parts[-1]
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
        await self._update_tech_utilities(account_name)

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
                        await self._update_tech_utilities(account_dir.name)

    async def _update_tech_utilities(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_account_data(account_folder)
            if not data:
                return

            # Create tech_utilities folder
            utils_dir = account_folder / "tech_utilities"
            utils_dir.mkdir(exist_ok=True)

            # Generate Email Assist
            email_content = await self._generate_email_assist(account_name, data)
            (utils_dir / "email_assist.md").write_text(email_content, encoding='utf-8')

            # Generate RFP Helper
            rfp_content = await self._generate_rfp_helper(account_name, data)
            (utils_dir / "rfp_responses.md").write_text(rfp_content, encoding='utf-8')

            # Generate Objection Crusher
            objection_content = await self._generate_objection_crusher(account_name, data)
            (utils_dir / "objection_handling.md").write_text(objection_content, encoding='utf-8')

            self.logger.info("Updated tech utilities", account=account_name)
            self.event_bus.publish(Event("tech_utilities.updated", "skill.tech_utilities", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update tech utilities", account=account_name, error=str(e))

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
        data.update(all_skill_data)  # merge in all other skill outputs

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

            # Research competitors
            for competitor in list(data['competitors'])[:3]:
                comp_data = await self.research_service.research_competitor(competitor)
                data['competitors_research'] = data.get('competitors_research', {})
                data['competitors_research'][competitor] = comp_data

            # Get YourCompany product pricing
            product = data['deals'][0].get('product') if data['deals'] else 'AcmeDesk'
            fw_pricing = await self.research_service.get_ACME_capabilities(product)
            data['ACME_pricing'] = fw_pricing

        except Exception as e:
            self.logger.debug("Research enrichment failed", error=str(e))

    def _sanitize_name(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_').lower()

    def _is_valid_account_folder(self, folder: Path) -> bool:
        has_smartness = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    # === GENERATION METHODS ===

    async def _generate_email_assist(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate context-aware email templates with real-time research."""
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        research = data.get('research', {})
        comp_research = data.get('competitors_research', {})

        context_prompt = f"""
Account: {account_name}
Industry: {research.get('industry', 'Unknown')}
Company Priorities: {', '.join(research.get('priorities', [])[:3])}
Current Tool: {data['deals'][0].get('current_systems', {}).get('ticket_system', 'Unknown') if data['deals'] else 'Unknown'}
Competitors: {', '.join(data['competitors'])}
Deal Stage: {data['deals'][0].get('stage', 'Unknown') if data['deals'] else 'Unknown'}

Recent Conversations:
{chr(10).join([c.get('insights', {}).get('summary', '')[:200] for c in data['conversations'][:3]])}

Risk Assessment Summary:
{data.get('risk_assessment', '')[:300] if data.get('risk_assessment') else 'N/A'}
"""

        if self.llm:
            try:
                response = await self.llm.generate([
                    Message(role="system", content=f"""You are {identity.full_display}, a Solution Engineer at YourCompany.
Generate email templates for technical communication. Include real-time research context.

Output JSON with:
{{
  "email_types": {{
    "follow_up": {{"subject": "...", "body": "...", "personalization_notes": "..."}},
    "proposal": {{"subject": "...", "body": "...", "attachments": ["..."]}},
    "objection_response": {{"subject": "...", "body": "...", "counter_points": ["..."]}},
    "executive_intro": {{"subject": "...", "body": "...", "value_prop": "..."}}
  }},
  "research_citations": ["URL1", "URL2"],
  "personalization_hooks": ["Hook1", "Hook2"]
}}"""),
                    Message(role="user", content=context_prompt)
                ])
                content = response.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                email_data = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM email generation failed", error=str(e))
                email_data = self._fallback_email_templates(data)
        else:
            email_data = self._fallback_email_templates(data)

        # Build markdown output
        return self._format_email_assist(account_name, identity, today, email_data, research, comp_research)

    def _fallback_email_templates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based email templates when LLM unavailable."""
        company = data['account_name'].split('::')[0]
        return {
            "email_types": {
                "follow_up": {
                    "subject": f"Following up on {company} YourCompany discussion",
                    "body": f"Hi [Name],\\n\\nFollowing up on our recent conversation about YourCompany for {company}.\\n\\nKey points we discussed:\\n- [Use case 1]\\n- [Use case 2]\\n\\nLet me know next steps.\\n\\nBest,\nSE",
                    "personalization_notes": "Add specific use cases from discovery"
                },
                "proposal": {
                    "subject": f"Proposal: YourCompany Solution for {company}",
                    "body": f"Dear [Executive],\\n\\nAttached is our proposal for implementing YourCompany at {company}.\\n\\nHighlights:\\n- [Benefit 1]\\n- [Benefit 2]\\n\\nWe look forward to discussing further.\\n\\nRegards,\nSE",
                    "attachments": ["Proposal.pdf", "ROI_Calculator.xlsx"]
                }
            },
            "research_citations": [],
            "personalization_hooks": [f"Mention {company}'s industry focus", "Reference recent conversation"]
        }

    def _format_email_assist(self, account_name: str, identity, today: str, email_data: Dict[str, Any], research: Dict, comp_research: Dict) -> str:
        content = f"""# Email Assist - {account_name}

**Generated:** {today} | **Owner:** {identity.full_display}

---

## Quick Templates

### 1. Follow-Up Email
**Subject:** {email_data.get('email_types', {}).get('follow_up', {}).get('subject', 'Follow-up')}

{email_data.get('email_types', {}).get('follow_up', {}).get('body', '')}

**Personalization Notes:**
{chr(10).join([f'- {note}' for note in email_data.get('personalization_hooks', [])])}

---

### 2. Proposal Email
**Subject:** {email_data.get('email_types', {}).get('proposal', {}).get('subject', 'Proposal')}

{email_data.get('email_types', {}).get('proposal', {}).get('body', '')}

**Attachments:** {', '.join(email_data.get('email_types', {}).get('proposal', {}).get('attachments', []))}

---

### 3. Objection Response
**Subject:** Re: {account_name} concerns

{email_data.get('email_types', {}).get('objection_response', {}).get('body', '')}

**Counter-Points:**
{chr(10).join([f'- {cp}' for cp in email_data.get('email_types', {}).get('objection_response', {}).get('counter_points', [])])}

---

### 4. Executive Intro
**Subject:** {email_data.get('email_types', {}).get('executive_intro', {}).get('subject', 'Executive Introduction')}

{email_data.get('email_types', {}).get('executive_intro', {}).get('body', '')}

**Value Proposition:** {email_data.get('email_types', {}).get('executive_intro', {}).get('value_prop', '')}

---

## 🔍 Research Context

**Company:** {research.get('company', account_name)}
**Industry:** {research.get('industry', 'Unknown')}
**Priorities:** {', '.join(research.get('priorities', [])[:3])}
**Competitors Analyzed:** {', '.join(comp_research.keys()) if comp_research else 'None'}

**Data Freshness:** {today}

---

## 📋 Linked Documents

- [Technical Risk Assessment](../TECHNICAL_RISK_ASSESSMENT.md)
- [Discovery Internal](./discovery/internal_discovery.md)
- [Q2A](./discovery/Q2A.md)

---

*Email templates dynamically generated with real-time research. Refresh before sending.*
"""
        return content

    async def _generate_rfp_helper(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate RFP responses with product capability lookup."""
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        research = data.get('research', {})
        fw_pricing = data.get('ACME_pricing', {})

        # Extract likely RFP questions from gaps and discovery
        rfp_questions = []
        gaps = data['notes'].get('knowledge_gaps', [])[:5]
        rfp_questions.extend(gaps)
        
        q2a_questions = []
        if data['discovery'].get('q2a'):
            q2a_content = data['discovery']['q2a']
            # Extract questions from Q2A markdown
            for line in q2a_content.split('\n'):
                if re.match(r'^\d+\.', line.strip()):
                    q2a_questions.append(line.strip())

        rfp_questions.extend(q2a_questions[:5])

        questions_markdown = "\n".join([f"- {q}" for q in rfp_questions]) if rfp_questions else "- No specific questions identified yet"

        if self.llm:
            try:
                prompt = f"""
Generate RFP response guidance for {account_name}.

Context:
- Industry: {research.get('industry', 'Unknown')}
- Product: {data['deals'][0].get('product', 'AcmeDesk') if data['deals'] else 'AcmeDesk'}
- Current Tool: {data['deals'][0].get('current_systems', {}).get('ticket_system', 'Unknown') if data['deals'] else 'Unknown'}
- Competitors: {', '.join(data['competitors'])}
- YourCompany Pricing: {json.dumps(fw_pricing, indent=2)}

Questions to address:
{chr(10).join(rfp_questions)}

For each question, provide:
- Recommended answer (aligned with current product capabilities)
- Supporting evidence/policies
- Differentiation vs competitors
- Compliance statements (SOC2, GDPR, etc.)
- References to similar customers

Output JSON:
{{
  "responses": [
    {{
      "question": "...",
      "answer": "...",
      "evidence": "...",
      "differentiation": "...",
      "compliance": ["SOC2", "GDPR", "HIPAA"],
      "customer_reference": "Similar company in same industry"
    }}
  ],
  "general_guidance": ["Always tie to Cost of Complexity savings", "Emphasize unified platform"],
  "compliance_matrix": {{"SOC2": "Yes", "GDPR": "Yes", "HIPAA": "Optional"}}
}}
"""
                response = await self.llm.generate([Message(role="user", content=prompt)])
                content = response.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                rfp_data = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM RFP generation failed", error=str(e))
                rfp_data = self._fallback_rfp_data(account_name, data)
        else:
            rfp_data = self._fallback_rfp_data(account_name, data)

        return self._format_rfp_helper(account_name, identity, today, rfp_data, research)

    def _fallback_rfp_data(self, account_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "responses": [
                {
                    "question": "What is your uptime SLA?",
                    "answer": "YourCompany provides 99.99% uptime SLA for enterprise customers.",
                    "evidence": "SLA included in enterprise contract",
                    "differentiation": "Few competitors guarantee 99.99%; ours is backed by financial penalties",
                    "compliance": ["SOC2"],
                    "customer_reference": "Multiple enterprise customers"
                }
            ],
            "general_guidance": ["Always emphasize unified architecture", "Highlight AI-native platform"],
            "compliance_matrix": {"SOC2": "Yes", "GDPR": "Yes", "HIPAA": "Available"}
        }

    def _format_rfp_helper(self, account_name: str, identity, today: str, rfp_data: Dict[str, Any], research: Dict) -> str:
        responses_md = ""
        for resp in rfp_data.get('responses', []):
            responses_md += f"""#### Q: {resp.get('question', '')}
**A:** {resp.get('answer', '')}

**Evidence:** {resp.get('evidence', '')}
**Differentiation:** {resp.get('differentiation', '')}
**Compliance:** {', '.join(resp.get('compliance', []))}
**Reference:** {resp.get('customer_reference', '')}

---
"""

        return f"""# RFP Helper - {account_name}

**Generated:** {today} | **Owner:** {identity.full_display}

---

## Proposed RFP Responses

{responses_md}

## General Guidance

{chr(10).join([f'- {g}' for g in rfp_data.get('general_guidance', [])])}

## Compliance Matrix

| Standard | Status | Notes |
|----------|--------|-------|
| SOC 2 Type II | ✅ | Audit report available |
| GDPR | ✅ | Full compliance |
| HIPAA | {rfp_data.get('compliance_matrix', {}).get('HIPAA', '❓')} | Available with BAA |

---

*RFP guidance based on current product capabilities. Verify pricing in latest price book.*
"""

    async def _generate_objection_crusher(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate objection handling with competitive research."""
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)
        comp_research = data.get('competitors_research', {})
        research = data.get('research', {})

        # Extract objections from notes/gaps
        objections = data['notes'].get('knowledge_gaps', [])[:5]
        if not objections:
            objections = [
                "YourCompany is more expensive than Zendesk",
                "We're already using Salesforce Service Cloud",
                "We need enterprise-grade security",
                "What about AI capabilities compared to competitors?",
                "Implementation will take too long"
            ]

        if self.llm:
            try:
                prompt = f"""
Generate objection handling for {account_name}.

Competitor Research:
{json.dumps(comp_research, indent=2) if comp_research else 'No competitor research available'}

Company Context:
- Industry: {research.get('industry', 'Unknown')}
- Current Tool: {data['deals'][0].get('current_systems', {}).get('ticket_system', 'Unknown') if data['deals'] else 'Unknown'}

Objections to address:
{chr(10).join(objections)}

For each objection, provide:
- Empathy statement
- Evidence-based response (with sources)
- Competitive counter (specific to mentioned competitor)
- Proof point (customer case, metric)
- Challenger question

Output JSON:
{{
  "objections": [
    {{
      "objection": "...",
      "empathy": "...",
      "response": "...",
      "evidence": ["source1", "source2"],
      "competitive_counter": "...",
      "proof_point": "...",
      "challenger_question": "..."
    }}
  ],
  "strategy": "Overall approach (Attack/Defend/Reframe)"
}}
"""
                response = await self.llm.generate([Message(role="user", content=prompt)])
                content = response.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                objection_data = json.loads(content)
            except Exception as e:
                self.logger.debug("LLM objection generation failed", error=str(e))
                objection_data = self._fallback_objection_data()
        else:
            objection_data = self._fallback_objection_data()

        return self._format_objection_crusher(account_name, identity, today, objection_data, comp_research)

    def _fallback_objection_data(self) -> Dict[str, Any]:
        return {
            "objections": [
                {
                    "objection": "YourCompany is more expensive",
                    "empathy": "I understand cost is a concern",
                    "response": "YourCompany TCO is 20% lower over 3 years due to unified architecture and reduced admin overhead",
                    "evidence": ["Cost of Complexity whitepaper", "G2 TCO comparisons"],
                    "competitive_counter": "Zendesk appears cheaper but requires additional AI and integration modules",
                    "proof_point": "Customer X saved 30% in year 2",
                    "challenger_question": "Are you comparing license costs or total cost of ownership?"
                }
            ],
            "strategy": "Attack with TCO data"
        }

    def _format_objection_crusher(self, account_name: str, identity, today: str, objection_data: Dict[str, Any], comp_research: Dict) -> str:
        objections_md = ""
        for obj in objection_data.get('objections', []):
            objections_md += f"""### {obj.get('objection', '')}

**Empathy:** {obj.get('empathy', '')}

**Response:** {obj.get('response', '')}

**Evidence:**
{chr(10).join([f'- {e}' for e in obj.get('evidence', [])])}

**Competitive Counter:** {obj.get('competitive_counter', '')}

**Proof Point:** {obj.get('proof_point', '')}

**Challenger Question:** {obj.get('challenger_question', '')}

---
"""

        return f"""# Objection Crusher - {account_name}

**Generated:** {today} | **Owner:** {identity.full_display}
**Strategy:** {objection_data.get('strategy', 'Adaptive')}

---

{objections_md}

## Competitive Intelligence

{', '.join(comp_research.keys()) if comp_research else 'No competitor research available'}

---

*Objection responses based on current competitive positioning. Refresh research regularly.*
"""
