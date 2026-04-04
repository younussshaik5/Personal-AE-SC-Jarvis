#!/usr/bin/env python3
"""
JARVIS CRM Dashboard Server — VP-Grade Deal Intelligence
Auto-generates skill outputs. Persists a job queue across restarts.
Loads ALL account data: deal_stage.json + all skill output .md files.

Run: python3 serve_crm.py
"""

import json
import os
import re
import sys
import asyncio
import logging
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

# ── Path setup so jarvis_mcp imports work ────────────────────────────────────
_here = Path(__file__).parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

# Load .env
def _load_env():
    env_file = _here / ".env"
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file, override=False)
        return
    except ImportError:
        pass
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

_load_env()

logging.basicConfig(level=logging.INFO, format="[CRM] %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

# ── ACCOUNTS root ─────────────────────────────────────────────────────────────
_env_root = os.getenv("ACCOUNTS_ROOT", "")
_candidates = [
    Path(_env_root) if _env_root else None,
    _here / "ACCOUNTS",
    Path.home() / "Documents" / "claude space" / "ACCOUNTS",
    Path.cwd() / "ACCOUNTS",
]
ACCOUNTS_ROOT = next((p for p in _candidates if p and p.exists()), _here / "ACCOUNTS")

# ── Skill output file registry ────────────────────────────────────────────────
SKILL_FILES = {
    "account_summary":          {"file": "account_summary.md",          "label": "Executive Summary",      "icon": "briefcase",  "cmd": "get_account_summary"},
    "quick_insights":           {"file": "quick_insights.md",           "label": "Quick Insights",         "icon": "zap",        "cmd": "quick_insights"},
    "battlecard":               {"file": "battlecard.md",               "label": "Battlecard",             "icon": "swords",     "cmd": "get_battlecard"},
    "meddpicc":                 {"file": "meddpicc.md",                 "label": "MEDDPICC Analysis",      "icon": "target",     "cmd": "track_meddpicc"},
    "risk_report":              {"file": "risk_report.md",              "label": "Risk Report",            "icon": "alert",      "cmd": "get_risk_report"},
    "value_architecture":       {"file": "value_architecture.md",       "label": "Value Architecture",     "icon": "layers",     "cmd": "get_value_architecture"},
    "competitive_intelligence": {"file": "competitive_intelligence.md", "label": "Competitive Intel",      "icon": "eye",        "cmd": "get_competitive_intelligence"},
    "competitor_pricing":       {"file": "competitor_pricing.md",       "label": "Pricing Analysis",       "icon": "dollar",     "cmd": "analyze_competitor_pricing"},
    "meeting_prep":             {"file": "meeting_prep.md",             "label": "Meeting Prep",           "icon": "calendar",   "cmd": "get_meeting_prep"},
    "demo_strategy":            {"file": "demo_strategy.md",            "label": "Demo Strategy",          "icon": "play",       "cmd": "get_demo_strategy"},
    "proposal":                 {"file": "proposal.md",                 "label": "Proposal",               "icon": "file-text",  "cmd": "get_proposal"},
    "followup_email":           {"file": "followup_email.md",           "label": "Follow-up Email",        "icon": "mail",       "cmd": "generate_followup"},
    "technical_risk":           {"file": "technical_risk.md",           "label": "Technical Risk",         "icon": "cpu",        "cmd": "assess_technical_risk"},
    "sow":                      {"file": "sow.md",                      "label": "Statement of Work",      "icon": "clipboard",  "cmd": "generate_sow"},
    "discovery_questions":      {"file": "discovery_questions.md",      "label": "Discovery Questions",    "icon": "search",     "cmd": "get_discovery"},
}

# ── Queue manager ─────────────────────────────────────────────────────────────
_queue = None
_llm = None
_config = None

def _init_queue():
    global _queue, _llm, _config
    try:
        from jarvis_mcp.queue_manager import QueueManager
        from jarvis_mcp.config.config_manager import ConfigManager
        from jarvis_mcp.llm.llm_manager import LLMManager
        _config = ConfigManager()
        _llm = LLMManager(_config)
        _queue = QueueManager()
        log.info("Queue manager initialized")
    except Exception as e:
        log.warning(f"Queue manager unavailable (skills won't auto-generate): {e}")

def _queue_status() -> dict:
    if _queue:
        return _queue.get_status()
    return {"pending": 0, "processing": 0, "done": 0, "failed": 0, "total": 0, "is_active": False, "by_account": {}}

def _add_to_queue(account: str, skill_key: str) -> str:
    if _queue:
        return _queue.add_job(account, skill_key, priority=1)
    return ""

# ── Background queue worker ───────────────────────────────────────────────────
_worker_lock = threading.Lock()

def _queue_worker():
    """Background thread: processes queue, then watches for new jobs every 30s."""
    # Give the server a moment to start
    time.sleep(3)

    # Scan for missing skills on startup
    if _queue:
        changed = _queue.scan_changed_files(ACCOUNTS_ROOT)
        missing = _queue.scan_missing_skills(ACCOUNTS_ROOT, SKILL_FILES)
        if changed + missing:
            log.info(f"Startup scan: {changed} changed files, {missing} missing skills queued")

    while True:
        with _worker_lock:
            pending = _queue.get_pending() if _queue else []
            if pending:
                log.info(f"Processing {len(pending)} queued jobs…")
                try:
                    asyncio.run(_run_queue_async())
                except Exception as e:
                    log.error(f"Queue processing error: {e}")
        time.sleep(30)

async def _run_queue_async():
    if _queue and _llm and _config:
        await _queue.process_all(_llm, _config)

# ── Data helpers ──────────────────────────────────────────────────────────────

def sanitize(text, max_len=None):
    if not text:
        return ""
    cleaned = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t\r')
    return cleaned[:max_len] if max_len else cleaned


def _has_real_content(text, min_lines=4):
    """Return True only if text contains at least min_lines of actual prose —
    not just headings (##), separators (---), or blank lines."""
    import re as _re
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith('#') and not _re.match(r'^-{2,}$', s):
            count += 1
            if count >= min_lines:
                return True
    return False


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def parse_md_sections(md):
    sections = {}
    cur = "intro"
    lines = []
    for line in md.split('\n'):
        if line.startswith('## '):
            if lines:
                sections[cur] = '\n'.join(lines).strip()
            cur = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    if lines:
        sections[cur] = '\n'.join(lines).strip()
    return sections


def extract_bullets(text):
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(('- ', '* ', '• ')):
            items.append(line[2:].strip())
        elif re.match(r'^\d+\.?\s', line):
            items.append(re.sub(r'^\d+\.?\s*', '', line).strip())
    return items


def compute_meddpicc(deal, disc_sec, claude_sec, stakeholders):
    score = {}
    success = disc_sec.get('Success Criteria', '')
    score['metrics'] = min(10, len(extract_bullets(success)) * 2) if success else 0

    # Stakeholders can be list of strings OR list of dicts — handle both
    def _s_str(s):
        if isinstance(s, dict):
            return ' '.join(str(v) for v in s.values()).lower()
        return str(s).lower()

    has_budget_holder = any(k in _s_str(s) for s in stakeholders for k in ['cfo', 'budget', 'finance', 'ceo', 'president'])
    score['economic_buyer'] = 10 if has_budget_holder else (3 if stakeholders else 0)

    criteria = disc_sec.get('Key Pain Points to Address', '') or disc_sec.get('Key Challenges', '') or disc_sec.get('Business Drivers', '')
    score['decision_criteria'] = min(10, len(extract_bullets(criteria)) * 2) if criteria else 0

    process = disc_sec.get('Decision Drivers', '') or disc_sec.get('Budget & Timeline', '')
    score['decision_process'] = 8 if process else 2

    stage = deal.get('stage', '').lower()
    has_legal = any(k in _s_str(s) for s in stakeholders for k in ['procurement', 'legal', 'contract'])
    score['paper_process'] = 9 if 'negotiate' in stage or 'close' in stage else (6 if has_legal else 2)

    pain = disc_sec.get('Business Drivers', '') or disc_sec.get('Key Challenges', '')
    score['implications'] = min(10, len(extract_bullets(pain)) * 2) if pain else 0

    has_champ = any(k in str(v).lower() for v in [str(disc_sec), str(claude_sec)] for k in ['champion', 'advocate', 'sponsor'])
    score['champion'] = 7 if has_champ else (5 if claude_sec.get('Account Context', '') else 1)

    comp = deal.get('competitive_situation', {})
    comp_sec = disc_sec.get('Competitive Landscape', '')
    score['competition'] = (8 if comp_sec else 6) if (comp.get('primary_competitor', 'TBD') != 'TBD') else 1

    score['total'] = sum(score.values())
    score['max'] = 80
    score['percentage'] = round((score['total'] / 80) * 100)
    return score


def compute_risks(deal, disc_sec, meddpicc):
    risks = []
    prob = deal.get('probability', 0)
    size = deal.get('deal_size', 0)
    comp = deal.get('competitive_situation', {})

    if meddpicc.get('economic_buyer', 0) < 5:
        risks.append({'level': 'high', 'cat': 'Stakeholder', 'text': 'No economic buyer identified — budget approval at risk'})
    if prob < 0.3 and size > 500000:
        risks.append({'level': 'high', 'cat': 'Pipeline', 'text': f'Low win probability ({int(prob * 100)}%) on ${size:,.0f} deal'})
    cs = comp.get('competitor_status', '').lower()
    if 'incumbent' in cs or 'strong' in cs:
        risks.append({'level': 'high', 'cat': 'Competition', 'text': f'Strong competitor: {comp.get("primary_competitor", "")} ({cs})'})
    if meddpicc.get('percentage', 0) < 40:
        risks.append({'level': 'medium', 'cat': 'Qualification', 'text': f'MEDDPICC {meddpicc["percentage"]}% — deal under-qualified'})
    if meddpicc.get('champion', 0) < 4:
        risks.append({'level': 'medium', 'cat': 'Champion', 'text': 'No internal champion identified'})
    if meddpicc.get('competition', 0) < 3:
        risks.append({'level': 'low', 'cat': 'Competition', 'text': 'Competitive landscape unknown'})
    return risks


def parse_meddpicc_scores(content):
    """Parse JARVIS-generated meddpicc.md for per-dimension RED/AMBER/GREEN scores.
    Falls back to 0 if a section is missing or empty."""
    if not content or len(content.strip()) < 100:
        return None
    rating = {'GREEN': 9, 'AMBER': 5, 'RED': 2}
    dim_aliases = {
        'metrics':          ['metrics', 'metric'],
        'economic_buyer':   ['economic buyer', 'economic'],
        'decision_criteria':['decision criteria'],
        'decision_process': ['decision process'],
        'paper_process':    ['paper process', 'paper'],
        'implications':     ['implication', 'pain'],
        'champion':         ['champion'],
        'competition':      ['competition', 'compet'],
    }
    sections = parse_md_sections(content)
    score = {}
    for dim, aliases in dim_aliases.items():
        sec_content = next(
            (v for k, v in sections.items() if any(a in k.lower() for a in aliases)),
            ''
        )
        m = re.search(r'\*{0,2}Score\*{0,2}\s*[:\*]+\s*\*{0,2}(RED|AMBER|GREEN)\*{0,2}',
                      sec_content, re.IGNORECASE)
        if m:
            score[dim] = rating[m.group(1).upper()]
        elif sec_content.strip() and len(sec_content.strip()) > 30:
            score[dim] = 4  # has content but no explicit score → mid-AMBER
        else:
            score[dim] = 0
    if not any(score.values()):
        return None   # nothing parsed — fall back to computed
    total = sum(score.values())
    score['total'] = total
    score['max'] = 80
    score['percentage'] = round((total / 80) * 100)
    return score


def compute_discovery(disc_sec, full_text=''):
    areas = ['Company Background', 'Business Drivers', 'Key Challenges', 'Technical Environment',
             'Success Criteria', 'Budget & Timeline', 'Key Stakeholders', 'Competitive Landscape', 'Decision Drivers']
    # Keywords that signal each area is covered — searched in full discovery text
    signals = {
        'Company Background':    ['company name', 'industry:', 'revenue:', 'hq:', 'employees:', 'founded'],
        'Business Drivers':      ['business driver', 'business goal', 'pain point', 'problem', 'initiative'],
        'Key Challenges':        ['challenge', 'blocker', 'pain point', 'risk', 'key challenge'],
        'Technical Environment': ['tech stack', 'technical', 'infrastructure', 'platform', 'integration', 'email'],
        'Success Criteria':      ['success criter', 'kpi', 'roi', 'outcome', 'quantif', 'payback'],
        'Budget & Timeline':     ['budget', 'timeline', 'arr', 'fiscal', 'deal size', 'forecast', 'apr 2026'],
        'Key Stakeholders':      ['stakeholder', 'champion', 'economic buyer', 'ravi', 'cfo', 'vp '],
        'Competitive Landscape': ['competitor', 'competitive', 'incumbent', 'alternative', 'in-house'],
        'Decision Drivers':      ['decision driver', 'decision process', 'evaluation', 'paper process', 'procurement'],
    }
    text_lower = full_text.lower()
    found, missing = 0, []
    for area in areas:
        has_section = any(area.lower() in k.lower() for k in disc_sec if disc_sec.get(k, '').strip())
        has_keyword = any(sig in text_lower for sig in signals.get(area, [area.lower()]))
        if has_section or has_keyword:
            found += 1
        else:
            missing.append(area)
    return {'completed': found, 'total': len(areas),
            'percentage': round((found / len(areas)) * 100), 'missing': missing}


def load_account(folder, name, parent=None):
    dsf = folder / "deal_stage.json"
    if not dsf.exists():
        return None
    try:
        with open(dsf, 'r', encoding='utf-8') as f:
            deal = json.load(f)
    except Exception:
        return None

    company_md = sanitize(read_file(folder / "company_research.md"))
    discovery_md = sanitize(read_file(folder / "discovery.md"))
    claude_md = sanitize(read_file(folder / "CLAUDE.md"))

    co_sec = parse_md_sections(company_md)
    disc_sec = parse_md_sections(discovery_md)
    cl_sec = parse_md_sections(claude_md)

    stakeholders = deal.get("stakeholders", [])

    # Use JARVIS-generated meddpicc.md scores when available; fall back to computed
    meddpicc_md = sanitize(read_file(folder / "meddpicc.md"))
    meddpicc = parse_meddpicc_scores(meddpicc_md) or \
               compute_meddpicc(deal, {**disc_sec, **co_sec}, cl_sec, stakeholders)

    risks = compute_risks(deal, disc_sec, meddpicc)
    # Pass full discovery text so keyword signals in appended intel are counted
    disc_comp = compute_discovery(disc_sec, discovery_md)

    # Next actions: deal_stage.json open_actions first, then CLAUDE.md, then account_summary.md
    _raw_open = deal.get("open_actions", []) or deal.get("next_actions", [])
    next_actions = [
        (f"{a.get('action','')} [{a.get('owner','')} · {a.get('deadline','')}]" if isinstance(a, dict) else str(a))
        for a in _raw_open if a
    ] if _raw_open else []
    if not next_actions:
        next_actions = extract_bullets(cl_sec.get('Next Actions', '') or cl_sec.get('Next Steps', ''))
    if not next_actions:
        sum_md = sanitize(read_file(folder / "account_summary.md"))
        if sum_md:
            sum_sec = parse_md_sections(sum_md)
            for key, text in sum_sec.items():
                if any(k in key.lower() for k in ('action', 'next step', 'recommendation')):
                    next_actions = extract_bullets(text)
                    if not next_actions:
                        for line in text.split('\n'):
                            line = line.strip().lstrip('#').strip()
                            if len(line) > 25:
                                next_actions = [line[:200]]
                                break
                    if next_actions:
                        break

    pain_points = extract_bullets(cl_sec.get('Key Pain Points to Address', ''))

    prog = []
    for line in cl_sec.get('Deal Progression', '').split('\n'):
        line = line.strip()
        if not line:
            continue
        status = ('completed' if any(c in line for c in ['✅', '✓']) else
                  'current' if '🔄' in line else
                  'pending' if '⏳' in line else 'unknown')
        clean = re.sub(r'[✅✓🔄⏳\-\*]', '', line).strip()
        if clean:
            prog.append({'name': clean, 'status': status})

    # Minimum bytes of content to count as "generated" — files with only
    # section headers (67–104 bytes) are treated as failed and re-queued.
    _MIN_SKILL_BYTES = 200

    skill_outputs = {}
    for skill_key, skill_info in SKILL_FILES.items():
        filepath = folder / skill_info["file"]
        if filepath.exists():
            content = sanitize(read_file(filepath))
            if (content.strip()
                    and len(content.strip()) >= _MIN_SKILL_BYTES
                    and _has_real_content(content)):
                skill_outputs[skill_key] = content

    # Queue status for this account
    queue_status = {}
    if _queue:
        q = _queue.get_status()
        queue_status = q.get("by_account", {}).get(name, [])

    return {
        "id": name.lower().replace("/", "_").replace(" ", "_"),
        "name": deal.get("account_name", name),
        "folder": name,
        "path": str(folder),
        "parent": parent,
        "stage": deal.get("stage", "Unknown"),
        "probability": deal.get("probability", 0),
        "deal_size": deal.get("deal_size") or deal.get("arr", 0),
        "timeline": deal.get("timeline", "TBD"),
        "last_updated": deal.get("last_updated", "Unknown"),
        "stakeholders": stakeholders,
        "competitive_situation": deal.get("competitive_situation", {}),
        "activities": [
            (f"{a.get('date','')} — {a.get('type','')}: {a.get('notes','')}" if isinstance(a, dict) else str(a))
            for a in deal.get("activities", [])
        ],
        "constraints": deal.get("constraints", []),
        "next_milestone": deal.get("next_milestone", {}),
        "company_info": sanitize(company_md),
        "discovery_notes": sanitize(discovery_md, 5000),
        "account_rules_md": sanitize(claude_md, 3000),
        "meddpicc": meddpicc,
        "risks": risks,
        "discovery_completeness": disc_comp,
        "next_actions": next_actions,
        "deal_progression": prog,
        "pain_points": pain_points,
        "skill_outputs": skill_outputs,
        "skills_generated": len(skill_outputs),
        "skills_total": len(SKILL_FILES),
        "skills_queued": queue_status,
    }


def load_accounts_data():
    accounts = []
    if not ACCOUNTS_ROOT.exists():
        return {"accounts": [], "pipeline_summary": {}, "skill_registry": SKILL_FILES, "queue": _queue_status()}

    for af in sorted(ACCOUNTS_ROOT.iterdir()):
        if not af.is_dir() or af.name.startswith('.'):
            continue
        d = load_account(af, af.name)
        if d:
            accounts.append(d)
            for sf in sorted(af.iterdir()):
                if sf.is_dir() and not sf.name.startswith('.'):
                    sd = load_account(sf, f"{af.name}/{sf.name}", parent=af.name)
                    if sd:
                        accounts.append(sd)

    open_accts = [a for a in accounts if a['stage'].lower() not in ('closed won', 'closed lost')]
    won_accts  = [a for a in accounts if a['stage'].lower() == 'closed won']
    lost_accts = [a for a in accounts if a['stage'].lower() == 'closed lost']

    tp = sum(a['deal_size'] for a in open_accts)
    tw = sum(a['deal_size'] * a['probability'] for a in open_accts)
    am = round(sum(a['meddpicc']['percentage'] for a in accounts) / len(accounts)) if accounts else 0
    hr = sum(1 for a in accounts for r in a['risks'] if r['level'] == 'high')

    stages = {}
    for a in accounts:
        s = a['stage']
        if s not in stages:
            stages[s] = {'count': 0, 'value': 0}
        stages[s]['count'] += 1
        stages[s]['value'] += a['deal_size']

    total_closed = len(won_accts) + len(lost_accts)

    return {
        "accounts": accounts,
        "pipeline_summary": {
            'total_accounts': len(accounts),
            'open_accounts': len(open_accts),
            'total_pipeline': tp,
            'total_weighted': tw,
            'avg_meddpicc': am,
            'high_risks': hr,
            'total_skills_generated': sum(a['skills_generated'] for a in accounts),
            'stages': stages,
            'won_count': len(won_accts),
            'lost_count': len(lost_accts),
            'total_won': sum(a['deal_size'] for a in won_accts),
            'total_lost': sum(a['deal_size'] for a in lost_accts),
            'win_rate': round(len(won_accts) / total_closed * 100) if total_closed else 0,
            'avg_deal_size': round(tp / len(open_accts)) if open_accts else 0,
            'pipeline_coverage': round(tp / tw, 1) if tw > 0 else 0,
        },
        "skill_registry": {k: {"label": v["label"], "icon": v["icon"], "cmd": v["cmd"]} for k, v in SKILL_FILES.items()},
        "queue": _queue_status(),
    }


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class CRMHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/api/accounts":
            self._json(load_accounts_data())
        elif self.path == "/api/queue":
            self._json(_queue_status())
        elif self.path in ("/", ""):
            self._serve_file(_here / "crm.html", "text/html")
        else:
            fpath = _here / self.path.lstrip("/")
            if fpath.exists() and fpath.is_file():
                mime = "text/css" if self.path.endswith(".css") else \
                       "application/javascript" if self.path.endswith(".js") else \
                       "text/html"
                self._serve_file(fpath, mime)
            else:
                self.send_error(404)

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            account = body.get("account", "")
            skill = body.get("skill", "")
            if account and skill:
                job_id = _add_to_queue(account, skill)
                self._json({"queued": True, "job_id": job_id})
            elif account and not skill:
                # Queue all missing skills for this account
                folder = ACCOUNTS_ROOT / account.replace("/", os.sep)
                count = 0
                for sk, si in SKILL_FILES.items():
                    if not (folder / si["file"]).exists():
                        _add_to_queue(account, sk)
                        count += 1
                self._json({"queued": True, "count": count})
            else:
                self._json({"error": "account required"}, 400)
        elif self.path == "/api/generate/all":
            count = 0
            if _queue:
                count = _queue.scan_missing_skills(ACCOUNTS_ROOT, SKILL_FILES)
            self._json({"queued": True, "count": count})
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=True).encode()
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path, mime):
        try:
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-type", mime)
            self._cors()
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_error(500)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        pass  # suppress access logs


# ── Entry point ───────────────────────────────────────────────────────────────

def start_server(port=None):
    port = port or int(os.getenv("CRM_PORT", "8000"))

    # Initialize queue
    _init_queue()

    # Start background worker
    t = threading.Thread(target=_queue_worker, daemon=True)
    t.start()

    httpd = HTTPServer(("", port), CRMHandler)
    log.info(f"CRM Dashboard → http://localhost:{port}")
    log.info(f"ACCOUNTS: {ACCOUNTS_ROOT}")
    log.info(f"Skills tracked: {len(SKILL_FILES)}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Stopped.")
        httpd.server_close()


if __name__ == "__main__":
    start_server()
