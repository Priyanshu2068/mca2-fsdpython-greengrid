import { useState } from 'react';
import { Empty } from './ui.jsx';

function niceMax(v) {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  const f = v / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
}

function Tip({ tip }) {
  if (!tip) return null;
  return (
    <div className="tip" style={{
      left: Math.min(window.innerWidth - 248, Math.max(8, tip.x + 14)),
      top: Math.max(8, tip.y - 70),
    }}>{tip.content}</div>
  );
}

/**
 * Line/area/bar chart. series: [{name, color, values:number[]}]
 */
export function LineChart({ labels, series, height = 260, fmt = v => String(Math.round(v)), xTick, tipLabel, area = true, type = 'line', label = 'Chart' }) {
  const [hover, setHover] = useState(null); // {i, x, y}
  if (!labels.length) return <div className="chart"><Empty>No data in this range.</Empty></div>;

  const W = 720, H = height;
  const m = { l: 52, r: 12, t: 10, b: 26 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const max = niceMax(Math.max(...series.flatMap(s => s.values), 0));
  const n = labels.length;
  const bar = type === 'bar';
  const x = i => m.l + (bar ? (i + 0.5) * iw / n : (n === 1 ? iw / 2 : i * iw / (n - 1)));
  const y = v => m.t + ih - (v / max) * ih;
  const every = Math.max(1, Math.ceil(n / 8));
  const hi = hover && Math.min(hover.i, n - 1);

  const onMove = e => {
    const r = e.currentTarget.ownerSVGElement.getBoundingClientRect();
    const px = (e.clientX - r.left) * W / r.width;
    let i = bar ? Math.floor((px - m.l) / (iw / n)) : Math.round((px - m.l) / (n === 1 ? 1 : iw / (n - 1)));
    i = Math.max(0, Math.min(n - 1, i));
    setHover({ i, x: e.clientX, y: e.clientY });
  };

  const tip = hover && {
    x: hover.x, y: hover.y,
    content: (
      <>
        <div>{tipLabel ? tipLabel(labels[hi], hi) : labels[hi]}</div>
        {series.map(s => <div key={s.name}><span style={{ color: s.color }}>●</span> {s.name}: <b>{fmt(s.values[hi])}</b></div>)}
      </>
    ),
  };

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label}>
        {[0, 1, 2, 3, 4].map(g => {
          const v = max * g / 4, yy = y(v);
          return (
            <g key={g}>
              <line x1={m.l} x2={W - m.r} y1={yy} y2={yy} className="grid-line" />
              <text x={m.l - 8} y={yy + 4} textAnchor="end">{fmt(v)}</text>
            </g>
          );
        })}
        {labels.map((lb, i) => (i % every ? null : (
          <text key={i} x={x(i)} y={H - 6} textAnchor="middle">{xTick ? xTick(lb, i) : lb}</text>
        )))}
        {series.map((s, si) => {
          if (bar) {
            const bw = Math.max(2, iw / n * 0.7 / series.length);
            return s.values.map((v, i) => (
              <rect key={`${si}-${i}`} x={x(i) - bw * series.length / 2 + si * bw} y={y(v)} width={bw} height={Math.max(0, m.t + ih - y(v))} rx={2} fill={s.color} />
            ));
          }
          const pts = s.values.map((v, i) => [x(i), y(v)]);
          const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
          return (
            <g key={si}>
              {area && <path d={`${d} L${pts[pts.length - 1][0]} ${m.t + ih} L${pts[0][0]} ${m.t + ih} Z`} fill={s.color} opacity={0.12} />}
              <path d={d} fill="none" stroke={s.color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
            </g>
          );
        })}
        {hover && !bar && (
          <>
            <line x1={x(hi)} x2={x(hi)} y1={m.t} y2={m.t + ih} stroke="currentColor" strokeOpacity={0.35} />
            {series.map(s => <circle key={s.name} cx={x(hi)} cy={y(s.values[hi])} r={4} fill={s.color} stroke="var(--surface)" strokeWidth={2} />)}
          </>
        )}
        <rect x={m.l} y={m.t} width={iw} height={ih} fill="transparent" onPointerMove={onMove} onPointerLeave={() => setHover(null)} />
      </svg>
      <Tip tip={tip} />
    </div>
  );
}

/** Donut. items: [{label, value, color}] */
export function Donut({ items, centerTop, centerBottom, fmt = v => v }) {
  const [tip, setTip] = useState(null);
  const total = items.reduce((a, b) => a + b.value, 0);
  if (!total) return <div className="chart"><Empty>No data.</Empty></div>;
  const S = 170, R = 68, r = 46, c = S / 2;
  const pt = (rad, a) => [c + rad * Math.cos(a), c + rad * Math.sin(a)];
  let a0 = -Math.PI / 2;
  const arcs = items.filter(it => it.value > 0).map(it => {
    const frac = it.value / total;
    const a1 = a0 + Math.min(frac, 0.9999) * Math.PI * 2;
    const large = a1 - a0 > Math.PI ? 1 : 0;
    const [x0, y0] = pt(R, a0), [x1, y1] = pt(R, a1), [x2, y2] = pt(r, a1), [x3, y3] = pt(r, a0);
    const d = `M${x0} ${y0} A${R} ${R} 0 ${large} 1 ${x1} ${y1} L${x2} ${y2} A${r} ${r} 0 ${large} 0 ${x3} ${y3} Z`;
    a0 = a1;
    return { it, frac, d };
  });
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${S} ${S}`} role="img" aria-label="Share breakdown" style={{ maxWidth: S }}>
        {arcs.map(({ it, frac, d }) => (
          <path key={it.label} d={d} fill={it.color}
            onPointerMove={e => setTip({ x: e.clientX, y: e.clientY, content: <>{it.label}: <b>{fmt(it.value)}</b> ({(frac * 100).toFixed(1)}%)</> })}
            onPointerLeave={() => setTip(null)} />
        ))}
        {centerTop && <text x={c} y={c + 2} textAnchor="middle" style={{ fontSize: 14, fontWeight: 650, fill: 'var(--text)' }}>{centerTop}</text>}
        {centerTop && centerBottom && <text x={c} y={c + 18} textAnchor="middle">{centerBottom}</text>}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
