/* Dependency-free SVG charts for GreenGrid. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const tip = () => document.getElementById('tip');

  function el(name, attrs, parent) {
    const n = document.createElementNS(NS, name);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function niceMax(v) {
    if (v <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(v)));
    const f = v / p;
    return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
  }
  function showTip(html, x, y) {
    const t = tip();
    t.innerHTML = html;
    t.classList.remove('hidden');
    const w = t.offsetWidth, h = t.offsetHeight;
    t.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, x + 14)) + 'px';
    t.style.top = Math.max(8, y - h - 10) + 'px';
  }
  function hideTip() { tip().classList.add('hidden'); }

  /**
   * Line/area chart. labels: string[]; series: [{name, color, values:number[]}]
   * opts: {height, fmt(value)->string, xTick(label, i)->string, area:boolean, type:'line'|'bar'}
   */
  function lineChart(host, labels, series, opts) {
    opts = opts || {};
    host.innerHTML = '';
    host.classList.add('chart');
    if (!labels.length) { host.innerHTML = '<div class="empty">No data in this range.</div>'; return; }
    const W = 720, H = opts.height || 260;
    const m = { l: 52, r: 12, t: 10, b: 26 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const fmt = opts.fmt || (v => String(Math.round(v)));
    const max = niceMax(Math.max(...series.flatMap(s => s.values), 0));
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': opts.label || 'Chart' }, host);
    const n = labels.length;
    const bar = opts.type === 'bar';
    const x = i => m.l + (bar ? (i + 0.5) * iw / n : (n === 1 ? iw / 2 : i * iw / (n - 1)));
    const y = v => m.t + ih - (v / max) * ih;

    for (let g = 0; g <= 4; g++) {
      const v = max * g / 4, yy = y(v);
      el('line', { x1: m.l, x2: W - m.r, y1: yy, y2: yy, class: 'grid-line' }, svg);
      const t = el('text', { x: m.l - 8, y: yy + 4, 'text-anchor': 'end' }, svg);
      t.textContent = fmt(v);
    }
    const every = Math.max(1, Math.ceil(n / 8));
    labels.forEach((lb, i) => {
      if (i % every) return;
      const t = el('text', { x: x(i), y: H - 6, 'text-anchor': 'middle' }, svg);
      t.textContent = opts.xTick ? opts.xTick(lb, i) : lb;
    });

    series.forEach((s, si) => {
      if (bar) {
        const bw = Math.max(2, iw / n * 0.7 / series.length);
        s.values.forEach((v, i) => {
          el('rect', { x: x(i) - bw * series.length / 2 + si * bw, y: y(v), width: bw, height: Math.max(0, m.t + ih - y(v)),
            rx: 2, fill: s.color }, svg);
        });
        return;
      }
      const pts = s.values.map((v, i) => [x(i), y(v)]);
      const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
      if (opts.area !== false) {
        el('path', { d: d + ` L${pts[pts.length - 1][0]} ${m.t + ih} L${pts[0][0]} ${m.t + ih} Z`, fill: s.color, opacity: .12 }, svg);
      }
      el('path', { d, fill: 'none', stroke: s.color, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
    });

    const cross = el('line', { y1: m.t, y2: m.t + ih, stroke: 'currentColor', 'stroke-opacity': .35, visibility: 'hidden' }, svg);
    const dots = series.map(s => el('circle', { r: 4, fill: s.color, stroke: 'var(--surface)', 'stroke-width': 2, visibility: 'hidden' }, svg));
    const hit = el('rect', { x: m.l, y: m.t, width: iw, height: ih, fill: 'transparent' }, svg);
    hit.addEventListener('pointermove', e => {
      const r = svg.getBoundingClientRect();
      const px = (e.clientX - r.left) * W / r.width;
      let i = bar ? Math.floor((px - m.l) / (iw / n)) : Math.round((px - m.l) / (n === 1 ? 1 : iw / (n - 1)));
      i = Math.max(0, Math.min(n - 1, i));
      cross.setAttribute('x1', x(i)); cross.setAttribute('x2', x(i)); cross.setAttribute('visibility', bar ? 'hidden' : 'visible');
      dots.forEach((d, si) => { d.setAttribute('cx', x(i)); d.setAttribute('cy', y(series[si].values[i])); d.setAttribute('visibility', bar ? 'hidden' : 'visible'); });
      const rows = series.map(s => `<div><span style="color:${s.color}">●</span> ${s.name}: <b>${fmt(s.values[i])}</b></div>`).join('');
      showTip(`<div>${opts.tipLabel ? opts.tipLabel(labels[i], i) : labels[i]}</div>${rows}`, e.clientX, e.clientY);
    });
    hit.addEventListener('pointerleave', () => {
      cross.setAttribute('visibility', 'hidden'); dots.forEach(d => d.setAttribute('visibility', 'hidden')); hideTip();
    });
  }

  /** Donut. items: [{label, value, color}] */
  function donut(host, items, centerTop, centerBottom, fmt) {
    host.innerHTML = '';
    host.classList.add('chart');
    const total = items.reduce((a, b) => a + b.value, 0);
    const S = 170, R = 68, r = 46, c = S / 2;
    const svg = el('svg', { viewBox: `0 0 ${S} ${S}`, role: 'img', 'aria-label': 'Share breakdown' }, host);
    svg.style.maxWidth = S + 'px';
    if (!total) { host.innerHTML = '<div class="empty">No data.</div>'; return; }
    let a0 = -Math.PI / 2;
    items.forEach(it => {
      const frac = it.value / total;
      if (frac <= 0) return;
      const a1 = a0 + Math.min(frac, 0.9999) * Math.PI * 2;
      const large = a1 - a0 > Math.PI ? 1 : 0;
      const p = (rad, a) => [c + rad * Math.cos(a), c + rad * Math.sin(a)];
      const [x0, y0] = p(R, a0), [x1, y1] = p(R, a1), [x2, y2] = p(r, a1), [x3, y3] = p(r, a0);
      const path = el('path', {
        d: `M${x0} ${y0} A${R} ${R} 0 ${large} 1 ${x1} ${y1} L${x2} ${y2} A${r} ${r} 0 ${large} 0 ${x3} ${y3} Z`, fill: it.color
      }, svg);
      path.addEventListener('pointermove', e => showTip(`${it.label}: <b>${(fmt || (v => v))(it.value)}</b> (${(frac * 100).toFixed(1)}%)`, e.clientX, e.clientY));
      path.addEventListener('pointerleave', hideTip);
      a0 = a1;
    });
    if (centerTop) {
      const t1 = el('text', { x: c, y: c + 2, 'text-anchor': 'middle', style: 'font-size:14px;font-weight:650;fill:var(--text)' }, svg);
      t1.textContent = centerTop;
      if (centerBottom) { const t2 = el('text', { x: c, y: c + 18, 'text-anchor': 'middle' }, svg); t2.textContent = centerBottom; }
    }
  }

  window.GGCharts = { lineChart, donut };
})();
