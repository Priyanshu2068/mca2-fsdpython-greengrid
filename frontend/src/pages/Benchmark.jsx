import { api } from '../api.js';
import { useApp } from '../context.js';
import { useAsync } from '../hooks.js';
import { kwh, list, nf, num, title } from '../format.js';
import { Card, Empty, Loader, Pill, Stars, Table } from '../components/ui.jsx';

function Gauge({ mine, bm }) {
  const lo = num(bm.top_20_percentile_eui), hi = num(bm.bottom_20_percentile_eui);
  const med = num(bm.median_eui_kwh_sqm_year), val = num(mine.calculated_eui_kwh_sqm_year);
  const max = Math.max(hi * 1.1, val * 1.1);
  const pos = v => Math.min(100, v / max * 100);
  return (
    <>
      <div style={{
        position: 'relative', height: 14, borderRadius: 9, margin: '26px 0 8px',
        background: `linear-gradient(90deg,var(--good-bg) ${pos(lo)}%,var(--warn-bg) ${pos(lo)}%,var(--warn-bg) ${pos(hi)}%,var(--bad-bg) ${pos(hi)}%)`,
      }}>
        <span title="This facility" style={{ position: 'absolute', left: `${pos(val)}%`, top: -6, width: 4, height: 26, borderRadius: 3, background: 'var(--brand)', transform: 'translateX(-2px)' }} />
        <span className="small muted" style={{ position: 'absolute', left: `${pos(val)}%`, top: -24, transform: 'translateX(-50%)', whiteSpace: 'nowrap', color: 'var(--brand)', fontWeight: 600 }}>{nf(val, 1)}</span>
        <span className="small muted" style={{ position: 'absolute', left: `${pos(med)}%`, top: 20, transform: 'translateX(-50%)' }}>median {nf(med)}</span>
      </div>
      <div className="small muted" style={{ marginTop: 22 }}>
        Energy use intensity (kWh/m²/yr). Left of {nf(lo)} is top-20% efficient; right of {nf(hi)} is bottom-20%.
      </div>
    </>
  );
}

const Stat = ({ label, children }) => (
  <div><div className="muted small">{label}</div><b className="num" style={{ fontSize: 20 }}>{children}</b></div>
);

export default function Benchmark() {
  const { fid } = useApp();
  const res = useAsync(async () => {
    const [rank, std] = await Promise.all([api('benchmarking/ranking/'), api('benchmarking/standards/')]);
    return { R: list(rank), S: list(std) };
  }, [fid]);

  return (
    <Loader res={res}>
      {({ R, S }) => {
        const mine = R.find(r => r.facility === fid);
        const bm = mine && S.find(s => s.facility_type === mine.facility_type);
        return (
          <>
            {mine ? (
              <div className="grid cols-2">
                <Card head={mine.facility_name}>
                  <div style={{ fontSize: 30 }}><Stars n={mine.star_rating} /></div>
                  <div className="grid kpis" style={{ marginTop: 12, gridTemplateColumns: 'repeat(3,1fr)' }}>
                    <Stat label="EUI">{nf(mine.calculated_eui_kwh_sqm_year, 1)}</Stat>
                    <Stat label="Percentile">{nf(mine.national_percentile)}</Stat>
                    <Stat label={`Energy (${mine.year})`}>{kwh(mine.annual_energy_kwh)}</Stat>
                  </div>
                </Card>
                <Card head={`Where you sit vs. ${title(mine.facility_type)} peers`}>
                  {bm ? <Gauge mine={mine} bm={bm} /> : <Empty>No standard available.</Empty>}
                </Card>
              </div>
            ) : <Card><Empty>No benchmark has been computed for this facility yet.</Empty></Card>}
            <Card head={<>Facility ranking {R.some(r => r.facility === null) && <span className="muted small">· facilities you can't access are shown anonymously</span>}</>}>
              {R.length ? (
                <Table
                  cols={[{ h: '#' }, { h: 'Facility' }, { h: 'Type' }, { h: 'EUI', r: 1 }, { h: 'Percentile', r: 1 }, { h: 'Rating' }]}
                  rows={R.map((r, i) => [i + 1, <><b>{r.facility_name}</b>{r.facility === fid && <> <Pill kind="info">Selected</Pill></>}</>, title(r.facility_type), nf(r.calculated_eui_kwh_sqm_year, 1), nf(r.national_percentile), <Stars n={r.star_rating} />])} />
              ) : <Empty>No data.</Empty>}
            </Card>
            <Card head={<>BEE benchmark standards <span className="muted small">· kWh/m²/year</span></>}>
              <Table
                cols={[{ h: 'Facility type' }, { h: 'Top 20%', r: 1 }, { h: 'Median', r: 1 }, { h: 'Bottom 20%', r: 1 }, { h: 'Standard' }]}
                rows={S.map(s => [s.facility_type_display, nf(s.top_20_percentile_eui), nf(s.median_eui_kwh_sqm_year), nf(s.bottom_20_percentile_eui), <span className="muted">{s.benchmark_standard}</span>])} />
            </Card>
          </>
        );
      }}
    </Loader>
  );
}
