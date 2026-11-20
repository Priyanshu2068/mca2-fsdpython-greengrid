import { useCallback, useEffect, useMemo, useState } from 'react';
import { Badge, Button, Dropdown, Form, Offcanvas } from 'react-bootstrap';
import { api, ensureCsrf, qs, setUnauthorizedHandler } from './api.js';
import { AppCtx, hasRole } from './context.js';
import { useHashRoute } from './hooks.js';
import { list, store, title } from './format.js';
import { Empty, Card, ToastProvider, useToast } from './components/ui.jsx';
import { ICONS } from './components/Icons.jsx';
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
  { id: 'users', name: 'Users', Page: Users, roles: ['admin', 'field_engineer'] },
];

const systemTheme = () => (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
const currentTheme = () => document.documentElement.getAttribute('data-bs-theme') || systemTheme();

function Brand() {
  return <div className="brand"><span className="logo" /><span>GreenGrid</span></div>;
}

function SideNav({ routes, activeId, badge, onNavigate }) {
  return (
    <nav className="side-nav nav flex-column gap-1" aria-label="Main">
      {routes.map(r => (
        <a key={r.id} href={`#/${r.id}`} className={`nav-link${r.id === activeId ? ' active' : ''}`} onClick={onNavigate}>
          {ICONS[r.id]}<span>{r.name}</span>
          {r.id === 'alerts' && badge > 0 && <Badge pill bg="danger">{badge}</Badge>}
        </a>
      ))}
    </nav>
  );
}

function Shell({ user, onLogout }) {
  const toast = useToast();
  const routeId = useHashRoute();
  const route = ROUTES.find(r => r.id === routeId) || ROUTES[0];
  const allowed = !route.roles || hasRole(user, ...route.roles);
  const visible = ROUTES.filter(r => !r.roles || hasRole(user, ...r.roles));
  const [facilities, setFacilities] = useState([]);
  const [fid, setFid] = useState(null);
  const [ready, setReady] = useState(false);
  const [badge, setBadge] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState(currentTheme);

  useEffect(() => {
    let live = true;
    api('facilities/?page_size=200').then(list).catch(e => { toast(e.message, true); return []; }).then(fs => {
      if (!live) return;
      const saved = Number(store.get('gg.fid'));
      setFacilities(fs);
      setFid(fs.find(f => f.id === saved) ? saved : (fs[0] && fs[0].id) || null);
      setReady(true);
    });
    return () => { live = false; };
  }, [toast]);

  const refreshBadge = useCallback(async () => {
    if (!fid) return;
    try {
      const a = list(await api('analytics/alerts/?' + qs({ facility_id: fid, status: 'open', page_size: 200 })));
      setBadge(a.length);
    } catch { /* non-critical */ }
  }, [fid]);

  useEffect(() => { refreshBadge(); }, [refreshBadge, route.id]);
  useEffect(() => { document.title = `${route.name} · GreenGrid`; setMenuOpen(false); }, [route]);

  const facility = facilities.find(f => f.id === fid) || {};
  const ctx = useMemo(() => ({ user, facilities, fid, facility, refreshBadge }), [user, facilities, fid, facility, refreshBadge]);
  const changeFacility = e => { const v = Number(e.target.value); setFid(v); store.set('gg.fid', v); };
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', next);
    store.set('gg.theme', next);
    setTheme(next);
  };

  const Page = route.Page;
  return (
    <AppCtx.Provider value={ctx}>
      <div className="app-shell">
        <aside className="sidebar d-none d-lg-flex">
          <Brand />
          <SideNav routes={visible} activeId={route.id} badge={badge} />
          <div className="mt-auto px-2 small">
            <div className="fw-semibold">{user.full_name || user.email}</div>
            <div className="text-secondary mb-2">{title(user.role)}</div>
            <Button size="sm" variant="outline-secondary" onClick={onLogout}>Sign out</Button>
          </div>
        </aside>

        <Offcanvas show={menuOpen} onHide={() => setMenuOpen(false)} className="d-lg-none" style={{ maxWidth: 280 }}>
          <Offcanvas.Header closeButton><Brand /></Offcanvas.Header>
          <Offcanvas.Body className="d-flex flex-column">
            <SideNav routes={visible} activeId={route.id} badge={badge} onNavigate={() => setMenuOpen(false)} />
            <div className="mt-auto small">
              <div className="fw-semibold">{user.full_name || user.email}</div>
              <div className="text-secondary mb-2">{title(user.role)}</div>
              <Button size="sm" variant="outline-secondary" onClick={onLogout}>Sign out</Button>
            </div>
          </Offcanvas.Body>
        </Offcanvas>

        <div className="main-col">
          <header className="topbar d-flex align-items-center gap-2 px-3 py-2">
            <Button variant="outline-secondary" className="d-lg-none" aria-label="Open navigation" onClick={() => setMenuOpen(true)}>☰</Button>
            <h1 className="h5 mb-0 me-auto">{route.name}</h1>
            <Form.Select size="sm" aria-label="Facility" style={{ maxWidth: 230 }} value={fid || ''} onChange={changeFacility}>
              {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
            </Form.Select>
            <Button variant="outline-secondary" size="sm" aria-label="Toggle theme" title="Toggle light / dark theme" onClick={toggleTheme}>
              {theme === 'dark' ? '☀' : '☾'}
            </Button>
            <Dropdown align="end">
              <Dropdown.Toggle variant="outline-secondary" size="sm" id="user-menu">{(user.first_name || user.email)[0].toUpperCase()}</Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.ItemText className="small">
                  <div className="fw-semibold">{user.full_name || user.email}</div>
                  <div className="text-secondary">{title(user.role)}</div>
                </Dropdown.ItemText>
                <Dropdown.Divider />
                <Dropdown.Item onClick={onLogout}>Sign out</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          </header>
          <main className="view" tabIndex={-1}>
            {!ready ? null
              : !allowed ? <Card><Empty>Your role does not have access to this page.</Empty></Card>
              : (!fid && route.id !== 'sites' && route.id !== 'users')
                ? <Card><Empty>No facilities are assigned to your account.</Empty></Card>
                : <Page key={`${route.id}:${fid}`} />}
          </main>
        </div>
      </div>
    </AppCtx.Provider>
  );
}

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = checking, null = signed out

  useEffect(() => {
    document.documentElement.setAttribute('data-bs-theme', store.get('gg.theme') || systemTheme());
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
