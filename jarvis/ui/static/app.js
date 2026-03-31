/* ── JARVIS Dashboard ────────────────────────────────────────── */

const API = '';   // same origin
let _accounts = [];
let _logsTimer = null;
let _statsTimer = null;

// ── Boot ─────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  refreshAll();
  _statsTimer = setInterval(refreshStats, 30_000);
});

async function refreshAll() {
  await Promise.all([loadStatus(), loadStats(), loadAccounts()]);
  const active = document.querySelector('.view.active');
  if (active?.id === 'view-pipeline')  renderPipeline();
  if (active?.id === 'view-accounts')  renderAccountsTable();
  if (active?.id === 'view-activity')  loadActivity();
  if (active?.id === 'view-logs')      loadLogs();
  document.getElementById('lastRefresh').textContent = new Date().toLocaleTimeString();
}

// ── Status ───────────────────────────────────────────────────
async function loadStatus() {
  try {
    const d = await apiFetch('/api/status');
    const dot   = document.getElementById('statusDot');
    const label = document.getElementById('statusLabel');
    dot.className   = 'status-dot ' + (d.running ? 'live' : 'offline');
    label.textContent = d.running ? 'Live' : 'Stopped';
    document.getElementById('jarvisHomePath').textContent = d.jarvis_home || '—';
  } catch { /* ignore */ }
}

// ── Stats ────────────────────────────────────────────────────
async function refreshStats() {
  try {
    const d = await apiFetch('/api/stats');
    document.getElementById('totalAccounts').textContent = d.total_accounts ?? '—';
    document.getElementById('staleDeals').textContent    = d.stale_deals ?? '—';
    document.getElementById('avgMeddpicc').textContent   = d.avg_meddpicc_pct != null ? d.avg_meddpicc_pct + '%' : '—';
  } catch { /* ignore */ }
}
async function loadStats() { return refreshStats(); }

// ── Accounts ─────────────────────────────────────────────────
async function loadAccounts() {
  try { _accounts = await apiFetch('/api/accounts'); } catch { _accounts = []; }
}

// ── Views ─────────────────────────────────────────────────────
function showView(name, el) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const view = document.getElementById('view-' + name);
  if (view) view.classList.add('active');
  if (el) el.classList.add('active');
  const titles = {
    pipeline: ['Pipeline', 'All active deals'],
    accounts: ['Accounts', 'Full account list'],
    activity: ['Activity Feed', 'Recent JARVIS events'],
    logs:     ['Live Logs',  'Orchestrator output'],
    detail:   ['Account Detail', ''],
  };
  const [title, sub] = titles[name] || [name, ''];
  document.getElementById('pageTitle').textContent = title;
  document.getElementById('pageSub').textContent   = sub;

  if (name === 'pipeline')  renderPipeline();
  if (name === 'accounts')  renderAccountsTable();
  if (name === 'activity')  loadActivity();
  if (name === 'logs')      loadLogs();
  if (name !== 'logs' && _logsTimer) { clearInterval(_logsTimer); _logsTimer = null; }
}

// ── Pipeline ─────────────────────────────────────────────────
const STAGE_ORDER = ['new_account','discovery','demo','proposal','negotiation','closed_won','closed_lost'];
const STAGE_LABELS = {
  new_account:'New', discovery:'Discovery', demo:'Demo',
  proposal:'Proposal', negotiation:'Negotiation',
  closed_won:'Won ✓', closed_lost:'Lost ✗',
};

function renderPipeline() {
  const board = document.getElementById('pipelineBoard');
  if (!_accounts.length) { board.innerHTML = '<div class="loading-msg">No accounts found in JARVIS_HOME/ACCOUNTS/</div>'; return; }
  const byStage = {};
  STAGE_ORDER.forEach(s => byStage[s] = []);
  _accounts.forEach(a => { const s = a.stage || 'new_account'; (byStage[s] = byStage[s] || []).push(a); });

  board.innerHTML = STAGE_ORDER.map(stage => {
    const cards = (byStage[stage] || []);
    const cardsHtml = cards.length
      ? cards.map(a => dealCard(a)).join('')
      : '<div style="color:var(--text3);font-size:.75rem;padding:.4rem .2rem">—</div>';
    return `<div class="stage-col">
      <div class="stage-col-header">
        <span class="stage-col-name">${STAGE_LABELS[stage]}</span>
        <span class="stage-col-count">${cards.length}</span>
      </div>
      <div class="stage-cards">${cardsHtml}</div>
    </div>`;
  }).join('');

  board.querySelectorAll('.deal-card').forEach(card => {
    card.addEventListener('click', () => openAccount(card.dataset.name));
  });
}

function dealCard(a) {
  const dims = a.meddpicc_dimensions || {};
  const dots = Object.values(dims).map(v => `<div class="medd-mini-dot${v > 0 ? ' filled' : ''}"></div>`).join('');
  const stale = a.days_stale != null && a.days_stale > 7
    ? `<div class="stale-flag">⚠ ${a.days_stale}d stale</div>` : '';
  return `<div class="deal-card" data-name="${esc(a.name)}">
    <div class="deal-card-name">${esc(a.name)}</div>
    <div class="deal-card-meta">
      <span class="deal-card-medd">MEDD ${a.meddpicc_pct ?? 0}%</span>
      <div class="medd-mini">${dots}</div>
    </div>
    ${stale}
  </div>`;
}

// ── Accounts Table ───────────────────────────────────────────
function renderAccountsTable() {
  renderTableRows(_accounts);
}

function filterTable() {
  const q = document.getElementById('acctSearch').value.toLowerCase();
  const s = document.getElementById('stageSel').value;
  const filtered = _accounts.filter(a => {
    const matchName  = !q || a.name.toLowerCase().includes(q);
    const matchStage = !s || a.stage === s;
    return matchName && matchStage;
  });
  renderTableRows(filtered);
}

function renderTableRows(list) {
  const tbody = document.getElementById('acctTbody');
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">No accounts found</td></tr>';
    return;
  }
  tbody.innerHTML = list.map(a => {
    const stageBadge = `<span class="badge badge-${a.stage || 'new_account'}">${STAGE_LABELS[a.stage] || a.stage}</span>`;
    const meddBar = `<div class="medd-bar-wrap">
      <div class="medd-bar-track"><div class="medd-bar-fill" style="width:${a.meddpicc_pct ?? 0}%"></div></div>
      <span class="medd-bar-pct">${a.meddpicc_pct ?? 0}%</span>
    </div>`;
    const winPct = a.win_probability != null
      ? `<span class="win-pct ${winClass(a.win_probability)}">${a.win_probability}%</span>`
      : '<span style="color:var(--text3)">—</span>';
    const lastAct = a.last_activity
      ? `${a.last_activity}${a.days_stale != null ? ` <span style="color:var(--text3);font-size:.68rem">(${a.days_stale}d)</span>` : ''}`
      : '<span style="color:var(--text3)">Never</span>';
    const disc = a.has_discovery
      ? '<span class="disc-check">✓</span>'
      : '<span class="disc-empty">—</span>';
    return `<tr onclick="openAccount('${esc(a.name)}')">
      <td><strong>${esc(a.name)}</strong></td>
      <td>${stageBadge}</td>
      <td>${meddBar}</td>
      <td>${winPct}</td>
      <td>${lastAct}</td>
      <td>${a.contacts_count ?? 0}</td>
      <td>${disc}</td>
      <td><button class="open-btn" onclick="event.stopPropagation();openAccount('${esc(a.name)}')">Open →</button></td>
    </tr>`;
  }).join('');
}

// ── Account Detail ───────────────────────────────────────────
async function openAccount(name) {
  showView('detail', null);
  document.getElementById('pageTitle').textContent = name;
  document.getElementById('pageSub').textContent   = 'Account intelligence';
  document.getElementById('detailName').textContent = name;

  // reset tabs
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('.tab[data-tab="overview"]').classList.add('active');
  document.getElementById('tab-overview').classList.add('active');

  try {
    const d = await apiFetch(`/api/accounts/${encodeURIComponent(name)}`);
    renderAccountDetail(d);
  } catch (e) {
    document.getElementById('detailName').textContent = name + ' — Error loading';
  }
}

function renderAccountDetail(d) {
  // Header badges
  document.getElementById('detailBadge').className = `badge badge-${d.stage || 'new_account'}`;
  document.getElementById('detailBadge').textContent = STAGE_LABELS[d.stage] || d.stage;
  document.getElementById('detailMeddpiccBadge').className = 'badge badge-grey';
  document.getElementById('detailMeddpiccBadge').textContent = `MEDDPICC ${d.meddpicc_pct ?? 0}%`;

  // Win chip
  const chips = document.getElementById('detailChips');
  chips.innerHTML = d.win_probability != null
    ? `<span class="chip"><span class="chip-val ${winClass(d.win_probability)}">${d.win_probability}%</span><span class="chip-lbl">win</span></span>`
    : '';
  if (d.days_stale != null && d.days_stale > 7) {
    chips.innerHTML += `<span class="chip chip-warn"><span class="chip-val">${d.days_stale}d</span><span class="chip-lbl">stale</span></span>`;
  }

  // ── Overview tab ──
  const dims = d.meddpicc_dimensions || {};
  const dimNames = { metrics:'Metrics', economic_buyer:'Econ Buyer', decision_criteria:'Dec Criteria',
    decision_process:'Dec Process', paper_process:'Paper Proc', implicate_pain:'Imp Pain',
    champion:'Champion', competition:'Competition' };

  document.getElementById('overviewCards').innerHTML = [
    { label: 'MEDDPICC', val: `${d.meddpicc_pct ?? 0}%`, sub: `${d.meddpicc_score ?? 0}/${d.meddpicc_max ?? 8}` },
    { label: 'Win Probability', val: d.win_probability != null ? d.win_probability + '%' : '—', cls: d.win_probability != null ? winClass(d.win_probability) : '' },
    { label: 'Last Activity', val: d.last_activity || '—', sub: d.days_stale != null ? `${d.days_stale} days ago` : '' },
    { label: 'Contacts', val: d.contacts_count ?? 0 },
  ].map(c => `<div class="ov-card">
    <div class="ov-card-label">${c.label}</div>
    <div class="ov-card-val ${c.cls || ''}">${c.val}</div>
    ${c.sub ? `<div class="ov-card-sub">${c.sub}</div>` : ''}
  </div>`).join('');

  document.getElementById('meddDims').innerHTML = Object.entries(dimNames).map(([k, label]) => {
    const v = dims[k] ?? 0;
    const cls = v === 0 ? 'zero' : v < 1 ? 'low' : 'high';
    return `<div class="medd-dim">
      <span class="medd-dim-name">${label}</span>
      <span class="medd-dim-score ${cls}">${v}</span>
    </div>`;
  }).join('');

  renderMd('overviewSummary', d.summary_md || '');

  const acts = d.activities || [];
  document.getElementById('overviewActivities').innerHTML = acts.length
    ? acts.slice(0, 10).map(a => `<div class="ov-activity-item">
        <span class="ov-act-date">${a.date || '—'}</span>
        <span class="ov-act-type">${a.type || ''}</span>
        <span class="ov-act-summary">${esc(a.summary || '')}</span>
      </div>`).join('')
    : '<div style="color:var(--text3);font-size:.8rem;padding:.5rem 0">No activities recorded yet</div>';

  // ── Discovery tab ──
  renderMd('discPrep',   d.discovery?.prep);
  renderMd('discNotes',  d.discovery?.notes);

  // ── Battlecard tab ──
  renderMd('bcMd', d.battlecard?.markdown);
  const comps = d.battlecard?.data?.competitors || d.competitors || [];
  document.getElementById('bcCompetitors').innerHTML = comps.length
    ? comps.map(c => `<span class="comp-tag">${esc(c)}</span>`).join('')
    : '<span style="color:var(--text3);font-size:.8rem">None identified yet</span>';

  const wp = d.win_probability;
  const wCls = wp != null ? winClass(wp) : '';
  document.getElementById('winRing').innerHTML = `
    <div class="win-ring-num ${wCls}">${wp != null ? wp + '%' : '—'}</div>
    <div class="win-ring-label">Win Probability</div>`;

  // ── Demo tab ──
  renderMd('demoStrat',  d.demo?.strategy);
  renderMd('demoScript', d.demo?.script);

  // ── Value tab ──
  renderMd('roiModel',  d.value?.roi);
  renderMd('tcoModel',  d.value?.tco);

  // ── Proposal tab ──
  const pd = d.proposal?.data || {};
  document.getElementById('proposalWrap').innerHTML = `
    <div class="proposal-wrap">
      <div class="prop-status">
        <strong>Status:</strong> ${pd.status || 'Not generated yet'} &nbsp;
        <strong>Generated:</strong> ${pd.generated_at ? pd.generated_at.slice(0,10) : '—'}
      </div>
      ${d.proposal?.html_exists
        ? `<button class="prop-open-btn" onclick="alert('Open ACCOUNTS/${esc(d.name)}/PROPOSAL/proposal.html in your browser')">Open HTML Proposal ↗</button>`
        : '<span style="color:var(--text3);font-size:.78rem">HTML not generated yet — ask Claude to generate proposal</span>'}
    </div>`;
  renderMd('proposalMd', pd.executive_summary
    ? `**Executive Summary:**\n${pd.executive_summary}\n\n**Solution:** ${pd.proposed_solution || '—'}`
    : '');

  // ── Risk tab ──
  renderMd('riskMd', d.risk?.report);

  // ── Contacts tab ──
  const contacts = d.contacts || [];
  document.getElementById('contactsGrid').innerHTML = contacts.length
    ? contacts.map(c => `<div class="contact-card">
        <div class="contact-name">${esc(c.name || 'Unknown')}</div>
        <div class="contact-title">${esc(c.title || c.role || '')}</div>
        ${c.email ? `<div class="contact-email">${esc(c.email)}</div>` : ''}
        ${c.type ? `<span class="badge badge-grey contact-role">${esc(c.type)}</span>` : ''}
      </div>`).join('')
    : '<div class="no-contacts">No contacts saved yet — update discovery notes with contact names</div>';
}

function showTab(name, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  if (el) el.classList.add('active');
  const pane = document.getElementById('tab-' + name);
  if (pane) pane.classList.add('active');
}

// ── Activity Feed ─────────────────────────────────────────────
async function loadActivity() {
  const list = document.getElementById('activityList');
  list.innerHTML = '<div class="loading-msg">Loading…</div>';
  try {
    const items = await apiFetch('/api/activity?limit=60');
    if (!items.length) { list.innerHTML = '<div class="loading-msg">No activity recorded yet</div>'; return; }
    const icons = { discovery:'🔍', demo:'🎬', email:'📧', meeting:'📅', document:'📄', meddpicc:'📊', proposal:'📝', default:'⚡' };
    list.innerHTML = items.map(a => {
      const icon = icons[a.type] || icons.default;
      return `<div class="activity-item">
        <div class="activity-icon">${icon}</div>
        <div class="activity-body">
          <div class="activity-header">
            <span class="activity-account">${esc(a.account || '')}</span>
            <span class="activity-type">${esc(a.type || '')}</span>
            <span class="activity-date">${a.date || a.timestamp || '—'}</span>
          </div>
          <div class="activity-summary">${esc(a.summary || a.description || '')}</div>
        </div>
      </div>`;
    }).join('');
  } catch { list.innerHTML = '<div class="loading-msg">Failed to load activity</div>'; }
}

// ── Logs ─────────────────────────────────────────────────────
async function loadLogs() {
  const pre = document.getElementById('logPre');
  try {
    const d = await apiFetch('/api/logs?lines=100');
    const lines = d.lines || [];
    if (!lines.length) { pre.textContent = 'No log output yet'; return; }
    pre.innerHTML = lines.map(l => {
      if (/ERROR|error/.test(l))   return `<span style="color:var(--red)">${esc(l)}</span>`;
      if (/WARN|warning/.test(l))  return `<span style="color:var(--yellow)">${esc(l)}</span>`;
      if (/INFO/.test(l))          return `<span style="color:var(--text2)">${esc(l)}</span>`;
      if (/started|Skill|trigger|Component/.test(l)) return `<span style="color:var(--green)">${esc(l)}</span>`;
      return esc(l);
    }).join('\n');
    pre.scrollTop = pre.scrollHeight;
  } catch { pre.textContent = 'Failed to load logs'; }
}

function toggleAutoLogs() {
  const checked = document.getElementById('autoRefreshCheck').checked;
  if (checked) {
    _logsTimer = setInterval(loadLogs, 5000);
  } else {
    clearInterval(_logsTimer);
    _logsTimer = null;
  }
}

// ── Markdown renderer (lightweight) ──────────────────────────
function renderMd(elId, md) {
  const el = document.getElementById(elId);
  if (!el) return;
  if (!md || md.trim().length < 10 || md.includes('*Generating...') || md.includes('*Waiting')) {
    el.innerHTML = '<div class="md-empty">Not generated yet — JARVIS will populate this after discovery data is saved</div>';
    return;
  }
  el.innerHTML = mdToHtml(md);
}

function mdToHtml(md) {
  return md
    // fenced code blocks
    .replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) => `<pre><code>${esc(code.trim())}</code></pre>`)
    // headings
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    // bold + italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>')
    .replace(/_(.+?)_/g,           '<em>$1</em>')
    // inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // unordered lists
    .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    // ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // horizontal rule
    .replace(/^---+$/gm, '<hr/>')
    // blockquote
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    // simple table (| a | b | → table)
    .replace(/((?:\|.+\|\n?)+)/g, m => {
      const rows = m.trim().split('\n').filter(r => !r.match(/^\|[-| ]+\|$/));
      if (rows.length < 1) return m;
      const toRow = (r, tag) => `<tr>${r.split('|').filter((_,i,a)=>i>0&&i<a.length-1).map(c=>`<${tag}>${c.trim()}</${tag}>`).join('')}</tr>`;
      return `<table>${toRow(rows[0],'th')}${rows.slice(1).map(r=>toRow(r,'td')).join('')}</table>`;
    })
    // paragraphs
    .replace(/\n\n+/g, '</p><p>')
    .replace(/^(.+)$/gm, (m) => m.startsWith('<') ? m : m)
    .replace(/^(?!<)(.+)/gm, '$1')
    // wrap in paragraphs properly
    .split('\n\n').map(p => {
      p = p.trim();
      if (!p) return '';
      if (p.startsWith('<')) return p;
      return `<p>${p}</p>`;
    }).join('');
}

// ── Helpers ───────────────────────────────────────────────────
async function apiFetch(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function winClass(pct) {
  if (pct >= 65) return 'high';
  if (pct >= 35) return 'mid';
  return 'low';
}
