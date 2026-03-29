#!/usr/bin/env python3
"""
HTMLGeneratorSkill — generates account.html and opp.html dashboards.

These are self-contained HTML files with data embedded directly as JSON.
No server needed — just open the file in a browser.
Auto-regenerated every time account or opportunity data changes.

account.html shows:
  - Account overview (stage, MEDDPICC score, contacts)
  - All opportunities (list + status)
  - Recent activities
  - Action items
  - INTEL summaries

opp.html shows:
  - Opportunity details (value, stage, close date)
  - MEDDPICC scorecard
  - Meetings, documents, emails count
  - Action items
  - INTEL for this opportunity
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager


class HTMLGeneratorSkill:
    """Generates and refreshes account + opportunity HTML dashboards."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config    = config_manager
        self.event_bus = event_bus
        self.logger    = JARVISLogger("skills.html_generator")

    async def start(self):
        self._jarvis_home  = Path(self.config.workspace_root)
        self._accounts_dir = self._jarvis_home / "ACCOUNTS"

        # Regenerate dashboards on any relevant data change
        self.event_bus.subscribe("knowledge.intel.updated",   self._on_account_change)
        self.event_bus.subscribe("meddpicc.updated",          self._on_account_change)
        self.event_bus.subscribe("account.initialized",       self._on_account_change)
        self.event_bus.subscribe("opportunity.initialized",   self._on_opp_change)
        self.event_bus.subscribe("meeting.summary.ready",     self._on_account_change)
        self.event_bus.subscribe("deal.stage.changed",        self._on_account_change)

        self.logger.info("HTMLGeneratorSkill started")

    async def stop(self):
        pass

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_account_change(self, event: Event):
        account = (event.data.get("account") or
                   event.data.get("account_name") or "")
        if account:
            await self.generate_account_html(account)

    async def _on_opp_change(self, event: Event):
        account  = event.data.get("account_name", "")
        opp_name = event.data.get("opp_name", "")
        if account and opp_name:
            await self.generate_opp_html(account, opp_name)
            await self.generate_account_html(account)  # refresh account dashboard too

    # ------------------------------------------------------------------
    # Task handler (called by WorkerPool for html_refresh tasks)
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_html_refresh(task, services: Dict[str, Any]):
        skill: "HTMLGeneratorSkill" = services.get("html_generator")
        if not skill:
            return
        account = task.payload.get("account", "")
        level   = task.payload.get("level", "account")
        opp     = task.payload.get("opp", "")
        if account:
            await skill.generate_account_html(account)
        if level == "opp" and opp:
            await skill.generate_opp_html(account, opp)

    # ------------------------------------------------------------------
    # Generators
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

    async def generate_opp_html(self, account_name: str, opp_name: str):
        """Generate ACCOUNTS/{account}/{opp_name}/opp.html"""
        opp_dir = self._accounts_dir / account_name / opp_name
        if not opp_dir.exists():
            return
        try:
            data = self._collect_opp_data(account_name, opp_dir)
            html = self._render_opp_html(data)
            (opp_dir / "opp.html").write_text(html, encoding="utf-8")
            self.logger.debug("opp.html refreshed", account=account_name, opp=opp_name)
        except Exception as e:
            self.logger.error("opp.html generation failed",
                              account=account_name, opp=opp_name, error=str(e))

    # ------------------------------------------------------------------
    # Data collectors
    # ------------------------------------------------------------------

    def _collect_account_data(self, account_dir: Path) -> dict:
        d: Dict[str, Any] = {
            "account":      account_dir.name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "meddpicc":     self._read_json(account_dir / "meddpicc.json") or {},
            "deal_stage":   self._read_json(account_dir / "deal_stage.json") or {},
            "contacts":     (self._read_json(account_dir / "contacts.json") or {}).get("contacts", []),
            "activities":   self._read_jsonl(account_dir / "activities.jsonl")[-20:],
            "actions":      self._read_text(account_dir / "actions.md"),
            "intel_files":  self._list_intel(account_dir / "INTEL"),
            "opportunities": self._list_opportunities(account_dir),
            "meetings_count":   len(list((account_dir / "meetings").glob("*.md"))) if (account_dir / "meetings").exists() else 0,
            "documents_count":  len(list((account_dir / "DOCUMENTS").glob("*"))) if (account_dir / "DOCUMENTS").exists() else 0,
        }
        return d

    def _collect_opp_data(self, account_name: str, opp_dir: Path) -> dict:
        return {
            "account":      account_name,
            "opp_name":     opp_dir.name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "opp":          self._read_json(opp_dir / "opp.json") or {},
            "meddpicc":     self._read_json(opp_dir / "meddpicc.json") or {},
            "contacts":     (self._read_json(opp_dir / "contacts.json") or {}).get("contacts", []),
            "activities":   self._read_jsonl(opp_dir / "activities.jsonl")[-10:],
            "actions":      self._read_text(opp_dir / "actions.md"),
            "intel_files":  self._list_intel(opp_dir / "INTEL"),
            "meetings_count":  len(list((opp_dir / "MEETINGS").glob("*.*"))) if (opp_dir / "MEETINGS").exists() else 0,
            "documents_count": len(list((opp_dir / "DOCUMENTS").glob("*.*"))) if (opp_dir / "DOCUMENTS").exists() else 0,
        }

    # Standard folders that are NOT opportunities
    _STANDARD_DIRS = {
        "MEETINGS", "DOCUMENTS", "EMAILS", "INTEL", "meetings",
        "deals", ".processed", "failed",
    }

    def _list_opportunities(self, account_dir: Path) -> list:
        """
        Any subfolder inside the account folder that is NOT a standard folder
        and contains an opp.json file is an opportunity.
        e.g. ACCOUNTS/Tata/Tata Sky/ → opportunity "Tata Sky"
        """
        result = []
        for opp_dir in sorted(account_dir.iterdir()):
            if (opp_dir.is_dir()
                    and opp_dir.name not in self._STANDARD_DIRS
                    and not opp_dir.name.startswith((".", "_"))):
                opp_data = self._read_json(opp_dir / "opp.json") or {}
                meddpicc = self._read_json(opp_dir / "meddpicc.json") or {}
                result.append({
                    "name":     opp_dir.name,
                    "stage":    opp_data.get("stage", "new"),
                    "value":    opp_data.get("value", 0),
                    "currency": opp_data.get("currency", "USD"),
                    "score":    meddpicc.get("score", 0),
                    "close":    opp_data.get("close_date", ""),
                })
        return result

    def _list_intel(self, intel_dir: Path) -> list:
        if not intel_dir.exists():
            return []
        return [f.name for f in intel_dir.glob("*.md") if not f.name.startswith(".")]

    # ------------------------------------------------------------------
    # HTML renderers
    # ------------------------------------------------------------------

    def _render_account_html(self, d: dict) -> str:
        meddpicc    = d.get("meddpicc", {})
        score       = meddpicc.get("score", 0)
        max_score   = meddpicc.get("max_score", 8)
        stage       = d.get("deal_stage", {}).get("stage", "unknown")
        opps        = d.get("opportunities", [])
        contacts    = d.get("contacts", [])
        activities  = d.get("activities", [])
        intel_files = d.get("intel_files", [])
        actions_md  = d.get("actions", "")

        score_pct   = int((score / max_score) * 100) if max_score else 0
        score_color = "#22c55e" if score_pct >= 75 else "#f59e0b" if score_pct >= 40 else "#ef4444"

        opps_rows = "".join(
            f"<tr><td><a href='OPPORTUNITIES/{o['name']}/opp.html'>{o['name']}</a></td>"
            f"<td><span class='badge'>{o['stage']}</span></td>"
            f"<td>{o['currency']} {o['value']:,}</td>"
            f"<td>{o['score']}/8</td>"
            f"<td>{o.get('close','')}</td></tr>"
            for o in opps
        ) or "<tr><td colspan='5' style='color:#6b7280'>No opportunities yet — create a folder in OPPORTUNITIES/</td></tr>"

        contacts_html = "".join(
            f"<div class='contact'><strong>{c.get('name','?')}</strong> · {c.get('title','')} · "
            f"<a href='mailto:{c.get('email','')}'>{c.get('email','')}</a></div>"
            for c in contacts[:8]
        ) or "<p style='color:#6b7280'>No contacts yet</p>"

        meddpicc_bars = ""
        for dim in ("metrics","economic_buyer","decision_criteria","decision_process",
                    "paper_process","implicate_pain","champion","competition"):
            val = meddpicc.get(dim, 0)
            label = dim.replace("_", " ").title()
            w = int(val / 3 * 100) if val else 0
            bar_color = "#22c55e" if val >= 2 else "#f59e0b" if val == 1 else "#e5e7eb"
            meddpicc_bars += (
                f"<div class='meddpicc-row'>"
                f"<span class='dim-label'>{label}</span>"
                f"<div class='bar-bg'><div class='bar-fill' style='width:{w}%;background:{bar_color}'></div></div>"
                f"<span class='dim-val'>{val}/3</span></div>"
            )

        activity_html = "".join(
            f"<div class='activity-item'>{a.get('timestamp','')[:16]} — {a.get('type','event')}: {a.get('summary','')}</div>"
            for a in reversed(activities)
        ) or "<p style='color:#6b7280'>No activity yet</p>"

        intel_html = "".join(
            f"<span class='intel-tag'>{f.replace('.md','')}</span>"
            for f in intel_files
        ) or "<span style='color:#6b7280'>No intel generated yet</span>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{d['account']} — JARVIS</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f9fafb; color:#111827; }}
  .header {{ background:#1e293b; color:white; padding:20px 32px; display:flex; align-items:center; justify-content:space-between; }}
  .header h1 {{ font-size:22px; font-weight:700; }}
  .header .meta {{ font-size:12px; color:#94a3b8; }}
  .main {{ max-width:1200px; margin:0 auto; padding:24px 32px; display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  .card {{ background:white; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .card h2 {{ font-size:14px; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:.05em; margin-bottom:14px; }}
  .score-big {{ font-size:48px; font-weight:800; color:{score_color}; }}
  .score-sub {{ font-size:14px; color:#6b7280; margin-top:4px; }}
  .badge {{ display:inline-block; padding:2px 10px; border-radius:999px; background:#dbeafe; color:#1d4ed8; font-size:12px; font-weight:600; text-transform:uppercase; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ text-align:left; color:#6b7280; font-weight:600; padding:6px 8px; border-bottom:1px solid #e5e7eb; }}
  td {{ padding:8px; border-bottom:1px solid #f3f4f6; }}
  tr:hover td {{ background:#f9fafb; }}
  a {{ color:#2563eb; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .meddpicc-row {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
  .dim-label {{ width:140px; font-size:12px; color:#374151; flex-shrink:0; }}
  .bar-bg {{ flex:1; height:8px; background:#e5e7eb; border-radius:4px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:4px; transition:width .3s; }}
  .dim-val {{ width:30px; font-size:12px; color:#6b7280; text-align:right; flex-shrink:0; }}
  .contact {{ font-size:13px; padding:6px 0; border-bottom:1px solid #f3f4f6; }}
  .activity-item {{ font-size:12px; padding:4px 0; color:#374151; border-bottom:1px solid #f9fafb; }}
  .intel-tag {{ display:inline-block; margin:3px; padding:3px 10px; background:#f0fdf4; color:#16a34a; border-radius:6px; font-size:12px; }}
  .full-width {{ grid-column:1/-1; }}
  pre {{ font-family:inherit; white-space:pre-wrap; font-size:12px; color:#374151; max-height:200px; overflow-y:auto; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>{d['account']}</h1>
    <div class="meta">Stage: <strong>{stage}</strong> &nbsp;·&nbsp; {d['meetings_count']} meetings · {d['documents_count']} documents</div>
  </div>
  <div class="meta">Updated: {d['generated_at']}</div>
</div>
<div class="main">

  <div class="card">
    <h2>MEDDPICC Score</h2>
    <div class="score-big">{score}<span style="font-size:24px;color:#9ca3af">/{max_score}</span></div>
    <div class="score-sub">{score_pct}% qualified</div>
    <div style="margin-top:16px">{meddpicc_bars}</div>
  </div>

  <div class="card">
    <h2>Contacts ({len(contacts)})</h2>
    {contacts_html}
  </div>

  <div class="card full-width">
    <h2>Opportunities ({len(opps)})</h2>
    <table>
      <thead><tr><th>Opportunity</th><th>Stage</th><th>Value</th><th>MEDDPICC</th><th>Close Date</th></tr></thead>
      <tbody>{opps_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Intel Generated</h2>
    {intel_html}
  </div>

  <div class="card">
    <h2>Recent Activity</h2>
    {activity_html}
  </div>

  <div class="card full-width">
    <h2>Action Items</h2>
    <pre>{actions_md[:2000]}</pre>
  </div>

</div>
</body>
</html>"""

    def _render_opp_html(self, d: dict) -> str:
        opp      = d.get("opp", {})
        meddpicc = d.get("meddpicc", {})
        score    = meddpicc.get("score", 0)
        max_s    = meddpicc.get("max_score", 8)
        score_pct = int((score / max_s) * 100) if max_s else 0
        score_color = "#22c55e" if score_pct >= 75 else "#f59e0b" if score_pct >= 40 else "#ef4444"
        contacts = d.get("contacts", [])
        activities = d.get("activities", [])

        meddpicc_bars = ""
        for dim in ("metrics","economic_buyer","decision_criteria","decision_process",
                    "paper_process","implicate_pain","champion","competition"):
            val = meddpicc.get(dim, 0)
            label = dim.replace("_", " ").title()
            w = int(val / 3 * 100) if val else 0
            bar_color = "#22c55e" if val >= 2 else "#f59e0b" if val == 1 else "#e5e7eb"
            meddpicc_bars += (
                f"<div class='meddpicc-row'>"
                f"<span class='dim-label'>{label}</span>"
                f"<div class='bar-bg'><div class='bar-fill' style='width:{w}%;background:{bar_color}'></div></div>"
                f"<span class='dim-val'>{val}/3</span></div>"
            )

        contacts_html = "".join(
            f"<div class='contact'><strong>{c.get('name','?')}</strong> · {c.get('title','')} · {c.get('email','')}</div>"
            for c in contacts[:5]
        ) or "<p style='color:#6b7280'>No contacts</p>"

        activity_html = "".join(
            f"<div class='activity-item'>{a.get('timestamp','')[:16]} — {a.get('type','event')}: {a.get('summary','')}</div>"
            for a in reversed(activities)
        ) or "<p style='color:#6b7280'>No activity yet</p>"

        intel_html = "".join(
            f"<span class='intel-tag'>{f.replace('.md','')}</span>"
            for f in d.get("intel_files", [])
        ) or "<span style='color:#6b7280'>No intel yet</span>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{d['opp_name']} — {d['account']} — JARVIS</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f9fafb; color:#111827; }}
  .header {{ background:#1e293b; color:white; padding:20px 32px; }}
  .header .breadcrumb {{ font-size:12px; color:#94a3b8; margin-bottom:6px; }}
  .header h1 {{ font-size:22px; font-weight:700; }}
  .header .meta {{ font-size:12px; color:#94a3b8; margin-top:4px; }}
  .main {{ max-width:1000px; margin:0 auto; padding:24px 32px; display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  .card {{ background:white; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .card h2 {{ font-size:14px; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:.05em; margin-bottom:14px; }}
  .score-big {{ font-size:48px; font-weight:800; color:{score_color}; }}
  .score-sub {{ font-size:14px; color:#6b7280; margin-top:4px; }}
  .kv {{ display:flex; gap:8px; margin-bottom:8px; font-size:13px; }}
  .kv .k {{ color:#6b7280; width:100px; flex-shrink:0; }}
  .kv .v {{ font-weight:600; }}
  .meddpicc-row {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
  .dim-label {{ width:140px; font-size:12px; color:#374151; flex-shrink:0; }}
  .bar-bg {{ flex:1; height:8px; background:#e5e7eb; border-radius:4px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:4px; }}
  .dim-val {{ width:30px; font-size:12px; color:#6b7280; text-align:right; flex-shrink:0; }}
  .contact {{ font-size:13px; padding:6px 0; border-bottom:1px solid #f3f4f6; }}
  .activity-item {{ font-size:12px; padding:4px 0; color:#374151; border-bottom:1px solid #f9fafb; }}
  .intel-tag {{ display:inline-block; margin:3px; padding:3px 10px; background:#f0fdf4; color:#16a34a; border-radius:6px; font-size:12px; }}
  .full-width {{ grid-column:1/-1; }}
  a {{ color:#2563eb; text-decoration:none; }}
  pre {{ font-family:inherit; white-space:pre-wrap; font-size:12px; color:#374151; max-height:180px; overflow-y:auto; }}
</style>
</head>
<body>
<div class="header">
  <div class="breadcrumb"><a href="../account.html" style="color:#94a3b8">{d['account']}</a> › Opportunities</div>
  <h1>{d['opp_name']}</h1>
  <div class="meta">Stage: <strong>{opp.get('stage','new')}</strong> &nbsp;·&nbsp; {d['meetings_count']} meetings · {d['documents_count']} documents &nbsp;·&nbsp; Updated: {d['generated_at']}</div>
</div>
<div class="main">

  <div class="card">
    <h2>Opportunity</h2>
    <div class="kv"><span class="k">Value</span><span class="v">{opp.get('currency','USD')} {opp.get('value',0):,}</span></div>
    <div class="kv"><span class="k">Stage</span><span class="v">{opp.get('stage','new')}</span></div>
    <div class="kv"><span class="k">Close Date</span><span class="v">{opp.get('close_date','TBD')}</span></div>
    <div class="kv"><span class="k">Notes</span><span class="v" style="font-weight:400">{opp.get('notes','—')}</span></div>
  </div>

  <div class="card">
    <h2>MEDDPICC Score</h2>
    <div class="score-big">{score}<span style="font-size:24px;color:#9ca3af">/{max_s}</span></div>
    <div class="score-sub">{score_pct}% qualified</div>
    <div style="margin-top:16px">{meddpicc_bars}</div>
  </div>

  <div class="card">
    <h2>Contacts</h2>
    {contacts_html}
  </div>

  <div class="card">
    <h2>Intel</h2>
    {intel_html}
  </div>

  <div class="card full-width">
    <h2>Recent Activity</h2>
    {activity_html}
  </div>

  <div class="card full-width">
    <h2>Action Items</h2>
    <pre>{d.get('actions','')[:2000]}</pre>
  </div>

</div>
</body>
</html>"""

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

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
