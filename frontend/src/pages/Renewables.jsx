import { api, qs } from '../api.js';
import { useApp } from '../context.js';
import { useAsync } from '../hooks.js';
import { SOURCE_NAMES, SRC_COLORS, dt, inr, kwh, list, nf, num, title } from '../format.js';
import { Card, Empty, Kpi, Loader, Pill, Swatch, Table } from '../components/ui.jsx';
import { Donut, LineChart } from '../components/Charts.jsx';

export default function Renewables() {
  const { fid } = useApp();
  const res = useAsync(async () => {
    const day = x => x.toISOString().slice(0, 10);
    const rng = { facility_id: fid, start_date: day(new Date(Date.now() - 30 * 864e5)), end_date: day(new Date()) };
    const [self, em, gen, ev, assets] = await Promise.all([
      api('renewables/self-consumption/?' + qs(rng)),
      api('renewables/emissions/?' + qs(rng)),
      api('renewables/generation/?' + qs({ ...rng, page_size: 5000 })),
      api('renewables/grid-events/?facility_id=' + fid),
      api('renewables/solar-assets/?facility_id=' + fid),
    ]);
    return { self, em, gen: list(gen), events: list(ev), assets: list(assets) };
  }, [fid]);

  return (
    <Loader res={res}>
      {({ self, em, gen, events, assets }) => {
        // API returns the latest <=100 hourly readings, newest first
        const readings = gen.slice().reverse();
        const srcItems = Object.entries(em.breakdown_by_source || {}).map(([k, v]) => ({
          key: k, label: SOURCE_NAMES[k] || title(k), value: num(v.emissions_kg_co2),
          kwh: num(v.energy_kwh), factor: v.factor_kg_per_kwh, color: SRC_COLORS[k] || 'var(--c1)',
        }));
        const capacity = assets.reduce((a, s) => a + num(s.rated_capacity_kwp), 0);
        return (
          <>
            <div className="grid kpis">
              <Kpi label="Solar generation" value={kwh(self.total_solar_generation_kwh)} sub={`${nf(capacity)} kWp installed · 30 days`} />
              <Kpi label="Solar share" value={nf(self.solar_fraction_percentage, 1)} unit="%" sub="of facility consumption" />
              <Kpi label="Cost avoided" value={inr(self.estimated_cost_avoided_inr)} sub="versus grid purchase" />
              <Kpi label="CO₂ emitted" value={nf(em.total_emissions_tco2e, 1)} unit="tCO₂e" sub={`${nf(em.avoided_emissions_tco2e, 1)} tCO₂e avoided by solar`} />
            </div>
            <div className="grid cols-3">
              <Card head={<>Solar generation <span className="muted small">· latest hourly readings</span></>}>
                <LineChart type="bar" labels={readings.map(g => g.timestamp)} fmt={v => nf(v)} label="Hourly solar generation"
                  xTick={l => new Date(l).toLocaleString('en-IN', { day: '2-digit', month: 'short' })} tipLabel={dt}
                  series={[{ name: 'Generation (kWh)', color: 'var(--c3)', values: readings.map(g => num(g.generation_kwh)) }]} />
              </Card>
              <Card head="Emissions by source">
                <div className="donut-wrap">
                  <Donut items={srcItems.filter(s => s.value > 0)} centerTop={nf(em.total_emissions_tco2e, 1)} centerBottom="tCO₂e" fmt={v => nf(v) + ' kg'} />
                  <div className="rows">
                    {srcItems.map(s => (
                      <div className="row-item" key={s.key}>
                        <div className="top"><span><Swatch color={s.color} />{s.label}</span><b className="num">{nf(s.value / 1000, 1)} t</b></div>
                        <div className="small muted">{kwh(s.kwh)} × {s.factor} kg/kWh</div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
            <Card head="Grid events &amp; outages">
              {events.length ? (
                <Table
                  cols={[{ h: 'Event' }, { h: 'Started' }, { h: 'Duration', r: 1 }, { h: 'Diesel used', r: 1 }, { h: 'Restored' }, { h: 'Notes', wrap: 1 }]}
                  rows={events.map(e => [
                    e.event_type_display, dt(e.start_time), `${nf(e.duration_minutes, 0)} min`, `${nf(e.fuel_consumed_litres, 0)} L`,
                    e.grid_restored ? <Pill kind="good">Yes</Pill> : <Pill kind="bad">Ongoing</Pill>, e.notes,
                  ])} />
              ) : <Empty>No grid events recorded.</Empty>}
            </Card>
          </>
        );
      }}
    </Loader>
  );
}
