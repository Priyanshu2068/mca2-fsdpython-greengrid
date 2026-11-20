import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, ensureCsrf, qs, setUnauthorizedHandler } from './api.js';
import { AppCtx } from './context.js';
import { useHashRoute, useLiveTick } from './hooks.js';
import { list, store, title } from './format.js';
import { hasRole } from './context.js';
import { Empty, Card, ToastProvider, useToast } from './components/ui.jsx';
import { ICONS } from './components/Icons.jsx';
import { Link } from './components/Link.jsx';
import ChangePasswordDialog from './components/ChangePassword.jsx';
import Login from './pages/Login.jsx';
import Overview from './pages/Overview.jsx';
import Alerts from './pages/Alerts.jsx';
import Billing from './pages/Billing.jsx';
import Benchmark from './pages/Benchmark.jsx';
import Recommendations from './pages/Recommendations.jsx';
import Renewables from './pages/Renewables.jsx';
import Facilities from './pages/Facilities.jsx';
import Users from './pages/Users.jsx';

const ROUTES = [
  { id: 'overview', name: 'Overview', Page: Overview },
  { id: 'alerts', name: 'Alerts', Page: Alerts },
  { id: 'billing', name: 'Billing', Page: Billing },
  { id: 'benchmark', name: 'Benchmarking', Page: Benchmark },
  { id: 'recs', name: 'Recommendations', Page: Recommendations },
  { id: 'solar', name: 'Renewables & Carbon', Page: Renewables },
  { id: 'sites', name: 'Facilities', Page: Facilities },
  { id: 'users', name: 'Users', Page: Users, roles: ['admin'] },
];

function Shell({ user, onLogout }) {
  const toast = useToast();
  const routeId = useHashRoute();
  const route = ROUTES.find(r => r.id === routeId) || ROUTES[0];
  const allowed = !route.roles || hasRole(user, ...route.roles);
  const [facilities, setFacilities] = useState([]);
  const [fid, setFid] = useState(null);
  const [ready, setReady] = useState(false);
  const [badge, setBadge] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const [pwOpen, setPwOpen] = useState(false);
  const live = useLiveTick(30000);

  useEffect(() => {
    let alive = true;
    api('facilities/?page_size=200').then(list).catch(e => { toast(e.message, true); return []; }).then(fs => {
      if (!alive) return;
      const saved = Number(store.get('gg.fid'));
      setFacilities(fs);
      setFid(fs.find(f => f.id === saved) ? saved : (fs[0] && fs[0].id) || null);
      setReady(true);
    });
    return () => { alive = false; };
  }, [toast]);

  /** Reloads the facility list (e.g. after an admin adds one); optionally selects a facility id. */
  const refreshFacilities = useCallback(async (selectId) => {
    try {
      const fs = list(await api('facilities/?page_size=200'));
      setFacilities(fs);
      setFid(cur => {
        const next = selectId && fs.find(f => f.id === selectId) ? selectId : (fs.find(f => f.id === cur) ? cur : (fs[0] && fs[0].id) || null);
        if (next) store.set('gg.fid', next);
        return next;
      });
      return fs;
    } catch (e) { toast(e.message, true); return []; }
  }, [toast]);

  const refreshBadge = useCallback(async () => {
    if (!fid) return;
    try {
      const a = list(await api('analytics/alerts/?' + qs({ facility_id: fid, status: 'open', page_size: 200 })));
      setBadge(a.length);
    } catch { /* non-critical */ }
  }, [fid]);

  useEffect(() => { refreshBadge(); }, [refreshBadge, route.id, live.tick]);
  useEffect(() => { document.title = `${route.name} · GreenGrid`; setMenuOpen(false); }, [route]);

  const facility = facilities.find(f => f.id === fid) || {};
  const ctx = useMemo(() => ({ user, facilities, fid, facility, refreshBadge, refreshFacilities, tick: live.tick }), [user, facilities, fid, facility, refreshBadge, refreshFacilities, live.tick]);
  const changeFacility = e => { const v = Number(e.target.value); setFid(v); store.set('gg.fid', v); };
  const toggleTheme = () => {
    const cur = document.documentElement.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    store.set('gg.theme', next);
  };

  const Page = route.Page;
  return (
    <AppCtx.Provider value={ctx}>
      <div className="shell">
        <aside className={`sidebar${menuOpen ? ' open' : ''}`}>
          <div className="brand"><span className="logo" /><span>GreenGrid</span></div>
          <nav id="nav">
            {ROUTES.filter(r => !r.roles || hasRole(user, ...r.roles)).map(r => (
              <Link key={r.id} to={r.id} className={r.id === route.id ? 'active' : ''}>
                {ICONS[r.id]}<span>{r.name}</span>
                {r.id === 'alerts' && badge > 0 && <span className="badge">{badge}</span>}
              </Link>
            ))}
          </nav>
          <div className="sidebar-foot">
            <div className="who"><b>{user.full_name || user.email}</b><span>{title(user.role)}</span></div>
            <button className="btn ghost small" onClick={() => setPwOpen(true)}>Change password</button>
            <button className="btn ghost small" onClick={onLogout}>Sign out</button>
          </div>
        </aside>
        <div className="main">
          <header className="topbar">
            <button className="icon-btn menu" aria-label="Toggle navigation" onClick={() => setMenuOpen(o => !o)}>☰</button>
            <h1>{route.name}</h1>
            <div className="spacer" />
            <span className="live" title="Data refreshes automatically every 30 seconds">
              <i className="dot" /><span className="live-text">Live · {live.at.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            </span>
            <button className="icon-btn" aria-label="Refresh now" title="Refresh now" onClick={live.refresh}>⟳</button>
            <label className="fac-select">
              <span className="muted small">Facility</span>
              <select value={fid || ''} onChange={changeFacility}>
                {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </label>
            <button className="icon-btn" aria-label="Toggle theme" title="Toggle theme" onClick={toggleTheme}>◐</button>
          </header>
          <main className="view" tabIndex={-1}>
            {!ready ? null
              : !allowed ? <Card><Empty>Your role does not have access to this page.</Empty></Card>
              : (!fid && route.id !== 'sites' && route.id !== 'users')
                ? <Card><Empty>No facilities are assigned to your account.</Empty></Card>
                : <Page key={`${route.id}:${fid}`} />}
          </main>
          {pwOpen && <ChangePasswordDialog onClose={() => setPwOpen(false)} />}
        </div>
      </div>
    </AppCtx.Provider>
  );
}

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = checking, null = signed out

  useEffect(() => {
    const t = store.get('gg.theme');
    if (t) document.documentElement.setAttribute('data-theme', t);
    setUnauthorizedHandler(() => setUser(null));
    (async () => {
      await ensureCsrf().catch(() => {});
      try { setUser(await api('accounts/me/')); } catch { setUser(null); }
    })();
  }, []);

  const logout = async () => {
    try { await api('accounts/logout/', { method: 'POST' }); } catch { /* ignore */ }
    await ensureCsrf().catch(() => {});
    setUser(null);
  };

  return (
    <ToastProvider>
      {user === undefined ? null : user ? <Shell user={user} onLogout={logout} /> : <Login onLogin={setUser} />}
    </ToastProvider>
  );
}
