import { useState } from 'react';
import { api, ensureCsrf } from '../api.js';

const DEMO_PASSWORD = 'GreenGrid@123';
const DEMOS = [['Admin', 'admin@greengrid.test'], ['Customer', 'customer@greengrid.test'], ['Field Engineer', 'engineer@greengrid.test']];

export default function Login({ onLogin }) {
  const [email, setEmail] = useState(DEMOS[0][1]);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const isFile = window.location.protocol === 'file:';

  const submit = async e => {
    e.preventDefault();
    setError(''); setBusy(true);
    try {
      await ensureCsrf();
      onLogin(await api('accounts/login/', { method: 'POST', body: { email, password } }));
    } catch (ex) { setError(ex.message); setBusy(false); }
  };

  return (
    <div className="login">
      <form className="login-card" onSubmit={submit} autoComplete="on">
        <div className="brand big"><span className="logo" /><span>GreenGrid</span></div>
        <p className="muted">Energy management for commercial facilities</p>
        <label>Email<input type="email" required autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" required autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} /></label>
        <div className="form-error" role="alert">
          {isFile
            ? <>Open the app through a server: run <code>npm run build</code> in <code>frontend/</code>, start Django, and visit <a href="http://127.0.0.1:8000/app/">http://127.0.0.1:8000/app/</a>.</>
            : error}
        </div>
        <button className="btn primary" type="submit" disabled={busy}>Sign in</button>
        <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
          <span className="muted small" style={{ textAlign: 'center' }}>Demo accounts:</span>
          <div style={{ display: 'flex', gap: 6, justifyContent: 'center', flexWrap: 'wrap' }}>
            {DEMOS.map(([label, mail]) => (
              <button key={mail} type="button" className="btn ghost small" onClick={() => { setEmail(mail); setPassword(DEMO_PASSWORD); setError(''); }}>{label}</button>
            ))}
          </div>
          <p className="hint" style={{ textAlign: 'center', fontSize: 11.5, marginTop: 4 }}>Password for all: <code>{DEMO_PASSWORD}</code></p>
        </div>
      </form>
    </div>
  );
}
