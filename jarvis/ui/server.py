#!/usr/bin/env python3
"""
JARVIS Dashboard Server
Reads all account data from JARVIS_HOME and serves a live dashboard API.
"""

import http.server
import socketserver
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PORT = 8080
STATIC_DIR = Path(__file__).parent / "static"

# Resolve JARVIS_HOME dynamically — same logic as config.py
def get_jarvis_home() -> Path:
    env = os.environ.get("JARVIS_HOME") or os.environ.get("JARVIS_DATA_DIR")
    if env:
        return Path(env).expanduser()
    # Check .env in repo root
    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("JARVIS_HOME="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                return Path(val).expanduser()
    return Path.home() / "JARVIS"


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def get_accounts(jarvis_home: Path) -> list:
    accounts_dir = jarvis_home / "ACCOUNTS"
    if not accounts_dir.exists():
        return []
    accounts = []
    for entry in sorted(accounts_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        accounts.append(build_account_summary(entry))
    return accounts


def build_account_summary(account_dir: Path) -> dict:
    name = account_dir.name

    # MEDDPICC
    meddpicc = read_json(account_dir / "meddpicc.json") or {}
    score = meddpicc.get("score", 0)
    max_score = meddpicc.get("max_score", 8)

    # Deal stage
    stage_data = read_json(account_dir / "deal_stage.json") or {}
    stage = stage_data.get("stage", "new_account")
    stage_updated = stage_data.get("last_updated", "")

    # Activities (last activity)
    last_activity = None
    activities_file = account_dir / "activities.jsonl"
    if activities_file.exists():
        lines = activities_file.read_text().strip().splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                last_activity = last.get("date") or last.get("timestamp", "")
            except Exception:
                pass

    # Contacts
    contacts_data = read_json(account_dir / "contacts.json") or {}
    contacts = contacts_data.get("contacts", [])

    # Battlecard status
    bc_file = account_dir / "BATTLECARD" / "battlecard_data.json"
    bc_data = read_json(bc_file) or {}
    win_prob = bc_data.get("win_probability")

    # Discovery status
    disc_file = account_dir / "DISCOVERY" / "final_discovery.md"
    has_discovery = disc_file.exists() and len(read_text(disc_file)) > 200

    # Proposal status
    prop_file = account_dir / "PROPOSAL" / "proposal_data.json"
    prop_data = read_json(prop_file) or {}

    # Days since last activity
    days_stale = None
    if last_activity:
        try:
            date_str = last_activity[:10]
            delta = datetime.now() - datetime.strptime(date_str, "%Y-%m-%d")
            days_stale = delta.days
        except Exception:
            pass

    return {
        "name": name,
        "stage": stage,
        "stage_updated": stage_updated,
        "meddpicc_score": score,
        "meddpicc_max": max_score,
        "meddpicc_pct": round((score / max_score) * 100) if max_score else 0,
        "meddpicc_dimensions": {
            "metrics": meddpicc.get("metrics", 0),
            "economic_buyer": meddpicc.get("economic_buyer", 0),
            "decision_criteria": meddpicc.get("decision_criteria", 0),
            "decision_process": meddpicc.get("decision_process", 0),
            "paper_process": meddpicc.get("paper_process", 0),
            "implicate_pain": meddpicc.get("implicate_pain", 0),
            "champion": meddpicc.get("champion", 0),
            "competition": meddpicc.get("competition", 0),
        },
        "win_probability": win_prob,
        "last_activity": last_activity,
        "days_stale": days_stale,
        "contacts_count": len(contacts),
        "has_discovery": has_discovery,
        "proposal_status": prop_data.get("status", ""),
        "competitors": bc_data.get("competitors", []),
    }


def build_account_detail(account_dir: Path) -> dict:
    summary = build_account_summary(account_dir)

    # Discovery
    discovery = {
        "prep": read_text(account_dir / "DISCOVERY" / "discovery_prep.md"),
        "notes": read_text(account_dir / "DISCOVERY" / "final_discovery.md"),
    }

    # Battlecard
    battlecard = {
        "markdown": read_text(account_dir / "BATTLECARD" / "battlecard.md"),
        "data": read_json(account_dir / "BATTLECARD" / "battlecard_data.json") or {},
    }

    # Demo strategy
    demo = {
        "strategy": read_text(account_dir / "DEMO_STRATEGY" / "demo_strategy.md"),
        "script": read_text(account_dir / "DEMO_STRATEGY" / "demo_script.md"),
    }

    # Risk report
    risk = {
        "report": read_text(account_dir / "RISK_REPORT" / "risk_report.md"),
    }

    # Value architecture
    value = {
        "roi": read_text(account_dir / "VALUE_ARCHITECTURE" / "roi_model.md"),
        "tco": read_text(account_dir / "VALUE_ARCHITECTURE" / "tco_analysis.md"),
        "data": read_json(account_dir / "VALUE_ARCHITECTURE" / "value_data.json") or {},
    }

    # Proposal
    proposal = {
        "data": read_json(account_dir / "PROPOSAL" / "proposal_data.json") or {},
        "html_exists": (account_dir / "PROPOSAL" / "proposal.html").exists(),
    }

    # SOW
    sow = {"content": read_text(account_dir / "SOW" / "sow.md")}

    # Architecture
    arch = {
        "diagram": read_text(account_dir / "ARCHITECTURE" / "architecture_diagram.md"),
        "html_exists": (account_dir / "ARCHITECTURE" / "architecture_diagram.html").exists(),
    }

    # Contacts
    contacts_data = read_json(account_dir / "contacts.json") or {}

    # Next steps
    next_steps = {"content": read_text(account_dir / "NEXT_STEPS" / "next_steps.md")}

    # Recent activities
    activities = []
    act_file = account_dir / "activities.jsonl"
    if act_file.exists():
        lines = act_file.read_text().strip().splitlines()
        for line in reversed(lines[-20:]):
            try:
                activities.append(json.loads(line))
            except Exception:
                pass

    # Actions
    actions = {"content": read_text(account_dir / "actions.md")}

    return {
        **summary,
        "discovery": discovery,
        "battlecard": battlecard,
        "demo": demo,
        "risk": risk,
        "value": value,
        "proposal": proposal,
        "sow": sow,
        "architecture": arch,
        "contacts": contacts_data.get("contacts", []),
        "next_steps": next_steps,
        "activities": activities,
        "actions": actions,
        "summary_md": read_text(account_dir / "summary.md"),
    }


def get_pipeline(accounts: list) -> dict:
    stages = {
        "new_account": [],
        "discovery": [],
        "demo": [],
        "proposal": [],
        "negotiation": [],
        "closed_won": [],
        "closed_lost": [],
    }
    for acc in accounts:
        s = acc.get("stage", "new_account")
        if s not in stages:
            stages[s] = []
        stages[s].append(acc)
    return stages


def get_activity_feed(jarvis_home: Path, limit: int = 50) -> list:
    accounts_dir = jarvis_home / "ACCOUNTS"
    events = []
    if not accounts_dir.exists():
        return events
    for entry in accounts_dir.iterdir():
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        act_file = entry / "activities.jsonl"
        if act_file.exists():
            for line in act_file.read_text().strip().splitlines():
                try:
                    ev = json.loads(line)
                    ev["account"] = entry.name
                    events.append(ev)
                except Exception:
                    pass
    events.sort(key=lambda x: x.get("date") or x.get("timestamp", ""), reverse=True)
    return events[:limit]


def get_logs(jarvis_home: Path, lines: int = 80) -> list:
    log_file = jarvis_home / "logs" / "orchestrator.log"
    if not log_file.exists():
        return []
    all_lines = log_file.read_text(errors="replace").splitlines()
    return all_lines[-lines:]


def get_stats(accounts: list, jarvis_home: Path) -> dict:
    total = len(accounts)
    by_stage = {}
    stale = 0
    avg_meddpicc = 0
    for acc in accounts:
        s = acc.get("stage", "new_account")
        by_stage[s] = by_stage.get(s, 0) + 1
        if acc.get("days_stale") and acc["days_stale"] > 7:
            stale += 1
        avg_meddpicc += acc.get("meddpicc_pct", 0)
    avg_meddpicc = round(avg_meddpicc / total) if total else 0

    # Log file size as proxy for JARVIS activity
    log_lines = 0
    log_file = jarvis_home / "logs" / "orchestrator.log"
    if log_file.exists():
        log_lines = log_file.read_text(errors="replace").count("\n")

    return {
        "total_accounts": total,
        "by_stage": by_stage,
        "stale_deals": stale,
        "avg_meddpicc_pct": avg_meddpicc,
        "log_events": log_lines,
    }


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class DashboardHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.jarvis_home = get_jarvis_home()
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.serve_static("index.html")
        elif path.endswith(".css"):
            self.serve_static(path.lstrip("/"))
        elif path.endswith(".js"):
            self.serve_static(path.lstrip("/"))
        elif path.startswith("/api/"):
            self.handle_api(path, params)
        else:
            self.send_error(404)

    def serve_static(self, filename):
        try:
            p = STATIC_DIR / filename
            content = p.read_bytes()
            self.send_response(200)
            if filename.endswith(".html"):
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif filename.endswith(".css"):
                self.send_header("Content-Type", "text/css")
            elif filename.endswith(".js"):
                self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def handle_api(self, path, params):
        try:
            accounts = get_accounts(self.jarvis_home)

            if path == "/api/status":
                pid_running = False
                try:
                    pid = int((Path.cwd() / ".jarvis.pid").read_text().strip())
                    os.kill(pid, 0)
                    pid_running = True
                except Exception:
                    pass
                self.json_response({
                    "running": pid_running,
                    "jarvis_home": str(self.jarvis_home),
                    "timestamp": datetime.now().isoformat(),
                    "accounts_count": len(accounts),
                })

            elif path == "/api/accounts":
                self.json_response(accounts)

            elif path.startswith("/api/accounts/"):
                account_name = path.split("/api/accounts/")[1].rstrip("/")
                account_dir = self.jarvis_home / "ACCOUNTS" / account_name
                if account_dir.exists():
                    self.json_response(build_account_detail(account_dir))
                else:
                    self.json_response({"error": f"Account '{account_name}' not found"})

            elif path == "/api/pipeline":
                self.json_response(get_pipeline(accounts))

            elif path == "/api/activity":
                limit = int(params.get("limit", [50])[0])
                self.json_response(get_activity_feed(self.jarvis_home, limit))

            elif path == "/api/stats":
                self.json_response(get_stats(accounts, self.jarvis_home))

            elif path == "/api/logs":
                lines = int(params.get("lines", [80])[0])
                self.json_response({"lines": get_logs(self.jarvis_home, lines)})

            else:
                self.json_response({"error": "Unknown endpoint"})

        except Exception as e:
            self.json_response({"error": str(e)})

    def log_message(self, fmt, *args):
        pass  # silence access logs


def run():
    os.chdir(Path(__file__).parent.parent.parent)  # repo root for .jarvis.pid
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"JARVIS Dashboard → http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run()
