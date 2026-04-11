"""SystemHealthSkill — Real JARVIS system diagnostics."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from .base_skill import BaseSkill


class SystemHealthSkill(BaseSkill):
    """
    Real-time system health diagnostics:
      - NVIDIA key pool status (ready / rate-limited per model)
      - Queue depth (jobs waiting to run)
      - Skill timeline (last 5 runs per account)
      - Server uptime
    """

    # Injected after construction by JarvisServer
    skill_queue = None   # SkillQueue instance
    _start_time: float = time.time()

    async def generate(
        self,
        account_name: str,
        **kwargs,
    ) -> str:
        lines = [f"# JARVIS System Health\n*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"]

        # ── Uptime ────────────────────────────────────────────────────────────
        uptime_s = int(time.time() - SystemHealthSkill._start_time)
        h, rem = divmod(uptime_s, 3600)
        m, s = divmod(rem, 60)
        lines.append(f"**Uptime:** {h}h {m}m {s}s\n")

        # ── Queue depth ───────────────────────────────────────────────────────
        if self.skill_queue is not None:
            try:
                depth = self.skill_queue._queue.qsize()
                pending = len(self.skill_queue._pending)
                lines.append(f"**Queue:** {depth} jobs waiting | {pending} skill locks held\n")
            except Exception:
                lines.append("**Queue:** unavailable\n")
        else:
            lines.append("**Queue:** not wired\n")

        # ── NVIDIA key pool ───────────────────────────────────────────────────
        try:
            status = self.llm.provider_status()
            lines.append("## NVIDIA Key Pool\n")
            for key_id, models in status.items():
                ready = [m for m, s in models.items() if s == "ready"]
                limited = [f"{m} ({s})" for m, s in models.items() if s != "ready"]
                lines.append(f"**{key_id}:** {len(ready)} models ready"
                              + (f" | RATE-LIMITED: {', '.join(limited)}" if limited else ""))
        except Exception as e:
            lines.append(f"## NVIDIA Key Pool\nUnavailable: {e}\n")

        # ── Skill timeline (last 5 runs for this account) ─────────────────────
        try:
            account_path = self.config.get_account_path(account_name)
            timeline_file = account_path / "_skill_timeline.json"
            if timeline_file.exists():
                timeline = json.loads(timeline_file.read_text())
                recent = list(timeline.items())[-5:] if isinstance(timeline, dict) else []
                if recent:
                    lines.append(f"\n## Recent Skill Runs ({account_name})\n")
                    for skill, ts in reversed(recent):
                        lines.append(f"- `{skill}` — {ts}")
            else:
                lines.append(f"\n## Recent Skill Runs ({account_name})\nNo timeline yet.\n")
        except Exception:
            pass

        return "\n".join(lines)
