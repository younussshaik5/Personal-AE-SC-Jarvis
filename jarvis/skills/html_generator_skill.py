#!/usr/bin/env python3
"""
HTMLGeneratorSkill — generates account.html for every ACCOUNTS/ folder.

Self-contained HTML, data embedded directly. No server needed — open in browser.
Auto-regenerated every time account data changes (meeting processed, MEDDPICC updated, etc.)

account.html shows:
  - MEDDPICC scorecard with per-dimension bars
  - Current deal stage
  - Contacts
  - Recent activity log
  - Action items
  - INTEL files list (links to generated intelligence)

Every folder in ACCOUNTS/ — whether it's an account or an opportunity —
gets the same account.html. JARVIS makes no distinction.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager


class HTMLGeneratorSkill:
    """Generates and auto-refreshes account.html for every ACCOUNTS/ folder."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config    = config_manager
        self.event_bus = event_bus
        self.logger    = JARVISLogger("skills.html_generator")

    async def start(self):
        self._jarvis_home  = Path(self.config.workspace_root)
        self._accounts_dir = self._jarvis_home / "ACCOUNTS"

        # Regenerate on any data change
        self.event_bus.subscribe("knowledge.intel.updated",  self._on_account_change)
        self.event_bus.subscribe("meddpicc.updated",         self._on_account_change)
        self.event_bus.subscribe("account.initialized",      self._on_account_change)
        self.event_bus.subscribe("meeting.summary.ready",    self._on_account_change)
        self.event_bus.subscribe("deal.stage.changed",       self._on_account_change)
        # Presales section events
        self.event_bus.subscribe("discovery.updated",        self._on_account_change)
        self.event_bus.subscribe("battlecard.updated",       self._on_account_change)
        self.event_bus.subscribe("risk.report.updated",      self._on_account_change)
        self.event_bus.subscribe("demo.strategy.updated",    self._on_account_change)
        self.event_bus.subscribe("next_steps.updated",           self._on_account_change)
        self.event_bus.subscribe("value_architecture.updated",   self._on_account_change)
        self.event_bus.subscribe("architecture.diagram.updated", self._on_account_change)
        self.event_bus.subscribe("proposal.updated",             self._on_account_change)
        self.event_bus.subscribe("sow.updated",                  self._on_account_change)

        self.logger.info("HTMLGeneratorSkill started")

    async def stop(self):
        pass

    # ------------------------------------------------------------------
    # Event handler
    # ------------------------------------------------------------------

    async def _on_account_change(self, event: Event):
        account = (event.data.get("account") or
                   event.data.get("account_name") or "")
        if account:
            await self.generate_account_html(account)

    # ------------------------------------------------------------------
    # Task handler (called by WorkerPool for html_refresh tasks)
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_html_refresh(task, services: Dict[str, Any]):
        skill: "HTMLGeneratorSkill" = services.get("html_generator")
        if not skill:
            return
        account = task.payload.get("account", "")
        if account:
            await skill.generate_account_html(account)

    # ------------------------------------------------------------------
    # Generator
    # ------------------------------------------------------------------

    async def generate_account_html(self, account_name: str):
        """Generate ACCOUNTS/{account}/account.html"""
        account_dir = self._accounts_dir / account_name
        if not account_dir.exists():
            return
        try:
            data = self._collect_account_data(account_dir)
            html = self._render_account_html(data)
            (account_dir / "account.html").write_text(html, encoding="utf-8")
            self.logger.debug("account.html refreshed", account=account_name)
        except Exception as e:
            self.logger.error("account.html generation failed",
                              account=account_name, error=str(e))

    # ------------------------------------------------------------------
    # Data collector
    # ------------------------------------------------------------------

    def _collect_account_data(self, account_dir: Path) -> dict:
        # Presales section status
        def section_status(folder: str, key_file: str) -> str:
            f = account_dir / folder / key_file
            if not f.exists():
                return "not_initialized"
            text = self._read_text(f)
            if "Generating..." in text or "Waiting for" in text:
                return "pending"
            return "ready"

        def section_preview(folder: str, key_file: str, max_chars: int = 400) -> str:
            f = account_dir / folder / key_file
            text = self._read_text(f)
            if not text or "Generating..." in text:
                return ""
            # Return first non-heading content lines
            lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#") and not l.startswith("*Auto")]
            return " ".join(lines)[:max_chars]

        bc_data = self._read_json(account_dir / "BATTLECARD" / "battlecard_data.json") or {}

        return {
            "account":         account_dir.name,
            "generated_at":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            "meddpicc":        self._read_json(account_dir / "meddpicc.json") or {},
            "deal_stage":      self._read_json(account_dir / "deal_stage.json") or {},
            "contacts":        (self._read_json(account_dir / "contacts.json") or {}).get("contacts", []),
            "activities":      self._read_jsonl(account_dir / "activities.jsonl")[-20:],
            "actions":         self._read_text(account_dir / "actions.md"),
            "intel_files":     self._list_dir(account_dir / "INTEL", "*.md"),
            "meetings_count":  len(self._list_dir(account_dir / "meetings", "*.md")),
            "documents_count": len(self._list_dir(account_dir / "DOCUMENTS", "*.*")),
            "emails_count":    len(self._list_dir(account_dir / "EMAILS", "*.*")),
            # Presales section statuses and previews
            "discovery_status":    section_status("DISCOVERY", "discovery_prep.md"),
            "discovery_preview":   section_preview("DISCOVERY", "final_discovery.md"),
            "battlecard_status":   section_status("BATTLECARD", "battlecard.md"),
            "battlecard_win_prob": bc_data.get("win_probability", ""),
            "battlecard_diff":     bc_data.get("differentiators", [])[:3],
            "demo_status":         section_status("DEMO_STRATEGY", "demo_strategy.md"),
            "demo_preview":        section_preview("DEMO_STRATEGY", "demo_strategy.md"),
            "risk_status":         section_status("RISK_REPORT", "risk_report.md"),
            "risk_preview":        section_preview("RISK_REPORT", "risk_report.md"),
            "nextsteps_status":    section_status("NEXT_STEPS", "next_steps.md"),
            "nextsteps_stage":     (self._read_json(account_dir / "NEXT_STEPS" / "email_drafts.json") or {}).get("current_stage", ""),
            "va_status":           section_status("VALUE_ARCHITECTURE", "roi_model.md"),
            "rfi_files":           self._list_dir(account_dir / "RFI", "*.*"),
        }

    # ------------------------------------------------------------------
    # HTML renderer
    # ------------------------------------------------------------------

    def _render_account_html(self, d: dict) -> str:
        meddpicc    = d["meddpicc"]
        score       = meddpicc.get("score", 0)
        max_score   = meddpicc.get("max_score", 8)
        stage       = d["deal_stage"].get("stage", "new_account").replace("_", " ").title()
        contacts    = d["contacts"]
        activities  = d["activities"]
        intel_files = d["intel_files"]

        score_pct   = int((score / max_score) * 100) if max_score else 0
        score_color = "#22c55e" if score_pct >= 75 else "#f59e0b" if score_pct >= 40 else "#ef4444"

        # MEDDPICC dimension bars
        meddpicc_bars = ""
        for dim in ("metrics", "economic_buyer", "decision_criteria", "decision_process",
                    "paper_process", "implicate_pain", "champion", "competition"):
            val = meddpicc.get(dim, 0)
            label = dim.replace("_", " ").title()
            w = int(val / 3 * 100) if val else 0
            color = "#22c55e" if val >= 2 else "#f59e0b" if val == 1 else "#e5e7eb"
            meddpicc_bars += (
                f"<div class='mrow'>"
                f"<span class='mlbl'>{label}</span>"
                f"<div class='bar-bg'><div class='bar-fill' style='width:{w}%;background:{color}'></div></div>"
                f"<span class='mval'>{val}/3</span>"
                f"</div>"
            )

        # Contacts
        contacts_html = "".join(
            f"<div class='contact'>"
            f"<strong>{c.get('name','?')}</strong>"
            f"{' · ' + c.get('title','') if c.get('title') else ''}"
            f"{' · <a href=\"mailto:' + c.get('email','') + '\">' + c.get('email','') + '</a>' if c.get('email') else ''}"
            f"</div>"
            for c in contacts[:8]
        ) or "<p class='empty'>No contacts yet</p>"

        # Activities
        activity_html = "".join(
            f"<div class='act'><span class='act-time'>{a.get('timestamp','')[:16]}</span>"
            f" {a.get('type','event')}: {a.get('summary','')}</div>"
            for a in reversed(activities)
        ) or "<p class='empty'>No activity yet</p>"

        # Intel tags
        intel_html = "".join(
            f"<a class='intel-tag' href='INTEL/{f}'>{f.replace('.md','')}</a>"
            for f in intel_files
        ) or "<span class='empty'>No intel generated yet — NVIDIA is working on it</span>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{d['account']} — JARVIS</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;color:#0f172a}}
  .hdr{{background:#0f172a;color:#f8fafc;padding:18px 28px;display:flex;align-items:center;justify-content:space-between}}
  .hdr h1{{font-size:20px;font-weight:700}}
  .hdr .meta{{font-size:12px;color:#94a3b8;margin-top:3px}}
  .hdr .ts{{font-size:11px;color:#64748b}}
  .main{{max-width:1100px;margin:0 auto;padding:20px 28px;display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  .card{{background:white;border-radius:10px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
  .card h2{{font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px}}
  .score{{font-size:52px;font-weight:800;color:{score_color};line-height:1}}
  .score-sub{{font-size:13px;color:#64748b;margin-top:4px}}
  .stage-badge{{display:inline-block;margin-top:8px;padding:3px 12px;border-radius:999px;background:#dbeafe;color:#1d4ed8;font-size:12px;font-weight:600}}
  .mrow{{display:flex;align-items:center;gap:8px;margin-bottom:7px}}
  .mlbl{{width:130px;font-size:12px;color:#475569;flex-shrink:0}}
  .bar-bg{{flex:1;height:7px;background:#e2e8f0;border-radius:4px;overflow:hidden}}
  .bar-fill{{height:100%;border-radius:4px}}
  .mval{{width:28px;font-size:11px;color:#94a3b8;text-align:right;flex-shrink:0}}
  .contact{{font-size:13px;padding:5px 0;border-bottom:1px solid #f1f5f9}}
  .act{{font-size:12px;padding:4px 0;border-bottom:1px solid #f8fafc;color:#334155}}
  .act-time{{color:#94a3b8;font-size:11px}}
  .intel-tag{{display:inline-block;margin:3px;padding:3px 9px;background:#f0fdf4;color:#15803d;border-radius:6px;font-size:12px;text-decoration:none}}
  .intel-tag:hover{{background:#dcfce7}}
  .stat{{display:inline-block;margin-right:16px;font-size:13px}}
  .stat strong{{color:#0f172a}}
  .empty{{font-size:12px;color:#94a3b8;font-style:italic}}
  .full{{grid-column:1/-1}}
  pre{{font-family:inherit;white-space:pre-wrap;font-size:12px;color:#334155;max-height:180px;overflow-y:auto;line-height:1.5}}
  a{{color:#2563eb;text-decoration:none}}
  .ps-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;grid-column:1/-1}}
  .ps-card{{background:white;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
  .ps-card h3{{font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px}}
  .ps-badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;margin-bottom:6px}}
  .badge-ready{{background:#dcfce7;color:#15803d}}
  .badge-pending{{background:#fef9c3;color:#854d0e}}
  .badge-init{{background:#f1f5f9;color:#94a3b8}}
  .ps-preview{{font-size:12px;color:#475569;line-height:1.4;margin-top:4px}}
  .ps-list{{font-size:12px;color:#334155;margin-top:4px}}
  .ps-list li{{margin-bottom:2px}}
</style>
</head>
<body>
<div class="hdr">
  <div>
    <h1>{d['account']}</h1>
    <div class="meta">
      <span class="stat"><strong>{d['meetings_count']}</strong> meetings</span>
      <span class="stat"><strong>{d['documents_count']}</strong> documents</span>
      <span class="stat"><strong>{d['emails_count']}</strong> emails</span>
    </div>
  </div>
  <span class="ts">Updated: {d['generated_at']}</span>
</div>

<div class="main">

  <div class="card">
    <h2>MEDDPICC Score</h2>
    <div class="score">{score}<span style="font-size:24px;color:#cbd5e1">/{max_score}</span></div>
    <div class="score-sub">{score_pct}% qualified</div>
    <div class="stage-badge">{stage}</div>
    <div style="margin-top:14px">{meddpicc_bars}</div>
  </div>

  <div class="card">
    <h2>Contacts ({len(contacts)})</h2>
    {contacts_html}
  </div>

  <div class="card">
    <h2>Intel Generated ({len(intel_files)} files)</h2>
    {intel_html}
  </div>

  <div class="card">
    <h2>Recent Activity</h2>
    {activity_html}
  </div>

  <div class="card full">
    <h2>Action Items</h2>
    <pre>{d['actions'][:3000] or 'No action items yet'}</pre>
  </div>

  <div class="full" style="margin-top:4px">
    <div style="font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">
      Presales Intelligence
    </div>
    <div class="ps-grid">
      {self._render_ps_card("Discovery", d['discovery_status'], d['discovery_preview'], "DISCOVERY/discovery_prep.md")}
      {self._render_ps_card_battlecard(d)}
      {self._render_ps_card("Demo Strategy", d['demo_status'], d['demo_preview'], "DEMO_STRATEGY/demo_strategy.md")}
      {self._render_ps_card_risk(d)}
      {self._render_ps_card_nextsteps(d)}
      {self._render_ps_card("Value Architecture", d['va_status'], "", "VALUE_ARCHITECTURE/roi_model.md")}
    </div>
  </div>

</div>
</body>
</html>"""

    # ------------------------------------------------------------------
    # Presales section card renderers
    # ------------------------------------------------------------------

    def _badge(self, status: str) -> str:
        cls = {"ready": "badge-ready", "pending": "badge-pending"}.get(status, "badge-init")
        label = {"ready": "Ready", "pending": "Generating...", "not_initialized": "Not set up"}.get(status, status)
        return f"<span class='ps-badge {cls}'>{label}</span>"

    def _render_ps_card(self, title: str, status: str, preview: str, link: str) -> str:
        preview_html = f"<p class='ps-preview'>{preview[:300]}</p>" if preview else ""
        return (f"<div class='ps-card'>"
                f"<h3><a href='{link}' style='color:inherit;text-decoration:none'>{title}</a></h3>"
                f"{self._badge(status)}"
                f"{preview_html}"
                f"</div>")

    def _render_ps_card_battlecard(self, d: dict) -> str:
        status = d.get("battlecard_status", "not_initialized")
        win_prob = d.get("battlecard_win_prob", "")
        diffs = d.get("battlecard_diff", [])
        extras = ""
        if win_prob:
            extras += f"<p class='ps-preview'>Win probability: <strong>{win_prob}</strong></p>"
        if diffs:
            items = "".join(f"<li>{diff}</li>" for diff in diffs)
            extras += f"<ul class='ps-list'>{items}</ul>"
        return (f"<div class='ps-card'>"
                f"<h3><a href='BATTLECARD/battlecard.md' style='color:inherit;text-decoration:none'>Battlecard</a></h3>"
                f"{self._badge(status)}"
                f"{extras}"
                f"</div>")

    def _render_ps_card_risk(self, d: dict) -> str:
        status = d.get("risk_status", "not_initialized")
        preview = d.get("risk_preview", "")
        color = "#ef4444" if "Critical" in preview or "High" in preview else "#f59e0b" if "Medium" in preview else "#22c55e"
        dot = f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};margin-right:4px'></span>" if status == "ready" else ""
        preview_html = f"<p class='ps-preview'>{dot}{preview[:250]}</p>" if preview else ""
        return (f"<div class='ps-card'>"
                f"<h3><a href='RISK_REPORT/risk_report.md' style='color:inherit;text-decoration:none'>Risk Report</a></h3>"
                f"{self._badge(status)}"
                f"{preview_html}"
                f"</div>")

    def _render_ps_card_nextsteps(self, d: dict) -> str:
        status = d.get("nextsteps_status", "not_initialized")
        stage = d.get("nextsteps_stage", "").replace("_", " ").title()
        stage_html = f"<p class='ps-preview'>Stage: <strong>{stage}</strong></p>" if stage else ""
        return (f"<div class='ps-card'>"
                f"<h3><a href='NEXT_STEPS/next_steps.md' style='color:inherit;text-decoration:none'>Next Steps</a></h3>"
                f"{self._badge(status)}"
                f"{stage_html}"
                f"</div>")

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def _list_dir(self, path: Path, pattern: str) -> list:
        if not path.exists():
            return []
        return [f.name for f in sorted(path.glob(pattern))
                if not f.name.startswith((".", "README"))]

    def _read_json(self, path: Path) -> Optional[dict]:
        try:
            return json.loads(path.read_text()) if path.exists() else None
        except Exception:
            return None

    def _read_jsonl(self, path: Path) -> list:
        if not path.exists():
            return []
        result = []
        for line in path.read_text().splitlines():
            try:
                result.append(json.loads(line))
            except Exception:
                pass
        return result

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8") if path.exists() else ""
        except Exception:
            return ""
