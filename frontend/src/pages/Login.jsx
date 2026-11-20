import { useState } from 'react';
import { Alert, Button, Card, Form } from 'react-bootstrap';
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
      <Card className="w-100 shadow-sm" style={{ maxWidth: 400 }}>
        <Card.Body className="p-4">
          <Form onSubmit={submit} autoComplete="on" className="d-grid gap-3">
            <div className="brand big"><span className="logo" /><span>GreenGrid</span></div>
            <p className="text-secondary mb-0">Energy management for commercial facilities</p>
            <Form.Group controlId="login-email">
              <Form.Label className="small text-secondary">Email</Form.Label>
              <Form.Control type="email" required autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} />
            </Form.Group>
            <Form.Group controlId="login-password">
              <Form.Label className="small text-secondary">Password</Form.Label>
              <Form.Control type="password" required autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} />
            </Form.Group>
            {isFile && (
              <Alert variant="warning" className="mb-0 small">
                Open the app through a server: run <code>npm run build</code> in <code>frontend/</code>, start Django, and visit{' '}
                <a href="http://127.0.0.1:8000/app/">http://127.0.0.1:8000/app/</a>.
              </Alert>
            )}
            {error && <Alert variant="danger" className="mb-0 small" role="alert" dismissible onClose={() => setError('')}>{error}</Alert>}
            <Button type="submit" variant="primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</Button>
            <div className="text-center">
              <div className="small text-secondary mb-2">Demo accounts</div>
              <div className="d-flex gap-2 justify-content-center flex-wrap">
                {DEMOS.map(([label, mail]) => (
                  <Button key={mail} type="button" size="sm" variant="outline-secondary"
                    onClick={() => { setEmail(mail); setPassword(DEMO_PASSWORD); setError(''); }}>{label}</Button>
                ))}
              </div>
              <p className="small text-secondary mt-2 mb-0">Password for all: <code>{DEMO_PASSWORD}</code></p>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}
