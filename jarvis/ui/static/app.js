/* ── JARVIS Dashboard ────────────────────────────────────────── */
let _accounts  = [];
let _logTimer  = null;
let _pollTimer = null;
let _currentAccount = null;
let _intelFiles = [];

const STAGE_ORDER  = ['new_account','discovery','demo','proposal','negotiation','closed_won','closed_won_expansion','closed_lost'];
const STAGE_LABELS = { new_account:'New', discovery:'Discovery', demo:'Demo', proposal:'Proposal', negotiation:'Negotiation', closed_won:'Won ✓', closed_won_expansion:'Expansion', closed_lost:'Lost ✗' };
const ACT_ICONS    = { discovery:'🔍', demo:'🎬', email:'📧', meeting:'📅', document:'📄', meddpicc:'📊', proposal:'📝', conversation:'💬', opencode_conversation:'💬', document_processor:'📄', default:'⚡' };

// ── Boot ─────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  applyTheme(localStorage.getItem('theme') || 'dark');
  refreshAll();
  setInterval(refreshStats, 15_000);
  setInterval(refreshAccountsBackground, 20_000);
});

async function refreshAll() {
  await Promise.all([loadStatus(), loadStats(), loadAccounts()]);
  const v = document.querySelector('.view.active');
  if (v?.id === 'view-pipeline') renderPipeline();
  if (v?.id === 'view-accounts') renderTable(_accounts);
  if (v?.id === 'view-activity') loadActivity();
  if (v?.id === 'view-logs')     loadLogs();
  document.getElementById('lastRefresh').textContent = new Date().toLocaleTimeString();
}

async function refreshAccountsBackground() {
  const old = _accounts.length;
  await loadAccounts();
  if (_accounts.length !== old) refreshAll();
  else {
    const v = document.querySelector('.view.active');
    if (v?.id === 'view-pipeline') renderPipeline();
    if (v?.id === 'view-accounts') renderTable(_accounts);
  }
}

// ── Status ────────────────────────────────────────────────────
async function loadStatus() {
  try {
    const d = await get('/api/status');
    const dot = document.getElementById('statusDot');
    dot.className = 'status-dot ' + (d.running ? 'live' : 'offline');
    document.getElementById('statusLabel').textContent = d.running ? 'Live' : 'Stopped';
    document.getElementById('statusHome').textContent  = d.jarvis_home?.split('/').slice(-2).join('/') || '';
  } catch {}
}

// ── Stats ─────────────────────────────────────────────────────
async function refreshStats() {
  try {
    const d = await get('/api/stats');
    document.getElementById('totalAccounts').textContent = d.total_accounts ?? '—';
    document.getElementById('staleDeals').textContent    = d.stale_deals ?? '—';
    document.getElementById('avgMeddpicc').textContent   = d.avg_meddpicc_pct != null ? d.avg_meddpicc_pct + '%' : '—';
    document.getElementById('sideAccounts').textContent  = d.total_accounts ?? '—';
  } catch {}
}
async function loadStats() { return refreshStats(); }

// ── Accounts ──────────────────────────────────────────────────
async function loadAccounts() {
  try { _accounts = await get('/api/accounts'); } catch { _accounts = []; }
}

// ── Views ─────────────────────────────────────────────────────
function showView(name, el) {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('view-' + name)?.classList.add('active');
  el?.classList.add('active');
  const titles = { pipeline:['Pipeline','All active deals'], accounts:['Accounts','Full list'], activity:['Activity','Recent events'], logs:['Live Logs','Orchestrator output'], detail:['Account Detail',''] };
  const [t, s] = titles[name] || [name, ''];
  document.getElementById('pageTitle').textContent = t;
  document.getElementById('pageSub').textContent   = s;
  if (name === 'pipeline')  renderPipeline();
  if (name === 'accounts')  renderTable(_accounts);
  if (name === 'activity')  loadActivity();
  if (name === 'logs')      loadLogs();
  if (name !== 'logs' && _logTimer) { clearInterval(_logTimer); _logTimer = null; document.getElementById('autoLogCheck').checked = false; }
}

// ── Pipeline ──────────────────────────────────────────────────
function renderPipeline() {
  const board = document.getElementById('pipelineBoard');
  if (!_accounts.length) { board.innerHTML = '<div class="empty-state">No accounts found in JARVIS_HOME/ACCOUNTS/</div>'; return; }
  const grouped = {};
  STAGE_ORDER.forEach(s => grouped[s] = []);
  _accounts.forEach(a => { const s = a.stage || 'new_account'; (grouped[s] = grouped[s] || []).push(a); });
  const visibleStages = STAGE_ORDER.filter(s => (grouped[s]||[]).length > 0 || ['new_account','discovery','demo','proposal'].includes(s));
  board.innerHTML = visibleStages.map(stage => {
    const cards = grouped[stage] || [];
    return `<div class="stage-col">
      <div class="stage-col-header">
        <span class="stage-col-name">${STAGE_LABELS[stage] || stage}</span>
        <span class="stage-col-count">${cards.length}</span>
      </div>
      <div class="stage-cards">${cards.length ? cards.map(dealCard).join('') : '<div style="color:var(--text3);font-size:.72rem;padding:.35rem .2rem">Empty</div>'}</div>
    </div>`;
  }).join('');
  board.querySelectorAll('.deal-card').forEach(c => c.addEventListener('click', () => openAccount(c.dataset.name)));
}

function dealCard(a) {
  const dims = Object.values(a.meddpicc_dimensions || {});
  const dots = dims.map(v => `<div class="medd-dot${v > 0 ? ' on' : ''}"></div>`).join('');
  const stale = a.days_stale > 7 ? `<span class="stale-pill">⚠ ${a.days_stale}d</span>` : '';
  const intel = a.intel_count > 0 ? `<span class="intel-pill">📄 ${a.intel_count}</span>` : '';
  return `<div class="deal-card" data-name="${esc(a.name)}">
    <div class="deal-card-name">${esc(a.name)}</div>
    <div class="deal-card-bottom">
      <span class="deal-card-pct">${a.meddpicc_pct ?? 0}%</span>
      <div class="medd-dots">${dots}</div>
    </div>
    <div>${stale}${intel}</div>
  </div>`;
}

// ── Accounts Table ────────────────────────────────────────────
function filterTable() {
  const q = (document.getElementById('acctSearch').value || '').toLowerCase();
  const s = document.getElementById('stageSel').value;
  renderTable(_accounts.filter(a => (!q || a.name.toLowerCase().includes(q)) && (!s || a.stage === s)));
}
function renderTable(list) {
  const tbody = document.getElementById('acctTbody');
  if (!list.length) { tbody.innerHTML = '<tr><td colspan="9" class="empty-cell">No accounts</td></tr>'; return; }
  tbody.innerHTML = list.map(a => {
    const sb  = `<span class="badge badge-${a.stage||'new_account'}">${STAGE_LABELS[a.stage]||a.stage}</span>`;
    const mb  = `<div class="medd-bar"><div class="medd-track"><div class="medd-fill" style="width:${a.meddpicc_pct??0}%"></div></div><span class="medd-pct">${a.meddpicc_pct??0}%</span></div>`;
    const wp  = a.win_probability != null ? `<span class="win-pct ${winCls(a.win_probability)}">${a.win_probability}%</span>` : '<span style="color:var(--text3)">—</span>';
    const la  = a.last_activity ? `${a.last_activity.slice(0,10)} ${a.days_stale!=null?`<span style="color:var(--text3);font-size:.68rem">(${a.days_stale}d)</span>`:''}` : '<span style="color:var(--text3)">—</span>';
    const ic  = a.intel_count > 0 ? `<span class="intel-badge">📄 ${a.intel_count}</span>` : '<span style="color:var(--text3)">—</span>';
    const dc  = a.has_discovery ? '<span class="disc-yes">✓</span>' : '<span class="disc-no">—</span>';
    return `<tr onclick="openAccount('${esc(a.name)}')">
      <td><strong>${esc(a.name)}</strong></td><td>${sb}</td><td>${mb}</td><td>${wp}</td>
      <td>${la}</td><td>${a.contacts_count??0}</td><td>${ic}</td><td>${dc}</td>
      <td><button class="btn-open" onclick="event.stopPropagation();openAccount('${esc(a.name)}')">Open →</button></td>
    </tr>`;
  }).join('');
}

// ── Account Detail ────────────────────────────────────────────
async function openAccount(name) {
  _currentAccount = name;
  showView('detail', null);
  document.getElementById('pageTitle').textContent = name;
  document.getElementById('pageSub').textContent   = 'Account intelligence';
  document.getElementById('detailName').textContent = name;
  // Reset tabs
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('.tab[data-tab="overview"]').classList.add('active');
  document.getElementById('tab-overview').classList.add('active');
  document.getElementById('intelCount').textContent = '';
  try {
    const d = await get(`/api/accounts/${encodeURIComponent(name)}`);
    renderDetail(d);
    // Poll for updates every 12s while on this account
    if (_pollTimer) clearInterval(_pollTimer);
    _pollTimer = setInterval(async () => {
      if (_currentAccount !== name) return;
      const fresh = await get(`/api/accounts/${encodeURIComponent(name)}`);
      renderDetail(fresh);
    }, 12_000);
  } catch (e) {
    document.getElementById('detailName').textContent = name + ' — failed to load';
  }
}

function renderDetail(d) {
  // Header
  document.getElementById('detailStageBadge').className   = `badge badge-${d.stage||'new_account'}`;
  document.getElementById('detailStageBadge').textContent  = STAGE_LABELS[d.stage] || d.stage;
  document.getElementById('detailMeddBadge').textContent   = `MEDDPICC ${d.meddpicc_pct??0}%`;

  // Meta chips
  let chips = '';
  if (d.win_probability != null) chips += `<div class="chip"><span class="cv ${winCls(d.win_probability)}">${d.win_probability}%</span><span class="cl">win</span></div>`;
  if (d.days_stale > 7) chips += `<div class="chip chip-warn"><span class="cv">${d.days_stale}d</span><span class="cl">stale</span></div>`;
  if (d.arr) chips += `<div class="chip chip-blue"><span class="cv">${d.arr}</span><span class="cl">ARR</span></div>`;
  if (d.intel_count > 0) chips += `<div class="chip"><span class="cv" style="color:var(--cyan)">${d.intel_count}</span><span class="cl">intel files</span></div>`;
  document.getElementById('detailMetaChips').innerHTML = chips;

  // Intel tab count
  const ic = d.intel_files?.length || 0;
  document.getElementById('intelCount').textContent = ic > 0 ? ic : '';

  // ── Overview ──
  const dimNames = {metrics:'Metrics',economic_buyer:'Econ Buyer',decision_criteria:'Dec Criteria',decision_process:'Dec Process',paper_process:'Paper Proc',implicate_pain:'Imp Pain',champion:'Champion',competition:'Competition'};
  document.getElementById('ovCards').innerHTML = [
    { label:'MEDDPICC', val:`${d.meddpicc_pct??0}%`, sub:`${d.meddpicc_score??0}/${d.meddpicc_max??8}` },
    { label:'Win Probability', val:d.win_probability!=null?d.win_probability+'%':'—', cls:d.win_probability!=null?winCls(d.win_probability):'' },
    { label:'Last Activity', val:d.last_activity?.slice(0,10)||'—', sub:d.days_stale!=null?`${d.days_stale}d ago`:'' },
    { label:'Contacts', val:d.contacts_count??0 },
    { label:'Intel Files', val:d.intel_count||0, sub:'JARVIS researched' },
    { label:'Stage', val:STAGE_LABELS[d.stage]||d.stage||'—' },
  ].map(c => `<div class="ov-card"><div class="ov-label">${c.label}</div><div class="ov-val ${c.cls||''}">${c.val}</div>${c.sub?`<div class="ov-sub">${c.sub}</div>`:''}</div>`).join('');

  document.getElementById('meddGrid').innerHTML = Object.entries(dimNames).map(([k,label]) => {
    const v = d.meddpicc_dimensions?.[k] ?? 0;
    const cls = v === 0 ? 'medd-score-0' : v < 1 ? 'medd-score-low' : 'medd-score-ok';
    return `<div class="medd-dim"><span class="medd-dim-name">${label}</span><span class="medd-dim-score ${cls}">${v}</span></div>`;
  }).join('');

  renderMd('ovSummary', d.summary_md);
  renderMd('ovActions', d.actions?.content);

  const acts = d.activities || [];
  document.getElementById('ovActivity').innerHTML = acts.length
    ? acts.slice(0,12).map(a => `<div class="ov-act-item">
        <span class="ov-act-date">${String(a.timestamp||a.date||'').slice(0,16)}</span>
        <span class="ov-act-badge">${a.type||a.source||'event'}</span>
        <span class="ov-act-summary">${esc(a.summary||a.description||'')}</span>
      </div>`).join('')
    : '<div style="color:var(--text3);font-size:.8rem;padding:.5rem 0">No activities yet</div>';

  // ── Intel tab ──
  _intelFiles = d.intel_files || [];
  renderIntelGrid(_intelFiles);

  // ── Discovery ──
  renderMdSection('discPrep',  d.discovery?.prep,  'discPrepTime');
  renderMdSection('discNotes', d.discovery?.notes, 'discNotesTime');

  // ── Battlecard ──
  renderMdSection('bcMd', d.battlecard?.markdown, 'bcTime');
  const comps = d.battlecard?.data?.competitors || d.competitors || [];
  document.getElementById('bcComps').innerHTML = comps.length
    ? comps.map(c => `<span class="comp-tag">${esc(c)}</span>`).join('')
    : '<span style="color:var(--text3);font-size:.8rem">None identified yet</span>';
  const wp = d.win_probability;
  document.getElementById('winDisplay').innerHTML = `<div class="win-num ${wp!=null?winCls(wp):''}">${wp!=null?wp+'%':'—'}</div><div class="win-lbl">Win Probability</div>`;
  // Show battlecard raw data if available
  const bcData = d.battlecard?.data || {};
  const bcKeys = ['differentiators','objections','trap_questions'];
  let bcRawHtml = '';
  for (const k of bcKeys) {
    if (bcData[k]?.length) bcRawHtml += `<div class="sec-title" style="margin-top:.8rem">${k.replace(/_/g,' ')}</div><ul class="md-box" style="padding:.65rem 1rem">${bcData[k].map(i=>`<li style="font-size:.8rem;color:var(--text2);margin-bottom:.2rem">${esc(i)}</li>`).join('')}</ul>`;
  }
  document.getElementById('bcRaw').innerHTML = bcRawHtml;

  // ── Demo ──
  renderMdSection('demoStrat',  d.demo?.strategy, 'demoStratTime');
  renderMdSection('demoScript', d.demo?.script,   'demoScriptTime');

  // ── Value ──
  renderMdSection('roiMd', d.value?.roi, 'roiTime');
  renderMdSection('tcoMd', d.value?.tco);

  // ── Proposal ──
  const pd = d.proposal?.data || {};
  document.getElementById('propBanner').innerHTML = `<div class="prop-banner">
    <div>
      <strong>Status:</strong> ${pd.status||'Not generated'} &nbsp;
      <strong>Generated:</strong> ${d.proposal?.modified||'—'}
    </div>
    ${d.proposal?.html_exists
      ? `<button class="prop-btn" onclick="alert('Open: ~/JARVIS/ACCOUNTS/${esc(d.name)}/PROPOSAL/proposal.html')">Open HTML ↗</button>`
      : '<span style="color:var(--text3);font-size:.78rem">Not generated — ask Claude to generate proposal</span>'}
  </div>`;
  const propContent = pd.executive_summary
    ? `## Executive Summary\n${pd.executive_summary}\n\n**Solution:** ${pd.proposed_solution||'—'}\n\n**Pricing:** ${pd.pricing||'—'}`
    : '';
  renderMd('propMd', propContent);

  // ── Risk ──
  renderMdSection('riskMd', d.risk?.report, 'riskTime');

  // ── Contacts ──
  const contacts = d.contacts || [];
  document.getElementById('contactsGrid').innerHTML = contacts.length
    ? contacts.map(c => `<div class="contact-card">
        <div class="contact-name">${esc(c.name||'Unknown')}</div>
        <div class="contact-role">${esc(c.title||c.role||'')}</div>
        ${c.email ? `<div class="contact-email">${esc(c.email)}</div>` : ''}
        ${c.type  ? `<span class="badge badge-neutral" style="margin-top:.4rem">${esc(c.type)}</span>` : ''}
      </div>`).join('')
    : '<div class="no-contacts">No contacts yet — save discovery notes with contact names</div>';
}

// ── Intel Grid ────────────────────────────────────────────────
function renderIntelGrid(files) {
  const grid = document.getElementById('intelGrid');
  if (!files.length) { grid.innerHTML = '<div class="empty-state">No intel files yet — JARVIS populates this as you chat and add documents</div>'; return; }
  const icons = { md:'📄', json:'📊', txt:'📝' };
  grid.innerHTML = files.map((f, i) => {
    const ext = f.name.split('.').pop();
    const icon = icons[ext] || '📄';
    return `<div class="intel-card" onclick="openIntelModal(${i})">
      <div class="intel-card-head">
        <span class="intel-card-icon">${icon}</span>
        <span class="intel-card-name">${esc(f.name)}</span>
        <span class="intel-card-time">${f.modified}</span>
      </div>
      <div class="intel-card-preview">${esc(f.preview)}</div>
      <div class="intel-card-footer">
        <span>${f.size.toLocaleString()} chars</span>
        <span>Click to view full content</span>
      </div>
    </div>`;
  }).join('');
}

function filterIntel() {
  const q = (document.getElementById('intelSearch').value || '').toLowerCase();
  renderIntelGrid(q ? _intelFiles.filter(f => f.name.toLowerCase().includes(q) || f.preview.toLowerCase().includes(q)) : _intelFiles);
}

function openIntelModal(idx) {
  const f = _intelFiles[idx];
  if (!f) return;
  const overlay = document.createElement('div');
  overlay.className = 'intel-modal-overlay';
  overlay.innerHTML = `<div class="intel-modal">
    <div class="intel-modal-head">
      <span class="intel-modal-title">📄 ${esc(f.name)}</span>
      <button class="intel-modal-close" onclick="this.closest('.intel-modal-overlay').remove()">✕</button>
    </div>
    <div class="intel-modal-body"><div class="md-box" style="max-height:none;border:none;padding:0">${mdToHtml(f.content)}</div></div>
  </div>`;
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
}

function showTab(name, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  el?.classList.add('active');
  document.getElementById('tab-' + name)?.classList.add('active');
}

// ── Activity Feed ─────────────────────────────────────────────
async function loadActivity() {
  const list = document.getElementById('activityList');
  list.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    const items = await get('/api/activity?limit=80');
    if (!items.length) { list.innerHTML = '<div class="empty-state">No activity yet</div>'; return; }
    list.innerHTML = items.map(a => {
      const icon    = ACT_ICONS[a.type] || ACT_ICONS[a.source] || ACT_ICONS.default;
      const summary = a.summary || a.description || '';
      const isLong  = summary.length > 160;
      return `<div class="act-item">
        <div class="act-icon">${icon}</div>
        <div class="act-body">
          <div class="act-head">
            <span class="act-account">${esc(a.account||'')}</span>
            <span class="act-type">${esc(a.type||a.source||'')}</span>
            <span class="act-date">${String(a.timestamp||a.date||'').slice(0,16)}</span>
          </div>
          <div class="act-summary${isLong?' act-summary-long':''}">${esc(summary)}</div>
        </div>
      </div>`;
    }).join('');
  } catch { list.innerHTML = '<div class="empty-state">Failed to load</div>'; }
}

// ── Logs ──────────────────────────────────────────────────────
async function loadLogs() {
  const pre = document.getElementById('logPre');
  try {
    const d = await get('/api/logs?lines=120');
    const lines = d.lines || [];
    if (!lines.length) { pre.textContent = 'No log output yet'; return; }
    pre.innerHTML = lines.map(l => {
      if (/ERROR|error/.test(l))                              return `<span class="log-error">${esc(l)}</span>`;
      if (/WARN|warning/.test(l))                             return `<span class="log-warn">${esc(l)}</span>`;
      if (/Skill|trigger|skill\.trigger|Component started/.test(l)) return `<span class="log-skill">${esc(l)}</span>`;
      if (/INFO/.test(l))                                     return `<span class="log-info">${esc(l)}</span>`;
      return esc(l);
    }).join('\n');
    pre.scrollTop = pre.scrollHeight;
  } catch { pre.textContent = 'Failed to load logs'; }
}

function toggleAutoLogs() {
  const on = document.getElementById('autoLogCheck').checked;
  if (on) { _logTimer = setInterval(loadLogs, 5000); }
  else    { clearInterval(_logTimer); _logTimer = null; }
}

// ── Theme ─────────────────────────────────────────────────────
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  applyTheme(current === 'dark' ? 'light' : 'dark');
}
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  document.getElementById('themeToggle').textContent = t === 'dark' ? '🌙' : '☀️';
}

// ── Markdown ──────────────────────────────────────────────────
function renderMdSection(elId, section, timeElId) {
  if (timeElId && section?.modified) {
    const el = document.getElementById(timeElId);
    if (el) el.textContent = section.modified;
  }
  renderMd(elId, section?.content, section?.placeholder);
}

function renderMd(elId, content, placeholder) {
  const el = document.getElementById(elId);
  if (!el) return;
  const text = typeof content === 'string' ? content : (content?.content || '');
  const isPlaceholder = placeholder !== false && (!text || text.length < 30 ||
    ['*Generating...','*Waiting for','JARVIS is generating','Waiting for discovery'].some(m => text.includes(m)));

  if (isPlaceholder) {
    const isGenerating = text && text.includes('*Generating');
    el.innerHTML = `<div class="md-box-placeholder">
      <span class="ph-icon">${isGenerating ? '⏳' : '📭'}</span>
      <div class="ph-title ${isGenerating ? 'ph-generating' : ''}">${isGenerating ? 'JARVIS is generating this…' : 'Not generated yet'}</div>
      <div class="ph-sub">${isGenerating ? 'Waiting for NVIDIA LLM to complete' : 'Chat in this account folder to trigger generation'}</div>
    </div>`;
  } else {
    el.innerHTML = mdToHtml(text);
  }
}

function mdToHtml(md) {
  if (!md) return '';
  let html = md
    .replace(/```[\w]*\n?([\s\S]*?)```/g, (_,c) => `<pre><code>${esc(c.trim())}</code></pre>`)
    .replace(/^#{1} (.+)$/gm, '<h1>$1</h1>')
    .replace(/^#{2} (.+)$/gm, '<h2>$1</h2>')
    .replace(/^#{3} (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`([^`]+)`/g,     '<code>$1</code>')
    .replace(/^> (.+)$/gm,     '<blockquote>$1</blockquote>')
    .replace(/^---+$/gm,       '<hr/>')
    .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/^\d+\. (.+)$/gm, '<oli>$1</oli>')
    .replace(/(<oli>[\s\S]*?<\/oli>\n?)+/g, m => `<ol>${m.replace(/<\/?oli>/g, m2 => m2 === '<oli>' ? '<li>' : '</li>')}</ol>`);

  // Tables
  html = html.replace(/((?:\|.+\|\n?)+)/g, block => {
    const rows = block.trim().split('\n').filter(r => !/^\|[-|: ]+\|$/.test(r));
    if (!rows.length) return block;
    const cell = (r, tag) => `<tr>${r.split('|').filter((_,i,a) => i>0 && i<a.length-1).map(c => `<${tag}>${c.trim()}</${tag}>`).join('')}</tr>`;
    return `<table>${cell(rows[0],'th')}${rows.slice(1).map(r=>cell(r,'td')).join('')}</table>`;
  });

  // Paragraphs (skip lines that are already HTML)
  html = html.split('\n\n').map(p => {
    p = p.trim();
    if (!p || p.startsWith('<')) return p;
    return `<p>${p.replace(/\n/g, '<br/>')}</p>`;
  }).join('');
  return html;
}

// ── Helpers ───────────────────────────────────────────────────
async function get(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(r.status);
  return r.json();
}
function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function winCls(p) {
  if (p >= 65) return 'win-high';
  if (p >= 35) return 'win-mid';
  return 'win-low';
}
