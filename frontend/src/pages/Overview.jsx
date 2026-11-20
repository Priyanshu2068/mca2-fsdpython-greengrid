import { useState } from 'react';
import { Link } from '../components/Link.jsx';
import { api } from '../api.js';
import { useApp } from '../context.js';
import { useAsync } from '../hooks.js';
import { LOAD_NAMES, PALETTE, SOURCE_NAMES, SRC_COLORS, dOnly, dt, kwh, nf, num, title } from '../format.js';
import { Card, Empty, Kpi, Loader, Meter, Seg, Swatch, useToast } from '../components/ui.jsx';
import { Donut, LineChart } from '../components/Charts.jsx';

function Trend({ fid, tick }) {
  const [range, setRange] = useState('24h');
  const res = useAsync(() => api(`dashboard/trends/?facility_id=${fid}&range=${range}`), [fid, range, tick]);
  const toast = useToast();
  const pts = (res.data && res.data.points) || [];
  const labels = pts.map(p => p.timestamp || p.date);
  const xTick = l => range === '24h'
    ? new Date(l).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
    : dOnly(l).replace(/ \d{4}$/, '');
  const tipLabel = l => (range === '24h' ? dt(l) : dOnly(l));

  return (
    <Card head="Energy &amp; demand">
      <div className="toolbar" style={{ margin: '-4px 0 10px' }}>
        <Seg value={range} onChange={setRange} options={[['24h', '24 hours'], ['30d', '30 days']]} />
      </div>
      {res.error && <div className="form-error" role="alert">{res.error.message} <button className="btn small" onClick={res.reload}>Retry</button></div>}
      {res.data && (
        <>
          <LineChart labels={labels} xTick={xTick} tipLabel={tipLabel} fmt={v => nf(v)} label="Energy consumption trend"
            series={[{ name: 'Energy (kWh)', color: 'var(--c1)', values: pts.map(p => num(p.energy_kwh)) }]} />
          <div style={{ marginTop: 8 }}>
            <LineChart labels={labels} xTick={xTick} tipLabel={tipLabel} fmt={v => nf(v)} height={150} area={false} label="Peak demand trend"
              series={[{ name: 'Peak demand (kW)', color: 'var(--c3)', values: pts.map(p => num(p.peak_demand_kw)) }]} />
          </div>
        </>
      )}
      {!res.data && !res.error && <div className="skeleton" style={{ height: 260 }} />}
      <div className="legend">
        <span><i style={{ background: 'var(--c1)' }} />Energy (kWh)</span>
        <span><i style={{ background: 'var(--c3)' }} />Peak demand (kW)</span>
      </div>
    </Card>
  );
}

export default function Overview() {
  const { fid, facility, tick } = useApp();
  const res = useAsync(async () => {
    const [sum, mix, load] = await Promise.all([
      api(`dashboard/summary/?facility_id=${fid}`),
      api(`dashboard/energy-mix/?facility_id=${fid}`),
      api(`dashboard/load-breakdown/?facility_id=${fid}`),
    ]);
    return { sum, mix, load };
  }, [fid, tick]);

  return (
    <Loader res={res}>
      {({ sum, mix, load }) => {
        const m = sum.metrics;
        const ch = num(m.change_percentage);
        const util = num(m.demand_utilization_pct);
        const utilCls = util > 90 ? 'bad' : util > 75 ? 'warn' : '';
        const mixItems = (mix.energy_mix || []).map(x => ({
          label: SOURCE_NAMES[x.source] || title(x.source), value: num(x.energy_kwh),
          color: SRC_COLORS[x.source] || 'var(--c1)', pct: num(x.percentage),
        }));
        const breakdown = load.breakdown || [];
        const maxPct = Math.max(1, ...breakdown.map(b => num(b.percentage)));
        return (
          <>
            <div className="grid kpis">
              <Kpi label="Consumption today" value={nf(m.today_consumption_kwh)} unit="kWh"
                sub={<><span className={`delta ${ch > 0 ? 'up' : 'down'}`}>{ch > 0 ? '▲' : '▼'} {nf(Math.abs(ch), 1)}%</span> vs yesterday ({nf(m.yesterday_same_time_kwh)} kWh)</>} />
              <Kpi label="Month to date" value={nf(num(m.month_to_date_kwh) / 1000, 1)} unit="MWh" sub={facility.name} />
              <Kpi label="Peak demand today" value={nf(m.current_peak_demand_kw)} unit="kW"
                sub={`${nf(util, 1)}% of ${nf(m.sanctioned_demand_kva)} kVA sanctioned`}>
                <Meter cls={utilCls} pct={Math.min(100, util)} />
              </Kpi>
              <Kpi label="Open anomalies" value={m.active_anomalies_count}
                sub={m.active_anomalies_count ? <Link to="alerts">Review alerts →</Link> : 'All meters look healthy'} />
            </div>
            <div className="grid cols-3">
              <Trend fid={fid} tick={tick} />
              <Card head={<>Energy mix <span className="muted small">· last 30 days</span></>}>
                <div className="donut-wrap">
                  <Donut items={mixItems} centerTop={kwh(mix.total_consumption_kwh)} centerBottom="total" fmt={kwh} />
                  <div className="rows">
                    {mixItems.length ? mixItems.map(x => (
                      <div className="row-item" key={x.label}>
                        <div className="top"><span><Swatch color={x.color} />{x.label}</span><b className="num">{nf(x.pct, 1)}%</b></div>
                      </div>
                    )) : <Empty>No data</Empty>}
                  </div>
                </div>
              </Card>
            </div>
            <Card head={<>Load breakdown <span className="muted small">· sub-metered, last 30 days</span></>}>
              <div className="rows">
                {breakdown.length ? breakdown.map((b, i) => (
                  <div className="row-item" key={b.load_category}>
                    <div className="top">
                      <span>{LOAD_NAMES[b.load_category] || title(b.load_category)}</span>
                      <span className="num"><b>{nf(b.percentage, 1)}%</b> <span className="muted">· {kwh(b.energy_kwh)}</span></span>
                    </div>
                    <Meter pct={num(b.percentage) / maxPct * 100} color={PALETTE[i % 5]} />
                  </div>
                )) : <Empty>No sub-metered data yet.</Empty>}
              </div>
            </Card>
          </>
        );
      }}
    </Loader>
  );
}
