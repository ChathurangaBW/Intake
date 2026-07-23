from __future__ import annotations

import json
from html import escape

from sqlalchemy.orm import Session


CONSOLE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Intake Operator Console</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #070b14;
      --panel: #0f172a;
      --panel-2: #111827;
      --line: #243244;
      --text: #e5eefb;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --good: #22c55e;
      --warn: #f59e0b;
      --bad: #ef4444;
      --chip: #172554;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at top left, #172554 0, var(--bg) 34rem);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      position: sticky;
      top: 0;
      z-index: 20;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.25rem;
      background: rgba(7, 11, 20, 0.88);
      backdrop-filter: blur(18px);
      border-bottom: 1px solid var(--line);
    }
    h1 { margin: 0; font-size: 1.35rem; letter-spacing: -0.02em; }
    h2 { margin: 0 0 0.75rem; font-size: 1.05rem; }
    h3 { margin: 1rem 0 0.45rem; font-size: 0.95rem; color: #cbd5e1; }
    p { color: var(--muted); line-height: 1.5; }
    main { padding: 1.25rem; max-width: 1500px; margin: 0 auto; }
    .topbar { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
    .layout { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 1rem; align-items: start; }
    .panel {
      background: rgba(15, 23, 42, 0.86);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 1rem;
      box-shadow: 0 24px 70px rgba(0, 0, 0, 0.18);
    }
    .stack { display: grid; gap: 1rem; }
    .grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .card { background: var(--panel-2); border: 1px solid var(--line); border-radius: 14px; padding: 0.85rem; }
    .card strong { display: block; font-size: 1.55rem; }
    .card span { color: var(--muted); font-size: 0.85rem; }
    label { display: block; margin: 0.65rem 0 0.3rem; color: #cbd5e1; font-size: 0.85rem; }
    input, textarea, select, button {
      width: 100%;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #020617;
      color: var(--text);
      padding: 0.65rem 0.7rem;
      font: inherit;
    }
    textarea { min-height: 92px; resize: vertical; }
    button { cursor: pointer; background: #0c4a6e; border-color: #0369a1; font-weight: 650; }
    button.secondary { background: #111827; border-color: var(--line); }
    button.danger { background: #7f1d1d; border-color: #991b1b; }
    button.inline { width: auto; padding: 0.45rem 0.7rem; font-size: 0.85rem; }
    button:disabled { opacity: 0.55; cursor: not-allowed; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { border-bottom: 1px solid var(--line); text-align: left; padding: 0.6rem; vertical-align: top; }
    th { color: #cbd5e1; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; }
    tr:hover td { background: rgba(15, 23, 42, 0.72); }
    code, pre { background: #020617; border: 1px solid var(--line); border-radius: 10px; }
    code { padding: 0.1rem 0.3rem; }
    pre { padding: 0.85rem; overflow: auto; max-height: 360px; }
    .muted { color: var(--muted); }
    .row { display: flex; gap: 0.55rem; flex-wrap: wrap; align-items: center; }
    .row > * { flex: 1; min-width: 120px; }
    .pill { display: inline-flex; align-items: center; gap: 0.35rem; background: var(--chip); border: 1px solid #1d4ed8; color: #bfdbfe; padding: 0.25rem 0.55rem; border-radius: 999px; font-size: 0.75rem; }
    .pill.good { background: #052e16; border-color: #166534; color: #bbf7d0; }
    .pill.warn { background: #451a03; border-color: #92400e; color: #fde68a; }
    .pill.bad { background: #450a0a; border-color: #991b1b; color: #fecaca; }
    .nav { display: grid; gap: 0.35rem; }
    .nav button { text-align: left; background: transparent; border-color: transparent; color: #cbd5e1; }
    .nav button.active { background: #082f49; border-color: #075985; color: #e0f2fe; }
    .section { display: none; }
    .section.active { display: block; }
    .notice { border: 1px solid #854d0e; background: rgba(69, 26, 3, .65); color: #fef3c7; padding: 0.75rem; border-radius: 14px; }
    .split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 0.7fr); gap: 1rem; }
    .small { font-size: 0.82rem; }
    .hidden { display: none !important; }
    @media (max-width: 980px) { .layout, .split { grid-template-columns: 1fr; } header { align-items: flex-start; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Intake Operator Console</h1>
      <div class="muted small">Policy-gated workbench for authorized engagements, evidence, approvals, jobs, reports, and exports.</div>
    </div>
    <div class="topbar">
      <input id="apiKey" type="password" placeholder="Optional API key" autocomplete="off" style="min-width:240px">
      <button class="inline secondary" id="saveKey">Save key</button>
      <button class="inline" id="refreshAll">Refresh</button>
      <a class="pill" href="/docs">OpenAPI</a>
    </div>
  </header>

  <main class="layout">
    <aside class="stack">
      <section class="panel">
        <h2>Navigation</h2>
        <div class="nav" id="nav">
          <button data-section="overview" class="active">Overview</button>
          <button data-section="engagements">Engagements</button>
          <button data-section="artifacts">Artifacts</button>
          <button data-section="tools">Tools & jobs</button>
          <button data-section="approvals">Approvals</button>
          <button data-section="findings">Findings</button>
          <button data-section="evidence">Evidence</button>
          <button data-section="ops">Ops & exports</button>
        </div>
      </section>

      <section class="panel">
        <h2>Active engagement</h2>
        <select id="activeEngagement"></select>
        <p class="small muted">Most console actions use this engagement. Create one first if the list is empty.</p>
      </section>

      <section class="panel">
        <h2>System status</h2>
        <div id="statusBox" class="stack small"></div>
      </section>
    </aside>

    <section class="stack">
      <div class="notice">Authorized systems only. This console does not add unrestricted shell execution, destructive workflows, persistence, evasion, or unscoped network activity.</div>

      <section id="overview" class="section active panel">
        <h2>Overview</h2>
        <div class="cards" id="statsCards"></div>
        <div class="split">
          <div>
            <h3>Recent engagements</h3>
            <div id="engagementTable"></div>
          </div>
          <div>
            <h3>Readiness</h3>
            <pre id="readinessOutput">Loading...</pre>
          </div>
        </div>
      </section>

      <section id="engagements" class="section panel">
        <h2>Engagements</h2>
        <div class="grid">
          <form id="createEngagement" class="panel">
            <h3>Create engagement</h3>
            <label>ID</label><input name="engagement_id" placeholder="eng-demo" required>
            <label>Name</label><input name="name" placeholder="Demo Authorized Assessment" required>
            <label>Classification</label><input name="classification" value="internal">
            <label>Manifest JSON</label><textarea name="manifest">{}</textarea>
            <button>Create</button>
          </form>
          <form id="addTarget" class="panel">
            <h3>Add target</h3>
            <label>Target reference</label><input name="target_ref" placeholder="app.authorized-example.test" required>
            <label>Target type</label><select name="target_type"><option>domain</option><option>ip</option><option>cidr</option><option>application</option><option>repository</option><option>binary</option></select>
            <label>Metadata JSON</label><textarea name="metadata">{}</textarea>
            <button>Add target</button>
          </form>
        </div>
        <h3>Targets</h3><div id="targetTable"></div>
      </section>

      <section id="artifacts" class="section panel">
        <h2>Artifacts</h2>
        <div class="grid">
          <form id="uploadArtifact" class="panel">
            <h3>Upload artifact</h3>
            <label>File</label><input name="file" type="file" required>
            <button>Upload</button>
          </form>
          <div class="panel">
            <h3>Artifact inventory</h3>
            <div id="artifactTable"></div>
          </div>
        </div>
      </section>

      <section id="tools" class="section panel">
        <h2>Tools & jobs</h2>
        <div class="grid">
          <form id="proposeTool" class="panel">
            <h3>Propose tool call</h3>
            <label>Actor</label><input name="actor" value="operator">
            <label>Tool</label><input name="tool" value="ghidra" required>
            <label>Operation</label><input name="operation" value="analyze" required>
            <label>Risk</label><select name="risk"><option>read_only</option><option>network</option><option>dynamic_execution</option><option>destructive</option></select>
            <label>Arguments JSON</label><textarea name="arguments">{"artifact_id":"<artifact-id>","profile":"quick"}</textarea>
            <button>Propose</button>
          </form>
          <form id="executeTool" class="panel">
            <h3>Execute authorized call</h3>
            <label>Tool call ID</label><input name="tool_call_id" placeholder="tool-call-id" required>
            <button>Execute</button>
          </form>
        </div>
        <h3>Tool status</h3><div id="toolStatusTable"></div>
        <h3>Tool calls</h3><div id="toolCallTable"></div>
      </section>

      <section id="approvals" class="section panel">
        <h2>Approvals</h2>
        <div id="approvalTable"></div>
      </section>

      <section id="findings" class="section panel">
        <h2>Findings</h2>
        <div class="grid">
          <form id="createFinding" class="panel">
            <h3>Create finding</h3>
            <label>Title</label><input name="title" required>
            <label>Severity</label><select name="severity"><option>informational</option><option>low</option><option>medium</option><option>high</option><option>critical</option></select>
            <label>Description</label><textarea name="description" required></textarea>
            <label>Evidence IDs JSON array</label><textarea name="evidence_ids">[]</textarea>
            <button>Create finding</button>
          </form>
          <div class="panel">
            <h3>Findings</h3><div id="findingTable"></div>
          </div>
        </div>
      </section>

      <section id="evidence" class="section panel">
        <h2>Evidence</h2>
        <div class="grid">
          <form id="recordEvidence" class="panel">
            <h3>Record text evidence</h3>
            <label>Summary</label><input name="summary" placeholder="operator note">
            <label>Media type</label><input name="media_type" value="text/plain">
            <label>Data</label><textarea name="data" required></textarea>
            <label>Metadata JSON</label><textarea name="metadata">{}</textarea>
            <button>Store evidence</button>
          </form>
          <div class="panel">
            <h3>Evidence records</h3><div id="evidenceTable"></div>
          </div>
        </div>
      </section>

      <section id="ops" class="section panel">
        <h2>Operations & exports</h2>
        <div class="grid">
          <div class="panel stack">
            <h3>Diagnostics</h3>
            <button id="runReadiness">Run readiness</button>
            <button id="verifyEvidence">Verify evidence inventory</button>
          </div>
          <div class="panel stack">
            <h3>Exports</h3>
            <button id="downloadReport">Download Markdown report</button>
            <button id="downloadEngagementExport">Download engagement export</button>
            <button id="downloadAudit">Download audit NDJSON</button>
          </div>
        </div>
        <h3>Output</h3><pre id="opsOutput">No operation run yet.</pre>
      </section>

      <section class="panel">
        <h2>Last response</h2>
        <pre id="lastResponse">Ready.</pre>
      </section>
    </section>
  </main>

<script>
const initialEngagement = __INITIAL_ENGAGEMENT__;
const state = { engagements: [], active: initialEngagement || null };
const $ = (id) => document.getElementById(id);
const show = (value) => { $('lastResponse').textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); };
const headers = (json = true) => {
  const h = {};
  const key = localStorage.getItem('intakeApiKey') || '';
  if (json) h['content-type'] = 'application/json';
  if (key) h['x-intake-api-key'] = key;
  return h;
};
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...headers(!(options.body instanceof FormData)), ...(options.headers || {}) } });
  const type = response.headers.get('content-type') || '';
  const data = type.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
  return data;
}
function badge(value) {
  const text = String(value ?? 'unknown');
  const cls = /ok|allow|authorized|completed|approved|healthy|true/i.test(text) ? 'good' : /pending|queued|warn|degraded/i.test(text) ? 'warn' : /fail|deny|error|false|blocked/i.test(text) ? 'bad' : '';
  return `<span class="pill ${cls}">${escapeHtml(text)}</span>`;
}
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function table(rows, columns, empty='No records.') {
  if (!rows || !rows.length) return `<p class="muted">${empty}</p>`;
  return `<table><thead><tr>${columns.map(c => `<th>${escapeHtml(c.label)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${columns.map(c => `<td>${c.render ? c.render(row) : escapeHtml(row[c.key])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
function activeEngagement() { return $('activeEngagement').value || state.active || ''; }
function setActive(id) { state.active = id; $('activeEngagement').value = id || ''; refreshEngagementScoped(); }
async function refreshAll() {
  await Promise.allSettled([refreshStats(), refreshEngagements(), refreshReadiness(), refreshTools(), refreshApprovals()]);
  await refreshEngagementScoped();
}
async function refreshStats() {
  const stats = await api('/stats');
  $('statsCards').innerHTML = Object.entries(stats).map(([k,v]) => `<div class="card"><strong>${escapeHtml(v)}</strong><span>${escapeHtml(k.replaceAll('_',' '))}</span></div>`).join('');
}
async function refreshEngagements() {
  const rows = await api('/engagements');
  state.engagements = rows;
  $('engagementTable').innerHTML = table(rows, [
    {label:'ID', render:r => `<button class="inline secondary" onclick="setActive('${escapeHtml(r.id)}')">${escapeHtml(r.id)}</button>`},
    {label:'Name', key:'name'}, {label:'Status', render:r=>badge(r.status)}, {label:'Class', key:'classification'}
  ], 'No engagements yet.');
  $('activeEngagement').innerHTML = rows.map(r => `<option value="${escapeHtml(r.id)}">${escapeHtml(r.id)} — ${escapeHtml(r.name)}</option>`).join('');
  if (!state.active && rows[0]) state.active = rows[0].id;
  if (state.active) $('activeEngagement').value = state.active;
}
async function refreshEngagementScoped() {
  const id = activeEngagement();
  if (!id) return;
  await Promise.allSettled([refreshTargets(id), refreshArtifacts(id), refreshToolCalls(id), refreshFindings(id), refreshEvidence(id)]);
}
async function refreshTargets(id) {
  const rows = await api(`/engagements/${encodeURIComponent(id)}/targets`);
  $('targetTable').innerHTML = table(rows, [{label:'Ref', key:'target_ref'}, {label:'Type', key:'target_type'}, {label:'ID', key:'id'}], 'No targets.');
}
async function refreshArtifacts(id) {
  const rows = await api(`/engagements/${encodeURIComponent(id)}/artifacts`);
  $('artifactTable').innerHTML = table(rows, [
    {label:'ID', key:'id'}, {label:'SHA256', render:r=>`<code>${escapeHtml(r.sha256).slice(0,16)}…</code>`}, {label:'Size', key:'size_bytes'}, {label:'Type', key:'media_type'}
  ], 'No artifacts.');
}
async function refreshToolCalls(id) {
  const rows = await api(`/engagements/${encodeURIComponent(id)}/tool-calls`);
  $('toolCallTable').innerHTML = table(rows, [
    {label:'ID', key:'id'}, {label:'Tool', key:'tool'}, {label:'Operation', key:'operation'}, {label:'Risk', key:'risk'}, {label:'Status', render:r=>badge(r.status)},
    {label:'Action', render:r=>`<button class="inline" onclick="executeCall('${escapeHtml(r.id)}')">Execute</button>`}
  ], 'No tool calls.');
}
async function refreshFindings(id) {
  const rows = await api(`/engagements/${encodeURIComponent(id)}/findings`);
  $('findingTable').innerHTML = table(rows, [{label:'Title', key:'title'}, {label:'Severity', render:r=>badge(r.severity)}, {label:'Status', key:'status'}, {label:'Verification', key:'verification_status'}], 'No findings.');
}
async function refreshEvidence(id) {
  const rows = await api(`/engagements/${encodeURIComponent(id)}/evidence`);
  $('evidenceTable').innerHTML = table(rows, [
    {label:'ID', key:'id'}, {label:'SHA256', render:r=>`<code>${escapeHtml(r.sha256).slice(0,16)}…</code>`}, {label:'Summary', key:'summary'}, {label:'Download', render:r=>`<a href="/evidence/${escapeHtml(r.id)}/download">download</a>`}
  ], 'No evidence.');
}
async function refreshTools() {
  const rows = await api('/tools/status');
  $('toolStatusTable').innerHTML = table(rows, [{label:'Name', key:'name'}, {label:'Operation', key:'operation'}, {label:'Available', render:r=>badge(r.available)}, {label:'Runtime', key:'runtime'}, {label:'Detail', key:'detail'}], 'No tools.');
}
async function refreshApprovals() {
  const rows = await api('/approvals/pending');
  $('approvalTable').innerHTML = table(rows, [
    {label:'ID', key:'id'}, {label:'Tool call', key:'tool_call_id'}, {label:'Requested by', key:'requested_by'}, {label:'Status', render:r=>badge(r.status)},
    {label:'Decision', render:r=>`<button class="inline" onclick="decideApproval('${escapeHtml(r.id)}', true)">Approve</button> <button class="inline danger" onclick="decideApproval('${escapeHtml(r.id)}', false)">Reject</button>`}
  ], 'No pending approvals.');
}
async function refreshReadiness() {
  try {
    const data = await api('/ops/readiness');
    $('readinessOutput').textContent = JSON.stringify(data, null, 2);
    $('statusBox').innerHTML = `<div>${badge(data.status || 'unknown')} readiness</div><div class="muted">Version: ${escapeHtml(data.version || 'unknown')}</div>`;
  } catch (err) {
    $('readinessOutput').textContent = String(err);
    $('statusBox').innerHTML = `<div>${badge('degraded')} readiness unavailable</div>`;
  }
}
async function executeCall(id) {
  const data = await api(`/tool-calls/${encodeURIComponent(id)}/execute`, { method:'POST', body:'{}' });
  show(data); await refreshAll();
}
async function decideApproval(id, approved) {
  const data = await api(`/approvals/${encodeURIComponent(id)}/decision`, { method:'POST', body: JSON.stringify({approved, decided_by:'operator', reason: approved ? 'approved in console' : 'rejected in console'}) });
  show(data); await refreshAll();
}
function parseJsonField(form, name, fallback) {
  const raw = new FormData(form).get(name);
  if (!raw) return fallback;
  return JSON.parse(raw);
}
function download(path) { window.open(path, '_blank', 'noopener,noreferrer'); }
function bindForms() {
  $('createEngagement').addEventListener('submit', async e => {
    e.preventDefault(); const f=e.currentTarget; const fd=new FormData(f);
    const data = await api('/engagements', { method:'POST', body: JSON.stringify({engagement_id:fd.get('engagement_id'), name:fd.get('name'), classification:fd.get('classification') || 'internal', manifest:parseJsonField(f,'manifest',{})}) });
    show(data); state.active = data.id; await refreshAll();
  });
  $('addTarget').addEventListener('submit', async e => {
    e.preventDefault(); const id=activeEngagement(); const f=e.currentTarget; const fd=new FormData(f);
    const data = await api(`/engagements/${encodeURIComponent(id)}/targets`, { method:'POST', body: JSON.stringify({target_ref:fd.get('target_ref'), target_type:fd.get('target_type'), metadata:parseJsonField(f,'metadata',{})}) });
    show(data); await refreshEngagementScoped();
  });
  $('uploadArtifact').addEventListener('submit', async e => {
    e.preventDefault(); const id=activeEngagement(); const fd=new FormData(e.currentTarget);
    const data = await api(`/engagements/${encodeURIComponent(id)}/artifacts`, { method:'POST', body: fd, headers: {} });
    show(data); await refreshEngagementScoped();
  });
  $('proposeTool').addEventListener('submit', async e => {
    e.preventDefault(); const id=activeEngagement(); const f=e.currentTarget; const fd=new FormData(f);
    const payload = {engagement_id:id, actor:fd.get('actor'), tool:fd.get('tool'), operation:fd.get('operation'), risk:fd.get('risk'), arguments:parseJsonField(f,'arguments',{})};
    const data = await api('/tool-calls', { method:'POST', body: JSON.stringify(payload) }); show(data); await refreshAll();
  });
  $('executeTool').addEventListener('submit', async e => { e.preventDefault(); await executeCall(new FormData(e.currentTarget).get('tool_call_id')); });
  $('createFinding').addEventListener('submit', async e => {
    e.preventDefault(); const id=activeEngagement(); const f=e.currentTarget; const fd=new FormData(f);
    const data = await api(`/engagements/${encodeURIComponent(id)}/findings`, { method:'POST', body: JSON.stringify({title:fd.get('title'), severity:fd.get('severity'), description:fd.get('description'), evidence_ids:parseJsonField(f,'evidence_ids',[])}) }); show(data); await refreshEngagementScoped();
  });
  $('recordEvidence').addEventListener('submit', async e => {
    e.preventDefault(); const id=activeEngagement(); const f=e.currentTarget; const fd=new FormData(f);
    const data = await api(`/engagements/${encodeURIComponent(id)}/evidence`, { method:'POST', body: JSON.stringify({summary:fd.get('summary'), media_type:fd.get('media_type'), data:fd.get('data'), metadata:parseJsonField(f,'metadata',{})}) }); show(data); await refreshEngagementScoped();
  });
}
function bindButtons() {
  $('saveKey').onclick = () => { localStorage.setItem('intakeApiKey', $('apiKey').value); show('API key saved locally in this browser.'); };
  $('refreshAll').onclick = refreshAll;
  $('activeEngagement').onchange = e => setActive(e.target.value);
  $('runReadiness').onclick = async () => { const data = await api('/ops/readiness'); $('opsOutput').textContent = JSON.stringify(data, null, 2); };
  $('verifyEvidence').onclick = async () => { const data = await api('/ops/evidence/verify'); $('opsOutput').textContent = JSON.stringify(data, null, 2); };
  $('downloadReport').onclick = () => download(`/engagements/${encodeURIComponent(activeEngagement())}/report.md`);
  $('downloadEngagementExport').onclick = () => download(`/ops/engagements/${encodeURIComponent(activeEngagement())}/export`);
  $('downloadAudit').onclick = () => download('/ops/audit/export.ndjson');
  $('nav').addEventListener('click', e => {
    const btn = e.target.closest('button[data-section]'); if (!btn) return;
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    btn.classList.add('active'); $(btn.dataset.section).classList.add('active');
  });
}
window.executeCall = executeCall;
window.decideApproval = decideApproval;
window.setActive = setActive;
window.addEventListener('DOMContentLoaded', async () => {
  $('apiKey').value = localStorage.getItem('intakeApiKey') || '';
  bindForms(); bindButtons(); await refreshAll();
});
</script>
</body>
</html>
"""


def render_dashboard(session: Session) -> str:
    return _console_page(None)


def render_engagement(session: Session, engagement_id: str) -> str:
    return _console_page(engagement_id)


def _console_page(initial_engagement: str | None) -> str:
    return CONSOLE_HTML.replace("__INITIAL_ENGAGEMENT__", json.dumps(initial_engagement))
