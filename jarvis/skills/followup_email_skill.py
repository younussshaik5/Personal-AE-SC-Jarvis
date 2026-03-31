"""Follow-up Email Skill - generates context-aware follow-up email drafts."""

import json
import time
from pathlib import Path
from typing import Dict, Any, List
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class FollowupEmailSkill:
    """Drafts follow-up emails based on meeting context and deal stage."""

    def __init__(self, config_manager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("skill.followup_email")
        self._llm_manager = None

    async def start(self):
        self.event_bus.subscribe("meeting.summary.ready", self._on_summary_ready)
        self.event_bus.subscribe("playbook.draft_followup", self._on_draft_request)
        self.logger.info("FollowupEmailSkill started")

    async def stop(self):
        self.logger.info("FollowupEmailSkill stopped")

    def set_llm_manager(self, llm_manager):
        self._llm_manager = llm_manager

    async def _on_summary_ready(self, event: Event):
        account = event.data.get("account", "")
        if account:
            await self.draft_followup(account, context=event.data.get("summary", ""))

    async def _on_draft_request(self, event: Event):
        account = event.data.get("account", "")
        context = event.data.get("context", "")
        if account:
            await self.draft_followup(account, context=context)

    async def draft_followup(self, account: str, context: str = "",
                              email_type: str = "meeting_followup") -> Dict:
        workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
        account_dir = workspace / "ACCOUNTS" / account

        # Load recent meeting summary if no context provided
        if not context:
            meetings_dir = account_dir / "meetings"
            if meetings_dir.exists():
                summaries = sorted(meetings_dir.glob("*_summary.md"),
                                   key=lambda f: f.stat().st_mtime, reverse=True)
                if summaries:
                    context = summaries[0].read_text()[:4000]

        # Load deal stage
        stage_info = ""
        stage_file = account_dir / "deal_stage.json"
        if stage_file.exists():
            try:
                stage_data = json.loads(stage_file.read_text())
                stage_info = f"Current deal stage: {stage_data.get('stage', 'unknown')}"
            except Exception:
                pass

        # Load template if available
        template = self._load_template(email_type)

        prompt = f"""Draft a professional follow-up email for {account} after a recent interaction.

{stage_info}

CONTEXT FROM RECENT MEETING/INTERACTION:
{context[:4000] if context else 'No specific context available. Draft a general check-in.'}

{f'TEMPLATE GUIDANCE: {template}' if template else ''}

Requirements:
- Professional but warm tone
- Reference specific discussion points from the meeting
- Include clear next steps with proposed dates
- Keep it concise (under 200 words)
- Include a subject line
- Sign off as the company representative

Format:
Subject: [subject line]

[email body]

Best regards,
{getattr(self.config.config, "identity", {}).get("name", "Your Name")}
Account Executive & Solution Consultant
{getattr(self.config.config, "identity", {}).get("company", "Your Company")}"""

        email_text = ""
        if self._llm_manager:
            from jarvis.llm.llm_client import Message
            messages = [
                Message(role="system", content=f"You are JARVIS, drafting professional sales follow-up emails for {getattr(self.config.config, 'identity', {}).get('company', 'Your Company')}."),
                Message(role="user", content=prompt)
            ]
            email_text = await self._llm_manager.generate_with_routing(
                messages, task_type="text", source="background"
            )

        # Write draft
        emails_dir = account_dir / "emails"
        emails_dir.mkdir(parents=True, exist_ok=True)
        date_str = time.strftime("%Y-%m-%d")
        draft_file = emails_dir / f"{date_str}_{email_type}_draft.md"

        content = f"""# Email Draft: {email_type.replace('_', ' ').title()}
**Account:** {account}
**Date:** {date_str}
**Status:** DRAFT - Review before sending via Claude Desktop

---

{email_text}

---
*To send: Open Claude Desktop and say "send the follow-up for {account}"*
"""
        draft_file.write_text(content)
        self.logger.info("Follow-up email drafted", account=account, file=str(draft_file))

        return {"account": account, "draft_file": str(draft_file), "email_text": email_text}

    def _load_template(self, email_type: str) -> str:
        workspace = Path(str(getattr(self.config.config, 'workspace_root', '.')))
        # Check repo templates first, then data dir
        for base in [Path(__file__).parent.parent / "data" / "templates" / "emails",
                     workspace / "data" / "templates" / "emails"]:
            template_file = base / f"{email_type}.md"
            if template_file.exists():
                return template_file.read_text()[:1000]
        return ""
