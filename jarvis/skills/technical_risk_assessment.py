#!/usr/bin/env python3
"""Technical Risk Assessment Skill - LLM-enhanced, interlinked docs."""

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


class TechnicalRiskAssessmentSkill:
    """LLM-synthesized risk assessment with interlinking."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.risk_assessment")
        self.workspace_root = Path(config_manager.config.workspace_root).resolve()
        self.accounts_dir = self.workspace_root / "ACCOUNTS"
        self._last_updates: Dict[str, datetime] = {}
        self._update_interval = 60
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.llm: Optional[LLMManager] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self):
        self.logger.info("Starting technical risk assessment skill")
        self._running = True
        self._main_loop = asyncio.get_running_loop()

        try:
            self.llm = LLMManager(self.config_manager)
            await self.llm.initialize()
        except Exception as e:
            self.logger.warning("LLM unavailable, using rule-based synthesis", error=str(e))
            self.llm = None

        self.event_bus.subscribe("account.initialized", self._on_account_initialized)
        self.event_bus.subscribe("file.modified", self._on_file_modified)
        self.event_bus.subscribe("file.created", self._on_file_created)
        self.event_bus.subscribe("conversation.stored", self._on_conversation_stored)
        self.event_bus.subscribe("competitor.detected", self._on_competitor_detected)
        self.event_bus.subscribe("notes.updated", self._on_notes_updated)
        self.event_bus.subscribe("deal.updated", self._on_deal_updated)
        self.event_bus.subscribe("discovery.updated", self._on_discovery_updated)

        self._task = asyncio.create_task(self._periodic_scan())
        self.logger.info("Skill started - LLM-enhanced risk assessment active")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # LLMManager doesn't require explicit close
        self.logger.info("Skill stopped")

    # Event handlers - schedule updates on main loop
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

    def _on_discovery_updated(self, event: Event):
        account = event.data.get("account")
        if account:
            self._main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._debounced_update(account, 5))
            )

    def _on_competitor_detected(self, event: Event):
        """Handle competitor detection event - trigger full scan."""
        # Competitor detection may affect multiple accounts; schedule a scan
        self._main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self._scan_all_accounts())
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
        await self._update_risk_assessment(account_name)

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
                        # Skip non-account folders (like 'deals' system folders)
                        if not self._is_valid_account_folder(account_dir):
                            continue
                        await self._update_risk_assessment(account_dir.name)

    async def _update_risk_assessment(self, account_name: str):
        try:
            account_folder = await self._find_account_folder(account_name)
            if not account_folder:
                return

            # Validate it's an actual account folder (has at least one smartness file)
            if not self._is_valid_account_folder(account_folder):
                return

            data = await self._gather_account_data(account_folder)
            if not data:
                return

            # Generate risk assessment with LLM enhancement
            content = await self._generate_risk_assessment(account_name, data)

            # Write file
            risk_file = account_folder / "TECHNICAL_RISK_ASSESSMENT.md"
            risk_file.write_text(content, encoding='utf-8')

            self.logger.info("Updated risk assessment", account=account_name)
            # Notify other skills (sync fire-and-forget)
            self.event_bus.publish(Event("risk.assessment.updated", "skill.risk_assessment", {"account": account_name, "file": str(risk_file)}))

        except Exception as e:
            self.logger.error("Failed to update risk assessment", account=account_name, error=str(e))

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
        # If only deals/ exists without any smartness file, it's not an account
        if (folder / 'deals').exists() and not has_smartness:
            return False
        return has_smartness

    async def _generate_risk_assessment(self, account_name: str, data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = get_se_identity(self.config_manager)

        # Build context for LLM
        context = self._build_context(account_name, data)

        # Use LLM to generate synthesized content if available
        if self.llm:
            try:
                synthesized = await self._synthesize_with_llm(context)
                if synthesized:
                    return self._format_risk_assessment(account_name, identity, today, synthesized, data)
            except Exception as e:
                self.logger.debug("LLM synthesis failed", error=str(e))

        # Fallback to rule-based
        return self._generate_rule_based(account_name, identity, today, data)

    def _build_context(self, account_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all data into a context dict for LLM."""
        deals_summary = []
        for deal in data['deals']:
            deals_summary.append({
                'name': deal.get('name'),
                'product': deal.get('product'),
                'arr': deal.get('arr'),
                'stage': deal.get('stage'),
                'competitors': deal.get('competitors', []),
                'integrations': deal.get('integrations', []),
                'requirements': deal.get('key_requirements', []) or []
            })

        # Safely get notes fields
        notes = data.get('notes', {})
        gaps = (notes.get('knowledge_gaps') or []) + (notes.get('internal_notes') or [])
        facts = notes.get('facts') or []
        preferences = notes.get('preferences') or []
        # Ensure preferences is list
        if isinstance(preferences, dict):
            pref_items = []
            for v in preferences.values():
                if isinstance(v, list):
                    pref_items.extend(v)
                else:
                    pref_items.append(str(v))
            preferences = pref_items

        # Extract conversation highlights
        conv_highlights = []
        for conv in data['conversations'][:5]:
            insights = conv.get('insights', {})
            summary = insights.get('summary', '')
            if summary:
                conv_highlights.append(summary[:300])

        # Discovery snippets
        discovery_refs = []
        if data['discovery'].get('internal'):
            discovery_refs.append("Internal discovery available")
        if data['discovery'].get('final'):
            discovery_refs.append("Final discovery available")
        if data['discovery'].get('q2a'):
            discovery_refs.append("Q2A document available")

        return {
            'account': account_name,
            'deals': deals_summary,
            'facts': facts,
            'preferences': preferences,
            'gaps': gaps,
            'competitors': list(data['competitors']),
            'conversation_highlights': conv_highlights,
            'discovery_references': discovery_refs,
            'summary_text': data.get('summary', '')[:500]
        }

    async def _synthesize_with_llm(self, context: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Use LLM to synthesize risk assessment sections."""
        prompt = f"""
You are a Senior Solutions Engineer analyzing an opportunity.

Account: {context['account']}

Deal Info:
{json.dumps(context['deals'], indent=2)}

Key Facts:
{chr(10).join(context['facts'][:10])}

Requirements & Preferences:
{chr(10).join(context['preferences'][:10])}

Knowledge Gaps:
{chr(10).join(context['gaps'][:10])}

Competitors: {', '.join(context['competitors'])}

Recent Conversation Highlights:
{chr(10).join(context['conversation_highlights'])}

Discovery Documents Available: {', '.join(context['discovery_references'])}

Generate JSON with:
- use_cases (list of 3)
- se_steps (string)
- stakeholders (list)
- next_steps (list)
- technical_gaps (list)
- risk_level (Low/Medium/High)
- risk_rationale (string)

Respond ONLY with JSON.
"""
        from jarvis.llm.llm_client import Message
        messages = [
            Message(role="system", content="You are a technical risk analyst. Respond ONLY with valid JSON."),
            Message(role="user", content=prompt)
        ]
        try:
            response = await self.llm.generate(messages)
            content = response.strip()
            # Remove markdown code fences
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()
            # If doesn't start with {, try to extract the first JSON object
            if not content.startswith('{'):
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    content = match.group()
            return json.loads(content)
        except Exception as e:
            self.logger.debug("LLM synthesis failed", error=str(e))
            return None

    def _format_risk_assessment(self, account_name: str, identity, today: str, llm_out: Dict[str, Any], data: Dict[str, Any]) -> str:
        se_name = identity.full_display

        interlinks = []
        if data['discovery'].get('internal'):
            interlinks.append(f"- See [Internal Discovery](./discovery/internal_discovery.md) for technical deep dive")
        if data['discovery'].get('final'):
            interlinks.append(f"- [Final Discovery](./discovery/final_discovery.md) for handoff details")
        if data['discovery'].get('q2a'):
            interlinks.append(f"- [Q2A](./discovery/Q2A.md) lists questions to answer")
        if data.get('summary'):
            interlinks.append(f"- [Account Summary](./summary.md) for overview")

        content = f"""# Technical Risk Assessment: {account_name}

**Owner:** {se_name}  
**Frequency:** Updated in Real-Time (LLM-Enhanced)  
**Last Updated:** {today} {datetime.now().strftime("%H:%M")}

---

## {identity.signature} | {today}

### Top 3 Technical Use Cases
{self._format_list(llm_out.get('use_cases', []))}

### What have we done so far
{self._format_list([llm_out.get('se_steps', '')]) if llm_out.get('se_steps') else "- (No SE activities tracked yet)"}

### Stakeholders
{self._format_list(llm_out.get('stakeholders', []))}

### What is outstanding / Next steps
{self._format_list(llm_out.get('next_steps', [])[:7])}

### Technical gaps / risks
{self._format_list(llm_out.get('technical_gaps', [])[:10])}

### Identified Risk Level
**{llm_out.get('risk_level', 'Low')}** - {llm_out.get('risk_rationale', 'Insufficient data for assessment')}

---

## 📋 Interlinked Documents

{chr(10).join(interlinks) if interlinks else "- Additional documents (discovery, Q2A) will appear here when generated"}

---

## Summary Metrics

- **Deals:** {len(data['deals'])} active
- **Competitors:** {', '.join(data['competitors']) if data['competitors'] else 'None'}
- **Conversations analyzed:** {len(data['conversations'])}
- **Knowledge gaps:** {len(data['gaps'])}
- **Discovery docs:** {len([v for v in data['discovery'].values() if v])} / 3

*This file is auto-updated by JARVIS with LLM intelligence. All documents are interlinked.*
"""
        return content

    def _generate_rule_based(self, account_name: str, identity, today: str, data: Dict[str, Any]) -> str:
        use_cases = self._extract_use_cases(data)
        se_steps = self._extract_se_steps(data)
        stakeholders = self._extract_stakeholders(data)
        next_steps = self._extract_next_steps(data)
        technical_gaps = self._extract_technical_gaps(data)
        comp_count = len(data['competitors'])
        gaps_count = len(data['notes'].get('knowledge_gaps', []))

        if comp_count >= 3 and gaps_count >= 5:
            risk_level = "High"
            rationale = f"{comp_count} competitors + {gaps_count} knowledge gaps"
        elif comp_count >= 2 or gaps_count >= 3:
            risk_level = "Medium"
            rationale = "Some competitive pressure or open questions"
        else:
            risk_level = "Low"
            rationale = "Early stage or limited competitive risk"

        interlinks = []
        if data['discovery'].get('internal'):
            interlinks.append("- See [Internal Discovery](./discovery/internal_discovery.md)")
        if data['discovery'].get('final'):
            interlinks.append("- [Final Discovery](./discovery/final_discovery.md)")
        if data['discovery'].get('q2a'):
            interlinks.append("- [Q2A](./discovery/Q2A.md)")

        return f"""# Technical Risk Assessment: {account_name}

**Owner:** {identity.full_display}  
**Frequency:** Updated in Real-Time (Rule-Based)  
**Last Updated:** {today} {datetime.now().strftime("%H:%M")}

---

## {identity.signature} | {today}

### Top 3 Technical Use Cases
{use_cases or "- (No use cases identified yet)"}

### What have we done so far
{se_steps or "- (No SE activities tracked yet)"}

### Stakeholders
{stakeholders or "- (No stakeholder information yet)"}

### What is outstanding / Next steps
{next_steps or "- (No outstanding items tracked yet)"}

### Technical gaps / risks
{technical_gaps or "- (No technical gaps identified yet)"}

### Identified Risk Level
**{risk_level}** - {rationale}

---

## 📋 Interlinked Documents

{chr(10).join(interlinks) if interlinks else "- Discovery documents will appear here"}

---

## Summary

- **Deals:** {len(data['deals'])}
- **Competitors:** {', '.join(data['competitors']) if data['competitors'] else 'None'}
- **Conversations:** {len(data['conversations'])}
- **Knowledge gaps:** {gaps_count}

*Auto-updated by JARVIS.*
"""

    # Extraction helpers
    def _extract_use_cases(self, data: Dict[str, Any]) -> str:
        use_cases = []
        for deal in data['deals']:
            for req in deal.get('key_requirements', [])[:3]:
                if req not in use_cases:
                    use_cases.append(req)
        return "\n".join([f"- {uc}" for uc in use_cases[:3]]) if use_cases else ""

    def _extract_se_steps(self, data: Dict[str, Any]) -> str:
        steps = []
        for act in data['activities']:
            msg = act.get('message', '') if isinstance(act, dict) else str(act).lower()
            if 'discovery' in msg:
                steps.append("Discovery")
            if 'demo' in msg:
                steps.append("Demo")
            if 'pov' in msg or 'proof' in msg:
                steps.append("POV")
            if 'rfp' in msg:
                steps.append("RFP")
        if steps:
            from collections import Counter
            counts = Counter(steps)
            return ", ".join([f"({count}) {s}" for s, c in counts.most_common()])
        return ""

    def _extract_stakeholders(self, data: Dict[str, Any]) -> str:
        people = []
        for fact in data['notes'].get('facts', []):
            if any(word in fact.lower() for word in ['manager', 'director', 'vp', 'cto', 'cio']):
                people.append(fact)
        return "\n".join([f"- {p}" for p in people[:5]]) if people else ""

    def _extract_next_steps(self, data: Dict[str, Any]) -> str:
        steps = data['notes'].get('knowledge_gaps', [])[:5]
        return "\n".join([f"- {s}" for s in steps]) if steps else ""

    def _extract_technical_gaps(self, data: Dict[str, Any]) -> str:
        gaps = data['notes'].get('knowledge_gaps', [])
        for deal in data['deals']:
            for req in deal.get('key_requirements', []):
                if 'integration' in req.lower():
                    gaps.append(f"Integration: {req}")
        return "\n".join([f"- {g}" for g in gaps[:5]]) if gaps else ""

    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "- None"
        return "\n".join([f"- {item}" for item in items if item])
