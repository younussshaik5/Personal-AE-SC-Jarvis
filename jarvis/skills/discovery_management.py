#!/usr/bin/env python3
"""Discovery Management Skill - Auto-generate discovery documents per account."""

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


class DiscoveryManagementSkill:
    """Generates and maintains discovery documents for each account."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.discovery")
        self.workspace_root = Path(config_manager.config.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._last_updates: Dict[str, datetime] = {}
        self._update_interval = 60
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.llm: Optional[LLMManager] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self):
        self.logger.info("Starting discovery management skill")
        self._running = True
        self._main_loop = asyncio.get_running_loop()

        try:
            self.llm = LLMManager(self.config_manager)
            await self.llm.initialize()
        except Exception as e:
            self.logger.warning("LLM not available for discovery synthesis", error=str(e))
            self.llm = None

        self.event_bus.subscribe("account.initialized", self._on_account_initialized)
        self.event_bus.subscribe("file.modified", self._on_file_modified)
        self.event_bus.subscribe("file.created", self._on_file_created)
        self.event_bus.subscribe("conversation.stored", self._on_conversation_stored)
        self.event_bus.subscribe("notes.updated", self._on_notes_updated)
        self.event_bus.subscribe("deal.updated", self._on_deal_updated)
        self.event_bus.subscribe("risk.assessment.updated", self._on_risk_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Skill started - generating discovery documents")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # LLMManager doesn't require explicit close; OpenAI client cleaned up by GC
        self.logger.info("Skill stopped")

    # Event handlers with thread-safe scheduling
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

    def _on_file_created(self, event: Event):
        self._on_file_modified(event)

    def _on_conversation_stored(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 20))
            )

    def _on_notes_updated(self, event: Event):
        path = Path(event.data.get("path", ""))
        if self._is_account_file(path):
            account_name = self._extract_account_name(path)
            if account_name:
                self._main_loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self._debounced_update(account_name, 10))
                )

    def _on_deal_updated(self, event: Event):
        path = Path(event.data.get("path", ""))
        if self._is_account_file(path):
            account_name = self._extract_account_name(path)
            if account_name:
                self._main_loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self._debounced_update(account_name, 10))
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
                return parts[-2] if parts[-1] in ('index.json', 'notes.json', 'activities.jsonl', 'summary.md', 'deals', 'discovery') else parts[-1]
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
        await self._update_discovery_documents(account_name)

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
                        await self._update_discovery_documents(account_dir.name)

    async def _update_discovery_documents(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_account_data(account_folder)
            if not data:
                return

            discovery_dir = account_folder / "discovery"
            discovery_dir.mkdir(exist_ok=True)

            # Generate Internal Discovery with LLM (now async)
            internal_content = await self._generate_internal_discovery(account_name, data)
            (discovery_dir / "internal_discovery.md").write_text(internal_content, encoding='utf-8')

            # Generate Final Discovery with LLM (now async)
            final_content = await self._generate_final_discovery(account_name, data)
            (discovery_dir / "final_discovery.md").write_text(final_content, encoding='utf-8')

            # Generate Q2A with LLM synthesis
            q2a_content = await self._generate_q2a(account_name, data)
            (discovery_dir / "Q2A.md").write_text(q2a_content, encoding='utf-8')

            self.logger.info("Updated discovery documents", account=account_name, folder=str(discovery_dir))
            self.event_bus.publish(Event("discovery.updated", "skill.discovery", {"account": account_name}))

        except Exception as e:
            self.logger.error("Failed to update discovery documents", account=account_name, error=str(e))

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

        return data

    def _sanitize_name(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_').lower()

    def _is_valid_account_folder(self, folder: Path) -> bool:
        """Check if folder is a real account (has at least one smartness file, not just deals/)."""
        has_smartness = (folder / 'notes.json').exists() or (folder / 'summary.md').exists() or (folder / 'index.json').exists() or (folder / 'activities.jsonl').exists()
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    # Internal Discovery generation with LLM
    async def _generate_internal_discovery(self, account_name: str, data: Dict[str, Any]) -> str:
        """Generate internal discovery document using LLM synthesis."""
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)

        if self.llm:
            try:
                context = {
                    'account': account_name,
                    'deals': data['deals'],
                    'notes': data['notes'],
                    'facts': data['notes'].get('facts') or [],
                    'knowledge_gaps': data['notes'].get('knowledge_gaps') or [],
                    'competitors': list(data['competitors']),
                    'conversations': data['conversations'][:3],
                    'risk_summary': data.get('risk_assessment', '')[:500]
                }
                synthesized = await self._synthesize_internal_with_llm(context)
                if synthesized:
                    return self._format_internal_discovery(account_name, identity, today, synthesized, data)
            except Exception as e:
                self.logger.debug("LLM internal synthesis failed", error=str(e))

        # Fallback rule-based
        deal_info = ""
        for deal in data['deals']:
            deal_info += f"- **Deal:** {deal.get('name', 'N/A')}\n"
            deal_info += f"  - **Account:** {deal.get('account', 'N/A')}\n"
            deal_info += f"  - **Product:** {deal.get('product', 'N/A')}\n"
            deal_info += f"  - **ARR:** ${deal.get('arr', 0):,}\n"
            deal_info += f"  - **Agents:** {deal.get('agents', 'N/A')}\n"
            deal_info += f"  - **Stage:** {deal.get('stage', 'N/A')}\n"
            deal_info += f"  - **Forecast:** {deal.get('forecast_date', 'N/A')}\n"
            if deal.get('competitors'):
                deal_info += f"  - **Competitors:** {', '.join(deal['competitors'])}\n"
            if deal.get('integrations'):
                deal_info += f"  - **Integrations:** {', '.join(deal['integrations'])}\n"
            deal_info += "\n"

        knowledge_gaps = data['notes'].get('knowledge_gaps') or []
        next_steps_list = knowledge_gaps[:5]

        content = f"""# Internal Discovery - {account_name}

**Prepared by:** {identity.full_display}  
**Date:** {today}  
**Last Updated:** {datetime.now().strftime("%H:%M")}

---

## Deal Overview

{deal_info if deal_info else "- No deal information available"}

## Current Systems & Environment

{self._format_current_systems(data)}

## Key Requirements

{self._format_requirements(data)}

## Knowledge Gaps & Risks

{self._format_gaps(knowledge_gaps)}

## Technical Discovery Status

| Phase | Status | Owner | Notes |
|-------|--------|-------|-------|
| Discovery Call | [] | | |
| Technical Deep Dive | [] | | |
| Architecture Review | [] | | |
| Security Assessment | [] | | |
| Integration Scoping | [] | | |
| POV Planning | [] | | |

## Next Steps (Technical)

{self._format_list(next_steps_list)}

## Open Questions

{self._format_questions(data)}

## 📋 Linked Documents

- [Technical Risk Assessment](../TECHNICAL_RISK_ASSESSMENT.md)
- [Final Discovery](./final_discovery.md)
- [Q2A](./Q2A.md)

---

*This document is automatically maintained by JARVIS Discovery Management Skill.*
"""
        return content

    def _format_internal_discovery(self, account_name: str, identity, today: str, llm_out: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Format LLM-synthesized internal discovery."""
        content = f"""# Internal Discovery - {account_name}

**Prepared by:** {identity.full_display}  
**Date:** {today}  
**Last Updated:** {datetime.now().strftime("%H:%M")}

---

{llm_out.get('deal_overview', '')}

{llm_out.get('current_systems', '')}

## Key Requirements

{self._format_list(llm_out.get('requirements', []))}

## Knowledge Gaps & Risks

{self._format_gaps_from_text(llm_out.get('gaps_status', ''))}

## Technical Discovery Status

{llm_out.get('discovery_phases', '')}

## Next Steps (Technical)

{self._format_list(llm_out.get('next_steps', []))}

## Open Questions

{self._format_list(llm_out.get('open_questions', []))}

## 📋 Linked Documents

- [Technical Risk Assessment](../TECHNICAL_RISK_ASSESSMENT.md)
- [Final Discovery](./final_discovery.md)
- [Q2A](./Q2A.md)

---

*LLM-enhanced by JARVIS.*
"""
        return content

    async def _generate_final_discovery(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)

        if self.llm:
            try:
                context = self._build_context(account_name, data)
                synthesized = await self._synthesize_final_with_llm(context)
                if synthesized:
                    return self._format_final_discovery(account_name, identity, today, synthesized, data)
            except Exception as e:
                self.logger.debug("LLM final synthesis failed", error=str(e))

        current_systems = data['deals'][0].get('current_systems', {}) if data['deals'] else {}
        integrations = []
        for deal in data['deals']:
            integrations.extend(deal.get('integrations', []))

        content = f"""# Final Discovery Summary - {account_name}

**SE:** {identity.full_display}  
**Completion Date:** {today}

---

## Executive Summary

{self._summarize_final(data)}

## Technical Environment

### Current Systems
- **Ticket System:** {current_systems.get('ticket_system', 'Not documented')}
- **Email/Voice Tool:** {current_systems.get('email_voice_tool', 'Not documented')}

### Required Integrations
{self._format_list(integrations) if integrations else "- None specified"}

## Solution Architecture

{self._describe_solution(data)}

## Risks & Mitigations

{self._format_risks(data)}

## Implementation Considerations

- **Timeline:** Based on {len(data['deals'])} deal(s)
- **Dependencies:** See [Q2A](./Q2A.md) for outstanding items
- **Success Criteria:** Defined in [Internal Discovery](./internal_discovery.md)

## Handoff Notes

{self._handoff_notes(data)}

## 📋 Linked Documents

- [Technical Risk Assessment](../TECHNICAL_RISK_ASSESSMENT.md)
- [Internal Discovery](./internal_discovery.md)
- [Q2A](./Q2A.md)

---

*Finalized by {identity.full_display} on {today}*
"""
        return content

    def _format_final_discovery(self, account_name: str, identity, today: str, llm_out: Dict[str, Any], data: Dict[str, Any]) -> str:
        content = f"""# Final Discovery Summary - {account_name}

**SE:** {identity.full_display}  
**Completion Date:** {today}

---

## Executive Summary

{llm_out.get('executive_summary', '')}

## Solution Architecture

{llm_out.get('solution_architecture', '')}

## Risks & Mitigations

{self._format_list(llm_out.get('risks_mitigations', []))}

## Implementation Considerations

{llm_out.get('implementation', '')}

## Handoff Notes

{llm_out.get('handoff', '')}

## 📋 Linked Documents

- [Technical Risk Assessment](../TECHNICAL_RISK_ASSESSMENT.md)
- [Internal Discovery](./internal_discovery.md)
- [Q2A](./Q2A.md)

---

*LLM-enhanced by JARVIS.*
"""
        return content

    async     def _generate_q2a(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)

        gaps = data['notes'].get('knowledge_gaps') or []
        technical_gaps = []
        for deal in data['deals']:
            for req in deal.get('key_requirements', []) or []:
                if 'integration' in req.lower():
                    technical_gaps.append(f"Integration: {req}")
        all_gaps = gaps + technical_gaps

        q2a_list = all_gaps
        if self.llm and all_gaps:
            try:
                synthesized = await self._synthesize_with_llm(all_gaps)
                if synthesized:
                    q2a_list = synthesized
            except:
                pass

        content = f"""# Questions to Answer (Q2A) - {account_name}

**Generated:** {today}  
**Owner:** {identity.full_display}

---

## Priority 1: Critical for Proposal/Scoping

{self._format_priority(q2a_list[:3])}

## Priority 2: Important for Technical Evaluation

{self._format_priority(q2a_list[3:6])}

## Priority 3: Nice to Have / Future Planning

{self._format_priority(q2a_list[6:])}

## Sources & Dependencies

- Notes gaps: {len(gaps)} identified
- Deal requirements: {sum(len(d.get('key_requirements', [])) for d in data['deals'])} identified
- Conversations analyzed: {len(data['conversations'])}
- Risk assessment: {'✅ Available' if data['risk_assessment'] else '❌ Not generated'}

## Answer Status

| Question | Status | Answer | Owner | Due |
|----------|--------|--------|-------|-----|
| [Fill in as you get answers] | | | | |

---

*Q2A auto-generated and continuously updated by JARVIS.*
"""
        return content

    # LLM synthesis helpers
    async def _synthesize_with_llm(self, gaps: List[str]) -> List[str]:
        """Synthesize raw gaps into Q2A questions using LLM."""
        if not self.llm or not gaps:
            return gaps
        prompt = f"""
Convert these discovery knowledge gaps into clear, answerable technical questions.
Prioritize:
P1: Critical for proposal/scoping
P2: Important for technical evaluation  
P3: Nice to have

Gaps:
{chr(10).join(gaps[:15])}

Output format:
P1: question
P2: question
...
"""
        try:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content="You are a Solutions Engineer. Output only P1/P2/P3 questions."),
                Message(role="user", content=prompt)
            ]
            response = await self.llm.generate(messages)
            questions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and any(prefix in line for prefix in ['P1:', 'P2:', 'P3:']):
                    q = line.split(':', 1)[1].strip()
                    questions.append(q)
            return questions[:15] if questions else gaps
        except Exception as e:
            self.logger.debug("LLM Q2A synthesis failed", error=str(e))
            return gaps
        prompt = f"""
Convert these discovery knowledge gaps into clear, answerable technical questions.
Prioritize:
P1: Critical for proposal/scoping
P2: Important for technical evaluation  
P3: Nice to have

Gaps:
{chr(10).join(gaps[:15])}

Output format:
P1: question
P2: question
...
"""
        try:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content="You are a Solutions Engineer. Output only P1/P2/P3 questions."),
                Message(role="user", content=prompt)
            ]
            future = asyncio.run_coroutine_threadsafe(self.llm.generate(messages), self._main_loop)
            response = future.result(timeout=30)
            questions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and any(prefix in line for prefix in ['P1:', 'P2:', 'P3:']):
                    q = line.split(':', 1)[1].strip()
                    questions.append(q)
            # Ensure return is a list
            if questions:
                return questions[:15]
            # If LLM returned something else (e.g., JSON), fallback to parsing
            return gaps
        except Exception as e:
            self.logger.debug("LLM Q2A synthesis failed", error=str(e))
            return gaps

    async def _synthesize_internal_with_llm(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use LLM to synthesize internal discovery sections."""
        if not self.llm:
            return None
        prompt = f"""
Generate internal discovery for {context['account']} as JSON with keys:
deal_overview, current_systems, requirements (list), gaps_status (text), discovery_phases (markdown table), next_steps (list), open_questions (list).

Deals: {json.dumps(context['deals'], indent=2)}
Facts: {chr(10).join(context['facts'][:10])}
Gaps: {chr(10).join(context['knowledge_gaps'][:10])}
Competitors: {', '.join(context['competitors'])}
"""
        try:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content="You are a SE. Output only JSON."),
                Message(role="user", content=prompt)
            ]
            response = await self.llm.generate(messages)
            content = response.strip()
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()
            if not content.startswith('{'):
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    content = match.group()
            return json.loads(content)
        except Exception as e:
            self.logger.debug("LLM internal synthesis failed", error=str(e))
            return None
        prompt = f"""
Generate internal discovery for {context['account']} as JSON with keys:
deal_overview, current_systems, requirements (list), gaps_status (text), discovery_phases (markdown table), next_steps (list), open_questions (list).

Deals: {json.dumps(context['deals'], indent=2)}
Facts: {chr(10).join(context['facts'][:10])}
Gaps: {chr(10).join(context['knowledge_gaps'][:10])}
Competitors: {', '.join(context['competitors'])}
"""
        try:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content="You are a SE. Output only JSON."),
                Message(role="user", content=prompt)
            ]
            response = await self.llm.generate(messages)
            content = response.strip()
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            return json.loads(content)
        except Exception as e:
            self.logger.debug("LLM internal synthesis failed", error=str(e))
            return None
        prompt = f"""
Generate internal discovery for {context['account']} as JSON with keys:
deal_overview, current_systems, requirements (list), gaps_status (text), discovery_phases (markdown table), next_steps (list), open_questions (list).

Deals: {json.dumps(context['deals'], indent=2)}
Facts: {chr(10).join(context['facts'][:10])}
Gaps: {chr(10).join(context['knowledge_gaps'][:10])}
Competitors: {', '.join(context['competitors'])}
"""
        try:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content="You are a SE. Output only JSON."),
                Message(role="user", content=prompt)
            ]
            future = asyncio.run_coroutine_threadsafe(self.llm.generate(messages), self._main_loop)
            response = future.result(timeout=30)
            content = response.strip()
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()
            # If not starting with {, try to extract JSON
            if not content.startswith('{'):
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    content = match.group()
            return json.loads(content)
        except Exception as e:
            self.logger.debug("LLM internal synthesis failed", error=str(e))
            return None

    async def _synthesize_final_with_llm(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use LLM to synthesize final discovery."""
        if not self.llm:
            return None
        prompt = f"""
Generate final discovery summary as JSON with keys:
executive_summary, solution_architecture, risks_mitigations (list), implementation (text), handoff (text).

Account: {context['account']}

Deals: {json.dumps(context['deals'], indent=2)}
Facts: {chr(10).join(context['facts'][:10])}
Gaps: {chr(10).join(context['knowledge_gaps'][:10])}
"""
        try:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content="You are a SE. Output only JSON."),
                Message(role="user", content=prompt)
            ]
            response = await self.llm.generate(messages)
            content = response.strip()
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()
            if not content.startswith('{'):
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    content = match.group()
            return json.loads(content)
        except Exception as e:
            self.logger.debug("LLM final synthesis failed", error=str(e))
            return None

    # Helper build context
    def _build_context(self, account_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        notes = data.get('notes', {})
        # Safely extract fields
        facts = notes.get('facts') or []
        knowledge_gaps = notes.get('knowledge_gaps') or []
        internal_notes = notes.get('internal_notes') or []
        preferences = notes.get('preferences') or []
        if isinstance(preferences, dict):
            pref_items = []
            for v in preferences.values():
                if isinstance(v, list):
                    pref_items.extend(v)
                else:
                    pref_items.append(str(v))
            preferences = pref_items

        return {
            'account': account_name,
            'deals': data['deals'],
            'facts': facts,
            'preferences': preferences,
            'knowledge_gaps': knowledge_gaps,
            'internal_notes': internal_notes,
            'competitors': list(data['competitors']),
            'conversations': data['conversations'],
            'risk_assessment': data.get('risk_assessment', ''),
            'summary': data.get('summary', '')
        }

    # Formatting helpers
    def _format_current_systems(self, data: Dict[str, Any]) -> str:
        systems = []
        for deal in data['deals']:
            cs = deal.get('current_systems', {})
            if cs:
                systems.append(f"- Ticket: {cs.get('ticket_system', 'N/A')}")
                systems.append(f"- Email/Voice: {cs.get('email_voice_tool', 'N/A')}")
        return "\n".join(systems) if systems else "- Not documented yet"

    def _format_requirements(self, data: Dict[str, Any]) -> str:
        reqs = []
        for deal in data['deals']:
            reqs_deal = deal.get('key_requirements') or []
            if not isinstance(reqs_deal, list):
                reqs_deal = []
            for req in reqs_deal[:5]:
                reqs.append(f"- {req}")
        prefs = data['notes'].get('preferences') or []
        if isinstance(prefs, dict):
            # Convert dict values to list, flattening
            pref_items = []
            for value in prefs.values():
                if isinstance(value, list):
                    pref_items.extend(value)
                else:
                    pref_items.append(str(value))
            prefs = pref_items
        elif not isinstance(prefs, list):
            prefs = []
        for fact in prefs[:3]:
            reqs.append(f"- {fact}")
        return "\n".join(reqs) if reqs else "- No requirements captured yet"

    def _format_gaps(self, gaps: List[str]) -> str:
        if not gaps:
            return "- No gaps identified"
        return "\n".join([f"- {gap}" for gap in gaps[:10]])

    def _format_gaps_from_text(self, text: str) -> str:
        if text:
            return text
        return "- No gaps identified"

    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "- None"
        return "\n".join([f"- {item}" for item in items])

    def _format_questions(self, data: Dict[str, Any]) -> str:
        questions = data['notes'].get('knowledge_gaps') or []
        for conv in data['conversations'][:3]:
            insights = conv.get('insights', {})
            qs = insights.get('questions_asked') or []
            questions.extend(qs[:2])
        return self._format_list(questions[:10])

    def _format_risks(self, data: Dict[str, Any]) -> str:
        risk_lines = []
        if data.get('risk_assessment'):
            for line in data['risk_assessment'].split('\n'):
                if 'Risk Level' in line or 'risk:' in line.lower():
                    risk_lines.append(f"- {line.strip()}")
                    break
        comps = set()
        for deal in data['deals']:
            comps.update(deal.get('competitors', []))
        if comps:
            risk_lines.append(f"- Competitive displacement risk: {', '.join(comps)}")
        return "\n".join(risk_lines) if risk_lines else "- Low risk (insufficient data)"

    def _summarize_final(self, data: Dict[str, Any]) -> str:
        parts = []
        if data['deals']:
            deal = data['deals'][0]
            parts.append(f"Proposal for {deal.get('account')} to implement {deal.get('product')} ")
            parts.append(f"supporting {deal.get('agents', 'N/A')} agents with ${deal.get('arr', 0):,} ARR. ")
        if data.get('risk_assessment'):
            parts.append("Technical discovery completed. Key risks identified and mitigation strategies in place.")
        return "".join(parts) or "Discovery ongoing. Additional information needed."

    def _handoff_notes(self, data: Dict[str, Any]) -> str:
        notes = []
        if data['notes'].get('internal_notes'):
            notes.extend(data['notes']['internal_notes'][:3])
        if data['deals'] and data['deals'][0].get('why_now'):
            notes.append(f"Timeline driver: {data['deals'][0]['why_now']}")
        return "\n".join([f"- {n}" for n in notes[:5]]) if notes else "- No specific handoff notes"

    def _describe_solution(self, data: Dict[str, Any]) -> str:
        """Describe the proposed solution architecture (fallback when LLM unavailable)."""
        parts = []
        for deal in data['deals']:
            product = deal.get('product', '')
            reqs = deal.get('key_requirements', [])
            if product:
                parts.append(f"Implement **{product}** to address:")
            for req in reqs[:3]:
                parts.append(f"- {req}")
        if not parts:
            return "Solution details pending discovery completion."
        return "\n".join(parts)

    def _format_priority(self, items: List[str]) -> str:
        if not items:
            return "- None identified"
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
