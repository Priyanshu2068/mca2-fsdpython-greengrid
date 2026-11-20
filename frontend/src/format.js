export const num = v => (v == null || v === '' ? 0 : Number(v));
export const nf = (v, d = 0) => num(v).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d });
export const kwh = v => {
  const n = num(v);
  return Math.abs(n) >= 1e6 ? nf(n / 1e6, 2) + ' GWh' : Math.abs(n) >= 1e4 ? nf(n / 1e3, 1) + ' MWh' : nf(n, 0) + ' kWh';
};
export const inr = v => {
  const n = num(v), a = Math.abs(n);
  if (a >= 1e7) return '₹' + nf(n / 1e7, 2) + ' Cr';
  if (a >= 1e5) return '₹' + nf(n / 1e5, 2) + ' L';
  return '₹' + nf(n, 0);
};
export const dt = s => s ? new Date(s).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—';
export const dOnly = s => s ? new Date(s + (s.length === 10 ? 'T00:00:00' : '')).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
export const title = s => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
export const list = d => (d && d.results) ? d.results : (Array.isArray(d) ? d : []);

export const LOAD_NAMES = { hvac: 'HVAC & Chillers', it_infrastructure: 'IT & Servers', lighting: 'Lighting', auxiliary_pumps: 'Pumps', elevators: 'Elevators', ev_chargers: 'EV Charging', main_incomer: 'Main Incomer' };
export const SOURCE_NAMES = { grid: 'Utility Grid', diesel_generator: 'Diesel Generator', solar: 'Solar PV', water: 'Water', gas: 'Gas', natural_gas: 'Natural Gas' };
export const SRC_COLORS = { grid: 'var(--c2)', diesel_generator: 'var(--c5)', solar: 'var(--c3)', gas: 'var(--c4)', natural_gas: 'var(--c4)', water: 'var(--c1)' };
export const PALETTE = ['var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)'];

export const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } },
};
