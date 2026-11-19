/* GreenGrid web client: vanilla JS SPA over the Django REST API (same-origin, session auth). */
(function () {
  'use strict';

  /* ---------- helpers ---------- */
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = v => (v == null || v === '' ? 0 : Number(v));
  const nf = (v, d = 0) => num(v).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d });
  const kwh = v => { const n = num(v); return Math.abs(n) >= 1e6 ? nf(n / 1e6, 2) + ' GWh' : Math.abs(n) >= 1e4 ? nf(n / 1e3, 1) + ' MWh' : nf(n, 0) + ' kWh'; };
  const inr = v => {
    const n = num(v), a = Math.abs(n);
    if (a >= 1e7) return '₹' + nf(n / 1e7, 2) + ' Cr';
    if (a >= 1e5) return '₹' + nf(n / 1e5, 2) + ' L';
    return '₹' + nf(n, 0);
  };
  const dt = s => s ? new Date(s).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—';
  const dOnly = s => s ? new Date(s + (s.length === 10 ? 'T00:00:00' : '')).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
  const title = s => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const list = d => (d && d.results) ? d.results : (Array.isArray(d) ? d : []);
  const LOAD_NAMES = { hvac: 'HVAC & Chillers', it_infrastructure: 'IT & Servers', lighting: 'Lighting', auxiliary_pumps: 'Pumps', elevators: 'Elevators', ev_chargers: 'EV Charging', main_incomer: 'Main Incomer' };
  const SOURCE_NAMES = { grid: 'Utility Grid', diesel_generator: 'Diesel Generator', solar: 'Solar PV', water: 'Water', gas: 'Gas', natural_gas: 'Natural Gas' };
  const SRC_COLORS = { grid: 'var(--c2)', diesel_generator: 'var(--c5)', solar: 'var(--c3)', gas: 'var(--c4)', natural_gas: 'var(--c4)', water: 'var(--c1)' };
  const PALETTE = ['var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)'];

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
  };

  function toast(msg, isErr) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.toggle('err', !!isErr);
    t.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove('show'), 3200);
  }

  /* ---------- API ---------- */
  const cookie = n => (document.cookie.match('(?:^|; )' + n + '=([^;]*)') || [])[1] || '';
  async function ensureCsrf() { await fetch('/api/v1/accounts/csrf/', { credentials: 'same-origin' }); }
  async function api(path, opt) {
    opt = opt || {};
    const headers = { 'X-CSRFToken': decodeURIComponent(cookie('csrftoken')) };
    if (!opt.isFormData) headers['Content-Type'] = 'application/json';
    const res = await fetch('/api/v1/' + path, {
      method: opt.method || 'GET', credentials: 'same-origin',
      headers,
      body: opt.isFormData ? opt.body : (opt.body ? JSON.stringify(opt.body) : undefined),
    });
    let data = null;
    try { data = await res.json(); } catch (e) { /* empty body */ }
    if (!res.ok) {
      if ((res.status === 401 || res.status === 403) && state.user && path !== 'accounts/login/') {
        const msg = data && data.error && data.error.message || '';
        if (/authentication|credentials|not authenticated/i.test(msg) || res.status === 401) { showLogin(); }
      }
      const err = new Error((data && data.error && (data.error.message || JSON.stringify(data.error.details))) || ('Request failed (' + res.status + ')'));
      err.status = res.status; err.data = data;
      throw err;
    }
    return data;
  }
  const q = o => Object.entries(o).filter(([, v]) => v !== undefined && v !== '' && v !== null).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');

  /* ---------- state ---------- */
  const state = { user: null, facilities: [], fid: null, route: 'overview', renderId: 0 };

  /* ---------- icons ---------- */
  const ic = p => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
  const ICONS = {
    overview: ic('<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>'),
    alerts: ic('<path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10 21a2 2 0 0 0 4 0"/>'),
    billing: ic('<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>'),
    benchmark: ic('<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>'),
    recs: ic('<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>'),
    solar: ic('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    sites: ic('<path d="M3 21V8l9-5 9 5v13"/><path d="M9 21v-6h6v6"/>'),
  };

  const ROUTES = [
    { id: 'overview', name: 'Overview', render: renderOverview },
    { id: 'alerts', name: 'Alerts', render: renderAlerts },
    { id: 'billing', name: 'Billing', render: renderBilling },
    { id: 'benchmark', name: 'Benchmarking', render: renderBenchmark },
    { id: 'recs', name: 'Recommendations', render: renderRecs },
    { id: 'solar', name: 'Renewables & Carbon', render: renderRenewables },
    { id: 'sites', name: 'Facilities', render: renderSites },
  ];

  /* ---------- shell ---------- */
  function showLogin() {
    state.user = null;
    $('#shell').classList.add('hidden');
    $('#login').classList.remove('hidden');
  }
  async function enterApp(user) {
    state.user = user;
    $('#login').classList.add('hidden');
    $('#shell').classList.remove('hidden');
    $('#whoami').innerHTML = `<b>${esc(user.full_name || user.email)}</b><span>${esc(title(user.role))}</span>`;
    $('#nav').innerHTML = ROUTES.map(r => `<a href="#/${r.id}" data-r="${r.id}">${ICONS[r.id]}<span>${r.name}</span>${r.id === 'alerts' ? '<span class="badge hidden" id="alert-badge"></span>' : ''}</a>`).join('');
    try {
      state.facilities = list(await api('facilities/?page_size=200'));
    } catch (e) { toast(e.message, true); state.facilities = []; }
    const saved = Number(store.get('gg.fid'));
    state.fid = state.facilities.find(f => f.id === saved) ? saved : (state.facilities[0] && state.facilities[0].id);
    $('#facility').innerHTML = state.facilities.map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join('');
    if (state.fid) $('#facility').value = state.fid;
    route();
  }

  function route() {
    const id = (location.hash.replace(/^#\/?/, '') || 'overview').split('?')[0];
    const r = ROUTES.find(x => x.id === id) || ROUTES[0];
    state.route = r.id;
    $('#page-title').textContent = r.name;
    document.title = r.name + ' · GreenGrid';
    document.querySelectorAll('#nav a').forEach(a => a.classList.toggle('active', a.dataset.r === r.id));
    $('#sidebar').classList.remove('open');
    const view = $('#view');
    if (!state.fid && r.id !== 'sites') { view.innerHTML = '<div class="card empty">No facilities are assigned to your account.</div>'; return; }
    const myId = ++state.renderId;
    view.innerHTML = '<div class="grid kpis"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div><div class="skeleton" style="height:280px"></div>';
    Promise.resolve(r.render(view, () => myId === state.renderId)).catch(e => {
      if (myId !== state.renderId) return;
      view.innerHTML = `<div class="card empty">Could not load this page.<br><span class="small">${esc(e.message)}</span><br><br><button class="btn" onclick="location.reload()">Retry</button></div>`;
    });
    refreshBadge();
  }

  async function refreshBadge() {
    const b = $('#alert-badge');
    if (!b || !state.fid) return;
    try {
      const a = list(await api('analytics/alerts/?' + q({ facility_id: state.fid, status: 'open', page_size: 200 })));
      b.textContent = a.length; b.classList.toggle('hidden', !a.length);
    } catch (e) { /* non-critical */ }
  }

  /* ---------- UI atoms ---------- */
  const card = (head, body, cls) => `<section class="card ${cls || ''}">${head ? `<div class="card-head"><h2>${head}</h2></div>` : ''}${body}</section>`;
  const kpi = (label, value, sub, extra) => `<div class="card kpi"><div class="label">${label}</div><div class="value num">${value}</div><div class="sub">${sub || ''}</div>${extra || ''}</div>`;
  const pill = (txt, kind) => `<span class="pill ${kind || 'neutral'}">${esc(txt)}</span>`;
  const sevKind = s => ({ critical: 'bad', high: 'bad', medium: 'warn', low: 'info' }[s] || 'neutral');
  const empty = msg => `<div class="empty">${msg}</div>`;
  function table(cols, rows) {
    if (!rows.length) return '';
    return `<div class="table-wrap"><table><thead><tr>${cols.map(c => `<th class="${c.r ? 'r' : ''}">${c.h}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map((c, i) => `<td class="${cols[i].r ? 'r num' : ''} ${cols[i].wrap ? 'wrap' : ''}">${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function stars(n) { return `<span class="stars" aria-label="${n} of 5 stars">${'★'.repeat(n)}<span class="off">${'★'.repeat(5 - n)}</span></span>`; }
  function ask(titleTxt, label, required) {
    return new Promise(resolve => {
      const d = document.createElement('dialog');
      d.innerHTML = `<form method="dialog"><h2>${esc(titleTxt)}</h2><label>${esc(label)}<textarea rows="3" ${required ? 'required' : ''}></textarea></label><div class="actions"><button type="button" class="btn" value="x">Cancel</button><button class="btn primary" value="ok">Confirm</button></div></form>`;
      document.body.appendChild(d);
      const done = v => { d.close(); d.remove(); resolve(v); };
      d.querySelector('button[type=button]').onclick = () => done(null);
      d.addEventListener('cancel', () => done(null));
      d.querySelector('form').onsubmit = e => { e.preventDefault(); done(d.querySelector('textarea').value.trim()); };
      d.showModal();
    });
  }
  const fac = () => state.facilities.find(f => f.id === state.fid) || {};

  /* ---------- Overview ---------- */
  async function renderOverview(view, alive) {
    let range = '24h';
    const [sum, mix, load] = await Promise.all([
      api('dashboard/summary/?facility_id=' + state.fid),
      api('dashboard/energy-mix/?facility_id=' + state.fid),
      api('dashboard/load-breakdown/?facility_id=' + state.fid),
    ]);
    if (!alive()) return;
    const m = sum.metrics, f = fac();
    const ch = num(m.change_percentage);
    const util = num(m.demand_utilization_pct);
    const utilCls = util > 90 ? 'bad' : util > 75 ? 'warn' : '';
    view.innerHTML = `
      <div class="grid kpis">
        ${kpi('Consumption today', `${nf(m.today_consumption_kwh)}<small>kWh</small>`,
          `<span class="delta ${ch > 0 ? 'up' : 'down'}">${ch > 0 ? '▲' : '▼'} ${nf(Math.abs(ch), 1)}%</span> vs yesterday (${nf(m.yesterday_same_time_kwh)} kWh)`)}
        ${kpi('Month to date', `${nf(num(m.month_to_date_kwh) / 1000, 1)}<small>MWh</small>`, `${esc(f.name)}`)}
        ${kpi('Peak demand today', `${nf(m.current_peak_demand_kw)}<small>kW</small>`,
          `${nf(util, 1)}% of ${nf(m.sanctioned_demand_kva)} kVA sanctioned`, `<div class="meter-bar ${utilCls}"><i style="width:${Math.min(100, util)}%"></i></div>`)}
        ${kpi('Open anomalies', `${m.active_anomalies_count}`, m.active_anomalies_count ? `<a href="#/alerts">Review alerts →</a>` : 'All meters look healthy')}
      </div>
      <div class="grid cols-3">
        ${card('<span id="trend-title">Energy &amp; demand</span>', `
          <div class="toolbar" style="margin:-4px 0 10px"><div class="seg" id="range"><button data-r="24h" class="on">24 hours</button><button data-r="30d">30 days</button></div></div>
          <div id="trend"></div>
          <div class="legend"><span><i style="background:var(--c1)"></i>Energy (kWh)</span><span><i style="background:var(--c3)"></i>Peak demand (kW)</span></div>`)}
        ${card('Energy mix <span class="muted small">· last 30 days</span>', `<div class="donut-wrap"><div id="mix"></div><div class="rows" id="mix-legend"></div></div>`)}
      </div>
      ${card('Load breakdown <span class="muted small">· sub-metered, last 30 days</span>', `<div class="rows" id="load"></div>`)}`;

    const mixItems = (mix.energy_mix || []).map(x => ({ label: SOURCE_NAMES[x.source] || title(x.source), value: num(x.energy_kwh), color: SRC_COLORS[x.source] || 'var(--c1)', pct: num(x.percentage) }));
    GGCharts.donut($('#mix'), mixItems, kwh(mix.total_consumption_kwh), 'total', kwh);
    $('#mix-legend').innerHTML = mixItems.map(x => `<div class="row-item"><div class="top"><span><i style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${x.color};margin-right:8px"></i>${esc(x.label)}</span><b class="num">${nf(x.pct, 1)}%</b></div></div>`).join('') || empty('No data');

    const maxPct = Math.max(1, ...((load.breakdown || []).map(b => num(b.percentage))));
    $('#load').innerHTML = (load.breakdown || []).map((b, i) => `<div class="row-item"><div class="top"><span>${esc(LOAD_NAMES[b.load_category] || title(b.load_category))}</span><span class="num"><b>${nf(b.percentage, 1)}%</b> <span class="muted">· ${kwh(b.energy_kwh)}</span></span></div><div class="meter-bar"><i style="width:${num(b.percentage) / maxPct * 100}%;background:${PALETTE[i % 5]}"></i></div></div>`).join('') || empty('No sub-metered data yet.');

    async function drawTrend() {
      const t = await api(`dashboard/trends/?facility_id=${state.fid}&range=${range}`);
      if (!alive()) return;
      const pts = t.points || [];
      const labels = pts.map(p => p.timestamp || p.date);
      const fmtX = (l) => range === '24h' ? new Date(l).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false }) : dOnly(l).replace(/ \d{4}$/, '');
      const host = $('#trend');
      // two series with different units: draw energy as area+line, demand as a second chart overlay scaled separately
      GGCharts.lineChart(host, labels, [{ name: 'Energy (kWh)', color: 'var(--c1)', values: pts.map(p => num(p.energy_kwh)) }],
        { fmt: v => nf(v), xTick: fmtX, tipLabel: l => range === '24h' ? dt(l) : dOnly(l), label: 'Energy consumption trend' });
      const peak = document.createElement('div'); peak.style.marginTop = '8px';
      host.appendChild(peak);
      GGCharts.lineChart(peak, labels, [{ name: 'Peak demand (kW)', color: 'var(--c3)', values: pts.map(p => num(p.peak_demand_kw)) }],
        { fmt: v => nf(v), xTick: fmtX, height: 150, area: false, tipLabel: l => range === '24h' ? dt(l) : dOnly(l), label: 'Peak demand trend' });
    }
    $('#range').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      range = b.dataset.r;
      document.querySelectorAll('#range button').forEach(x => x.classList.toggle('on', x === b));
      drawTrend().catch(err => toast(err.message, true));
    });
    await drawTrend();
  }

  /* ---------- Alerts ---------- */
  async function renderAlerts(view, alive) {
    let status = 'open';
    const draw = async () => {
      const rows = list(await api('analytics/alerts/?' + q({ facility_id: state.fid, status: status === 'all' ? '' : status, page_size: 200 })));
      if (!alive()) return;
      const body = rows.length ? table(
        [{ h: 'Severity' }, { h: 'Type' }, { h: 'Meter' }, { h: 'Details', wrap: 1 }, { h: 'Detected' }, { h: 'Status' }, { h: '' }],
        rows.map(a => [pill(a.severity, sevKind(a.severity)), esc(title(a.anomaly_type)), esc(a.meter_identifier), esc(a.reason),
          dt(a.detected_at), pill(title(a.status), a.status === 'open' ? 'warn' : a.status === 'resolved' ? 'good' : 'neutral'),
          a.status === 'open' || a.status === 'acknowledged' ? `<div class="actions">${a.status === 'open' ? `<button class="btn small" data-a="acknowledged" data-id="${a.id}">Acknowledge</button>` : ''}<button class="btn small" data-a="resolved" data-id="${a.id}">Resolve</button><button class="btn small ghost" data-a="false_positive" data-id="${a.id}">False positive</button></div>` : '']))
        : empty(status === 'open' ? '✓ No open alerts. Everything looks healthy.' : 'No alerts match this filter.');
      $('#alert-table').innerHTML = body;
    };
    view.innerHTML = card('Anomaly alerts', `
      <div class="toolbar" style="margin-bottom:12px"><div class="seg" id="st">${['open', 'acknowledged', 'resolved', 'all'].map(s => `<button data-s="${s}" class="${s === status ? 'on' : ''}">${title(s)}</button>`).join('')}</div></div>
      <div id="alert-table"></div>`);
    $('#st').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      status = b.dataset.s;
      document.querySelectorAll('#st button').forEach(x => x.classList.toggle('on', x === b));
      draw().catch(err => toast(err.message, true));
    });
    $('#alert-table').addEventListener('click', async e => {
      const b = e.target.closest('button[data-a]'); if (!b) return;
      let notes = '';
      if (b.dataset.a !== 'acknowledged') {
        notes = await ask(b.dataset.a === 'resolved' ? 'Resolve alert' : 'Mark as false positive', 'Resolution notes', true);
        if (notes === null) return;
      }
      b.disabled = true;
      try {
        await api('analytics/alerts/' + b.dataset.id + '/', { method: 'PATCH', body: { status: b.dataset.a, resolution_notes: notes } });
        toast('Alert updated'); await draw(); refreshBadge();
      } catch (err) { toast(err.message, true); b.disabled = false; }
    });
    await draw();
  }

  /* ---------- Billing ---------- */
  async function renderBilling(view, alive) {
    const [bills, recs] = await Promise.all([
      api('billing/bills/?' + q({ facility_id: state.fid, page_size: 100 })),
      api('billing/reconciliations/?' + q({ facility_id: state.fid })),
    ]);
    if (!alive()) return;
    const B = list(bills), R = list(recs);
    const recStatus = { verified_within_tolerance: ['Verified', 'good'], variance_minor: ['Minor variance', 'warn'], variance_action_required: ['Action required', 'bad'] };
    const flagged = R.filter(r => r.reconciliation_status === 'variance_action_required');
    const totalBilled = B.reduce((a, b) => a + num(b.billed_amount_inr), 0);
    const leak = R.reduce((a, r) => a + Math.max(0, num(r.variance_cost_inr)), 0);
    view.innerHTML = `
      <div class="grid kpis">
        ${kpi('Bills on record', B.length, esc(fac().name))}
        ${kpi('Total billed', inr(totalBilled), 'across all cycles')}
        ${kpi('Flagged for audit', flagged.length, flagged.length ? 'variance above 2.5%' : 'No disputes needed')}
        ${kpi('Potential over-billing', inr(leak), 'billed vs sub-metered energy')}
      </div>
      ${card('Bill reconciliation <span class="muted small">· utility bill vs. metered energy</span>', R.length ? table(
        [{ h: 'Bill' }, { h: 'Billed kWh', r: 1 }, { h: 'Metered kWh', r: 1 }, { h: 'Variance', r: 1 }, { h: 'Cost impact', r: 1 }, { h: 'Result' }, { h: 'Note', wrap: 1 }],
        R.map(r => [`<b>${esc(r.bill_number)}</b>`, nf(r.billed_kwh), nf(r.metered_kwh), `${nf(r.discrepancy_percentage, 2)}%`, inr(r.variance_cost_inr),
          pill(...recStatus[r.reconciliation_status] || [r.reconciliation_status, 'neutral']), esc(r.notes)])) : empty('No reconciliations yet.'))}
      ${card('Utility bills', B.length ? table(
        [{ h: 'Bill' }, { h: 'Cycle' }, { h: 'Due' }, { h: 'kWh', r: 1 }, { h: 'Max kVA', r: 1 }, { h: 'Amount', r: 1 }, { h: '₹/kWh', r: 1 }, { h: 'Status' }],
        B.map(b => [`<b>${esc(b.bill_number)}</b><div class="muted small">${esc(b.tariff_name)}</div>`, `${dOnly(b.billing_cycle_start)} – ${dOnly(b.billing_cycle_end)}`, dOnly(b.due_date),
          nf(b.billed_kwh), nf(b.billed_max_demand_kva), inr(b.billed_amount_inr), nf(b.effective_cost_per_kwh_inr, 2),
          pill(title(b.payment_status), b.payment_status === 'paid' ? 'good' : b.payment_status === 'disputed' ? 'bad' : 'warn')])) : empty('No bills recorded for this facility.'))}`;
  }

  /* ---------- Benchmarking ---------- */
  async function renderBenchmark(view, alive) {
    const [rank, std] = await Promise.all([api('benchmarking/ranking/'), api('benchmarking/standards/')]);
    if (!alive()) return;
    const R = list(rank), S = list(std);
    const mine = R.find(r => r.facility === state.fid);
    const bm = mine && S.find(s => s.facility_type === mine.facility_type);
    let gauge = '';
    if (mine && bm) {
      const lo = num(bm.top_20_percentile_eui), hi = num(bm.bottom_20_percentile_eui), med = num(bm.median_eui_kwh_sqm_year), val = num(mine.calculated_eui_kwh_sqm_year);
      const max = Math.max(hi * 1.1, val * 1.1), pos = v => Math.min(100, v / max * 100);
      gauge = `<div style="position:relative;height:14px;border-radius:9px;background:linear-gradient(90deg,var(--good-bg) ${pos(lo)}%,var(--warn-bg) ${pos(lo)}%,var(--warn-bg) ${pos(hi)}%,var(--bad-bg) ${pos(hi)}%);margin:26px 0 8px">
        <span style="position:absolute;left:${pos(val)}%;top:-6px;width:4px;height:26px;border-radius:3px;background:var(--brand);transform:translateX(-2px)" title="This facility"></span>
        <span class="small muted" style="position:absolute;left:${pos(val)}%;top:-24px;transform:translateX(-50%);white-space:nowrap;color:var(--brand);font-weight:600">${nf(val, 1)}</span>
        <span class="small muted" style="position:absolute;left:${pos(med)}%;top:20px;transform:translateX(-50%)">median ${nf(med)}</span></div>
        <div class="small muted" style="margin-top:22px">Energy use intensity (kWh/m²/yr). Left of ${nf(lo)} is top-20% efficient; right of ${nf(hi)} is bottom-20%.</div>`;
    }
    view.innerHTML = `
      ${mine ? `<div class="grid cols-2">
        ${card(esc(mine.facility_name), `<div class="stars" style="font-size:30px">${stars(mine.star_rating)}</div>
          <div class="grid kpis" style="margin-top:12px;grid-template-columns:repeat(3,1fr)">
            <div><div class="muted small">EUI</div><b class="num" style="font-size:20px">${nf(mine.calculated_eui_kwh_sqm_year, 1)}</b></div>
            <div><div class="muted small">Percentile</div><b class="num" style="font-size:20px">${nf(mine.national_percentile)}</b></div>
            <div><div class="muted small">Energy (${mine.year})</div><b class="num" style="font-size:20px">${kwh(mine.annual_energy_kwh)}</b></div></div>`)}
        ${card('Where you sit vs. ' + esc(title(mine.facility_type)) + ' peers', gauge || empty('No standard available.'))}
      </div>` : card('', empty('No benchmark has been computed for this facility yet.'))}
      ${card('Facility ranking', R.length ? table(
        [{ h: '#' }, { h: 'Facility' }, { h: 'Type' }, { h: 'EUI', r: 1 }, { h: 'Percentile', r: 1 }, { h: 'Rating' }],
        R.map((r, i) => [i + 1, `<b>${esc(r.facility_name)}</b>`, esc(title(r.facility_type)), nf(r.calculated_eui_kwh_sqm_year, 1), nf(r.national_percentile), stars(r.star_rating)])) : empty('No data.'))}
      ${card('BEE benchmark standards <span class="muted small">· kWh/m²/year</span>', table(
        [{ h: 'Facility type' }, { h: 'Top 20%', r: 1 }, { h: 'Median', r: 1 }, { h: 'Bottom 20%', r: 1 }, { h: 'Standard' }],
        S.map(s => [esc(s.facility_type_display), nf(s.top_20_percentile_eui), nf(s.median_eui_kwh_sqm_year), nf(s.bottom_20_percentile_eui), `<span class="muted">${esc(s.benchmark_standard)}</span>`])))}`;
  }

  /* ---------- Recommendations ---------- */
  async function renderRecs(view, alive) {
    let status = 'active';
    const summary = async () => api('recommendations/summary/?facility_id=' + state.fid);
    const draw = async () => {
      const [s, r] = await Promise.all([summary(), api('recommendations/?' + q({ facility_id: state.fid, status: status === 'all' ? '' : status }))]);
      if (!alive()) return;
      $('#rec-kpis').innerHTML = `
        ${kpi('Potential savings', inr(s.total_potential_savings_inr), `${nf(num(s.total_potential_kwh_savings) / 1000)} MWh per year`)}
        ${kpi('Accepted', inr(s.accepted_annual_savings_inr), `${s.accepted_count} measure${s.accepted_count === 1 ? '' : 's'} committed`)}
        ${kpi('Active ideas', s.active_count, `of ${s.total_recommendations} generated`)}
        ${kpi('Dismissed', s.dismissed_count, 'with recorded reasons')}`;
      const rows = list(r);
      $('#rec-list').innerHTML = rows.length ? rows.map(x => `
        <section class="card rec" data-id="${x.id}">
          <header><div><h3>${esc(x.title)}</h3><div class="muted small">${esc(title(x.rule_category))}${x.meter_identifier ? ' · ' + esc(x.meter_identifier) : ''}</div></div>
            ${pill(title(x.status), x.status === 'active' ? 'info' : x.status === 'dismissed' ? 'neutral' : 'good')}</header>
          <div>${esc(x.description)}</div>
          <div class="stats">
            <div><span>Savings / year</span><b class="num" style="color:var(--good)">${inr(x.estimated_annual_savings_inr)}</b></div>
            <div><span>Energy saved</span><b class="num">${kwh(x.estimated_annual_kwh_savings)}</b></div>
            <div><span>Investment</span><b class="num">${inr(x.implementation_cost_inr)}</b></div>
            <div><span>Payback</span><b class="num">${nf(x.estimated_payback_months, 1)} mo</b></div></div>
          <details><summary>Action plan</summary><pre>${esc(x.action_plan)}</pre></details>
          ${x.status === 'dismissed' && x.dismissal_reason ? `<div class="small muted">Dismissed: ${esc(x.dismissal_reason)}</div>` : ''}
          <div class="actions">
            ${x.status === 'active' ? `<button class="btn primary small" data-a="accepted">Accept</button><button class="btn small danger" data-a="dismissed">Dismiss…</button>` : ''}
            ${x.status === 'accepted' ? `<button class="btn primary small" data-a="implemented">Mark implemented</button>` : ''}
          </div></section>`).join('') : card('', empty('Nothing here. Try another filter.'));
    };
    view.innerHTML = `<div class="grid kpis" id="rec-kpis"></div>
      <div class="toolbar"><div class="seg" id="st">${['active', 'accepted', 'implemented', 'dismissed', 'all'].map(s => `<button data-s="${s}" class="${s === status ? 'on' : ''}">${title(s)}</button>`).join('')}</div></div>
      <div class="grid" id="rec-list"></div>`;
    $('#st').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      status = b.dataset.s;
      document.querySelectorAll('#st button').forEach(x => x.classList.toggle('on', x === b));
      draw().catch(err => toast(err.message, true));
    });
    $('#rec-list').addEventListener('click', async e => {
      const b = e.target.closest('button[data-a]'); if (!b) return;
      const id = b.closest('.rec').dataset.id;
      const body = { status: b.dataset.a };
      if (body.status === 'dismissed') {
        const reason = await ask('Dismiss recommendation', 'Why is this not applicable?', true);
        if (!reason) return;
        body.dismissal_reason = reason;
      }
      b.disabled = true;
      try { await api('recommendations/' + id + '/', { method: 'PATCH', body }); toast('Recommendation ' + body.status); await draw(); }
      catch (err) { toast(err.message, true); b.disabled = false; }
    });
    await draw();
  }

  /* ---------- Renewables & carbon ---------- */
  async function renderRenewables(view, alive) {
    const end = new Date(), start = new Date(Date.now() - 30 * 864e5);
    const d = x => x.toISOString().slice(0, 10);
    const rng = { facility_id: state.fid, start_date: d(start), end_date: d(end) };
    const [self, em, gen, ev, assets] = await Promise.all([
      api('renewables/self-consumption/?' + q(rng)), api('renewables/emissions/?' + q(rng)),
      api('renewables/generation/?' + q({ ...rng, page_size: 5000 })), api('renewables/grid-events/?facility_id=' + state.fid),
      api('renewables/solar-assets/?facility_id=' + state.fid),
    ]);
    if (!alive()) return;
    // API returns the latest <=100 hourly readings, newest first
    const readings = list(gen).slice().reverse();
    const srcItems = Object.entries(em.breakdown_by_source || {}).map(([k, v]) => ({ key: k, label: SOURCE_NAMES[k] || title(k), value: num(v.emissions_kg_co2), kwh: num(v.energy_kwh), factor: v.factor_kg_per_kwh, color: SRC_COLORS[k] || 'var(--c1)' }));
    const capacity = list(assets).reduce((a, s) => a + num(s.rated_capacity_kwp), 0);
    const events = list(ev);
    view.innerHTML = `
      <div class="grid kpis">
        ${kpi('Solar generation', kwh(self.total_solar_generation_kwh), `${nf(capacity)} kWp installed · 30 days`)}
        ${kpi('Solar share', `${nf(self.solar_fraction_percentage, 1)}<small>%</small>`, 'of facility consumption')}
        ${kpi('Cost avoided', inr(self.estimated_cost_avoided_inr), 'versus grid purchase')}
        ${kpi('CO₂ emitted', `${nf(em.total_emissions_tco2e, 1)}<small>tCO₂e</small>`, `${nf(em.avoided_emissions_tco2e, 1)} tCO₂e avoided by solar`)}
      </div>
      <div class="grid cols-3">
        ${card('Solar generation <span class="muted small">· latest hourly readings</span>', `<div id="gen"></div>`)}
        ${card('Emissions by source', `<div class="donut-wrap"><div id="em"></div><div class="rows" id="em-l"></div></div>`)}
      </div>
      ${card('Grid events &amp; outages', events.length ? table(
        [{ h: 'Event' }, { h: 'Started' }, { h: 'Duration', r: 1 }, { h: 'Diesel used', r: 1 }, { h: 'Restored' }, { h: 'Notes', wrap: 1 }],
        events.map(e => [esc(e.event_type_display), dt(e.start_time), `${nf(e.duration_minutes, 0)} min`, `${nf(e.fuel_consumed_litres, 0)} L`, e.grid_restored ? pill('Yes', 'good') : pill('Ongoing', 'bad'), esc(e.notes)])) : empty('No grid events recorded.'))}`;
    GGCharts.lineChart($('#gen'), readings.map(g => g.timestamp), [{ name: 'Generation (kWh)', color: 'var(--c3)', values: readings.map(g => num(g.generation_kwh)) }],
      { type: 'bar', fmt: v => nf(v), xTick: l => new Date(l).toLocaleString('en-IN', { day: '2-digit', month: 'short' }), tipLabel: dt, label: 'Hourly solar generation' });
    GGCharts.donut($('#em'), srcItems.filter(s => s.value > 0), nf(em.total_emissions_tco2e, 1), 'tCO₂e', v => nf(v) + ' kg');
    $('#em-l').innerHTML = srcItems.map(s => `<div class="row-item"><div class="top"><span><i style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${s.color};margin-right:8px"></i>${esc(s.label)}</span><b class="num">${nf(s.value / 1000, 1)} t</b></div><div class="small muted">${kwh(s.kwh)} × ${esc(s.factor)} kg/kWh</div></div>`).join('');
  }

  /* ---------- Facilities ---------- */
  async function renderSites(view, alive) {
    const F = state.facilities;
    const isEng = state.user && (state.user.role === 'admin' || state.user.role === 'field_engineer' || state.user.is_superuser);
    const meters = await Promise.all(F.map(f => api(`facilities/${f.id}/meters/`).then(list).catch(() => [])));
    if (!alive()) return;
    view.innerHTML = F.length ? F.map((f, i) => card(`
      <div style="display:flex;align-items:center;justify-content:space-between;width:100%">
        <div>${esc(f.name)} <span class="muted small">· ${esc(f.code)}</span></div>
        ${isEng ? `<div style="display:flex;gap:8px">
          <button class="btn small primary add-meter-btn" data-fid="${f.id}" data-fname="${esc(f.name)}">+ Register Meter</button>
          <button class="btn small ghost upload-csv-btn" data-fid="${f.id}" data-fname="${esc(f.name)}">Upload CSV</button>
        </div>` : ''}
      </div>`, `
      <div class="grid kpis" style="margin-bottom:14px">
        <div><div class="muted small">Type</div><b>${esc(title(f.facility_type))}</b></div>
        <div><div class="muted small">Location</div><b>${esc(f.city)}, ${esc(f.state)}</b></div>
        <div><div class="muted small">Floor area</div><b class="num">${nf(f.gross_floor_area_sqm)} m²</b></div>
        <div><div class="muted small">Sanctioned demand</div><b class="num">${nf(f.sanctioned_demand_kva)} kVA</b></div></div>
      ${table([{ h: 'Meter' }, { h: 'ID' }, { h: 'Source' }, { h: 'Load' }, { h: 'Location' }, { h: 'Active' }],
        meters[i].map(m => [`<b>${esc(m.name)}</b>`, `<code>${esc(m.meter_identifier)}</code>`, esc(SOURCE_NAMES[m.energy_source] || m.energy_source), esc(LOAD_NAMES[m.load_category] || m.load_category), esc(m.physical_location), m.is_active ? pill('Yes', 'good') : pill('No', 'neutral')]))}`)).join('') : card('', empty('No facilities.'));

    view.querySelectorAll('.add-meter-btn').forEach(b => {
      b.onclick = () => {
        const fid = b.dataset.fid;
        const fname = b.dataset.fname;
        const d = document.createElement('dialog');
        d.innerHTML = `
          <form method="dialog" style="display:grid;gap:12px;min-width:320px;max-width:400px;padding:8px">
            <h2>Register Meter</h2>
            <div class="muted small">${esc(fname)}</div>
            <label>Meter Name<input name="name" required placeholder="e.g. Substation Feeder 2"></label>
            <label>Meter Identifier<input name="meter_identifier" required placeholder="e.g. MTR-FEEDER-02"></label>
            <label>Energy Source
              <select name="energy_source">
                <option value="grid">Utility Grid</option>
                <option value="solar">Solar PV</option>
                <option value="diesel_generator">Diesel Generator</option>
                <option value="gas">Natural Gas</option>
                <option value="water">Water</option>
              </select>
            </label>
            <label>Load Category
              <select name="load_category">
                <option value="main_incomer">Main Incomer</option>
                <option value="hvac">HVAC & Chillers</option>
                <option value="lighting">Lighting Circuits</option>
                <option value="it_infrastructure">IT & Server Room</option>
                <option value="auxiliary_pumps">Auxiliary Pumps</option>
                <option value="elevators">Elevators</option>
                <option value="ev_chargers">EV Chargers</option>
              </select>
            </label>
            <label>Physical Location<input name="physical_location" placeholder="e.g. Electrical Room B1"></label>
            <div class="actions" style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">
              <button type="button" class="btn cancel-btn">Cancel</button>
              <button class="btn primary" type="submit">Register</button>
            </div>
          </form>`;
        document.body.appendChild(d);
        d.querySelector('.cancel-btn').onclick = () => { d.close(); d.remove(); };
        d.querySelector('form').onsubmit = async e => {
          e.preventDefault();
          const form = e.target;
          const payload = {
            name: form.name.value.trim(),
            meter_identifier: form.meter_identifier.value.trim(),
            energy_source: form.energy_source.value,
            load_category: form.load_category.value,
            physical_location: form.physical_location.value.trim(),
          };
          try {
            await api(`facilities/${fid}/meters/`, { method: 'POST', body: payload });
            toast(`Registered meter ${payload.meter_identifier}`);
            d.close(); d.remove();
            route();
          } catch (err) {
            toast(err.message, true);
          }
        };
        d.showModal();
      };
    });

    view.querySelectorAll('.upload-csv-btn').forEach(b => {
      b.onclick = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv';
        input.onchange = async () => {
          if (!input.files || !input.files[0]) return;
          const fd = new FormData();
          fd.append('file', input.files[0]);
          try {
            toast('Uploading CSV telemetry batch...');
            const res = await api('ingestion/readings/upload-csv/', { method: 'POST', body: fd, isFormData: true });
            toast(`CSV accepted: ${res.accepted || res.ingested || 0} readings processed.`);
            route();
          } catch (err) {
            toast(err.message || 'Upload failed', true);
          }
        };
        input.click();
      };
    });
  }

  /* ---------- boot ---------- */
  function initTheme() {
    const t = store.get('gg.theme');
    if (t) document.documentElement.setAttribute('data-theme', t);
  }
  async function boot() {
    initTheme();
    if (window.location.protocol === 'file:') {
      const err = $('#login-error');
      if (err) {
        err.innerHTML = '⚠️ <b>Direct file opening detected.</b><br>GreenGrid requires the Django backend server to run.<br>Execute: <code>.\\venv\\Scripts\\python.exe manage.py runserver</code><br>Then open: <a href="http://127.0.0.1:8000/app/" target="_blank">http://127.0.0.1:8000/app/</a>';
      }
      showLogin();
      return;
    }
    if (window.location.port && window.location.port !== '8000') {
      const err = $('#login-error');
      if (err) {
        err.innerHTML = `ℹ️ Running on port ${window.location.port}. Please access the app through Django at <a href="http://127.0.0.1:8000/app/">http://127.0.0.1:8000/app/</a>.`;
      }
    }
    document.querySelectorAll('.demo-btn').forEach(btn => {
      btn.onclick = () => {
        const form = $('#login-form');
        form.email.value = btn.dataset.email;
        form.password.value = 'GreenGrid@123';
        $('#login-error').textContent = '';
      };
    });
    $('#theme-btn').onclick = () => {
      const cur = document.documentElement.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next); store.set('gg.theme', next);
    };
    $('#menu-btn').onclick = () => $('#sidebar').classList.toggle('open');
    $('#facility').onchange = e => { state.fid = Number(e.target.value); store.set('gg.fid', state.fid); route(); };
    $('#logout').onclick = async () => { try { await api('accounts/logout/', { method: 'POST' }); } catch (e) { /* ignore */ } await ensureCsrf(); showLogin(); };
    window.addEventListener('hashchange', () => state.user && route());
    $('#login-form').onsubmit = async e => {
      e.preventDefault();
      const f = e.target, err = $('#login-error'), btn = f.querySelector('button');
      err.textContent = ''; btn.disabled = true;
      try {
        await ensureCsrf();
        const user = await api('accounts/login/', { method: 'POST', body: { email: f.email.value, password: f.password.value } });
        await enterApp(user);
      } catch (ex) { err.textContent = ex.message; }
      btn.disabled = false;
    };
    await ensureCsrf();
    try { await enterApp(await api('accounts/me/')); } catch (e) { showLogin(); }
  }
  boot();
})();
