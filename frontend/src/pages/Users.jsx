import { useState } from 'react';
import { Button, ButtonGroup, Col, Form, InputGroup, Row } from 'react-bootstrap';
import { api } from '../api.js';
import { useApp, hasRole } from '../context.js';
import { useAsync } from '../hooks.js';
import { list, title } from '../format.js';
import { Card, Empty, Field, Loader, Modal, Pill, Table, useToast } from '../components/ui.jsx';

const SETS = ['ABCDEFGHJKLMNPQRSTUVWXYZ', 'abcdefghijkmnpqrstuvwxyz', '23456789', '#$%&*?'];

/** Random 14-character password containing upper, lower, digit and symbol characters. */
function generatePassword() {
  const all = SETS.join('');
  const rnd = n => { const a = new Uint32Array(1); crypto.getRandomValues(a); return a[0] % n; };
  const chars = SETS.map(s => s[rnd(s.length)]);
  while (chars.length < 14) chars.push(all[rnd(all.length)]);
  for (let i = chars.length - 1; i > 0; i--) { const j = rnd(i + 1); [chars[i], chars[j]] = [chars[j], chars[i]]; }
  return chars.join('');
}

function FacilityChecks({ facilities, value, onChange }) {
  const toggle = id => onChange(value.includes(id) ? value.filter(x => x !== id) : [...value, id]);
  return (
    <div className="border rounded p-2" style={{ maxHeight: 180, overflowY: 'auto' }}>
      {facilities.map(f => (
        <Form.Check key={f.id} type="checkbox" id={`fac-${f.id}`} checked={value.includes(f.id)} onChange={() => toggle(f.id)}
          label={<>{f.name} <span className="text-secondary small">{f.code}</span></>} />
      ))}
    </div>
  );
}

function AddUserDialog({ roles, facilities, isAdmin, onClose, onCreated }) {
  const toast = useToast();
  const [f, setF] = useState({ email: '', first_name: '', last_name: '', phone: '', password: generatePassword(), role: roles[0] });
  const [fids, setFids] = useState(facilities.length === 1 ? [facilities[0].id] : []);
  const [saving, setSaving] = useState(false);
  const set = k => e => setF(s => ({ ...s, [k]: e.target.value }));

  const submit = async e => {
    e.preventDefault();
    if (!isAdmin && !fids.length) { toast('Select at least one facility.', true); return; }
    setSaving(true);
    try {
      await api('accounts/users/', { method: 'POST', body: { ...f, email: f.email.trim(), facility_ids: fids } });
      onCreated({ email: f.email.trim().toLowerCase(), password: f.password });
    } catch (err) { toast(err.message, true); setSaving(false); }
  };

  return (
    <Modal onClose={onClose}>
      <form onSubmit={submit}>
        <h2 className="h5 mb-3">Add user</h2>
        <Field label="Email"><Form.Control type="email" required value={f.email} onChange={set('email')} placeholder="name@company.com" autoFocus /></Field>
        <Row className="g-3">
          <Col sm={6}><Field label="First name"><Form.Control required value={f.first_name} onChange={set('first_name')} /></Field></Col>
          <Col sm={6}><Field label="Last name"><Form.Control value={f.last_name} onChange={set('last_name')} /></Field></Col>
        </Row>
        <Row className="g-3">
          <Col sm={6}><Field label="Phone"><Form.Control value={f.phone} onChange={set('phone')} placeholder="optional" /></Field></Col>
          <Col sm={6}>
            <Field label="Role">
              <Form.Select value={f.role} onChange={set('role')} disabled={roles.length === 1}>
                {roles.map(r => <option key={r} value={r}>{title(r)}</option>)}
              </Form.Select>
            </Field>
          </Col>
        </Row>
        <Field label="Temporary password">
          <InputGroup>
            <Form.Control required minLength={8} value={f.password} onChange={set('password')} style={{ fontFamily: 'Consolas, monospace' }} />
            <Button type="button" variant="outline-secondary" onClick={() => setF(s => ({ ...s, password: generatePassword() }))}>Generate</Button>
          </InputGroup>
        </Field>
        <Field label={`Facility access${isAdmin ? ' (optional)' : ' (at least one)'}`}>
          <FacilityChecks facilities={facilities} value={fids} onChange={setFids} />
        </Field>
        <div className="d-flex justify-content-end gap-2">
          <Button type="button" variant="outline-secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={saving}>{saving ? 'Creating…' : 'Create user'}</Button>
        </div>
      </form>
    </Modal>
  );
}

function CredentialsDialog({ creds, onClose }) {
  const toast = useToast();
  const text = `Email: ${creds.email}\nPassword: ${creds.password}`;
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); toast('Copied to clipboard'); } catch { toast('Could not copy. Select and copy manually.', true); }
  };
  return (
    <Modal onClose={onClose}>
      <h2 className="h5 mb-2">User created</h2>
      <p className="text-secondary small">Share these sign-in details securely. The password is shown only now and cannot be retrieved later.</p>
      <pre className="p-3 rounded bg-body-tertiary" style={{ fontFamily: 'Consolas, monospace', whiteSpace: 'pre-wrap' }}>{text}</pre>
      <div className="d-flex justify-content-end gap-2">
        <Button variant="outline-secondary" onClick={copy}>Copy</Button>
        <Button variant="primary" onClick={onClose}>Done</Button>
      </div>
    </Modal>
  );
}

function AccessDialog({ target, facilities, onClose, onSaved }) {
  const toast = useToast();
  const known = new Set(facilities.map(f => f.id));
  const [fids, setFids] = useState((target.assigned_facility_ids || []).filter(id => known.has(id)));
  const [saving, setSaving] = useState(false);
  const save = async e => {
    e.preventDefault();
    setSaving(true);
    try {
      await api(`accounts/users/${target.id}/facilities/`, { method: 'PUT', body: { facility_ids: fids } });
      toast('Facility access updated');
      onSaved();
    } catch (err) { toast(err.message, true); setSaving(false); }
  };
  return (
    <Modal onClose={onClose}>
      <form onSubmit={save}>
        <h2 className="h5 mb-1">Facility access</h2>
        <div className="text-secondary small mb-3">{target.full_name || target.email} · {target.email}</div>
        <Field label="Facilities this user can see"><FacilityChecks facilities={facilities} value={fids} onChange={setFids} /></Field>
        <div className="d-flex justify-content-end gap-2">
          <Button type="button" variant="outline-secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={saving}>{saving ? 'Saving…' : 'Save'}</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function Users() {
  const { user, facilities } = useApp();
  const toast = useToast();
  const isAdmin = hasRole(user, 'admin');
  const roles = isAdmin ? ['customer', 'field_engineer'] : ['customer'];
  const [adding, setAdding] = useState(false);
  const [creds, setCreds] = useState(null);
  const [editing, setEditing] = useState(null);
  const [q, setQ] = useState('');
  const res = useAsync(async () => list(await api('accounts/users/?page_size=200')), []);
  const names = Object.fromEntries(facilities.map(f => [f.id, f.name]));
  const manageable = u => roles.includes(u.role) && !u.is_superuser;

  const toggleActive = async u => {
    try {
      await api(`accounts/users/${u.id}/`, { method: 'PATCH', body: { is_active: !u.is_active } });
      toast(u.is_active ? 'User deactivated' : 'User activated');
      res.reload();
    } catch (err) { toast(err.message, true); }
  };

  return (
    <div className="d-grid gap-3">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2">
        <span className="text-secondary small">
          {isAdmin ? 'Create customers and field engineers and choose which facilities they can see.'
            : 'Add customers for your facilities and manage which of your facilities they can see.'}
        </span>
        <Button variant="primary" onClick={() => setAdding(true)}>+ Add user</Button>
      </div>
      <Card head={<div className="d-flex flex-wrap align-items-center justify-content-between gap-2 w-100"><span>Users</span><Form.Control size="sm" type="search" placeholder="Search name or email" value={q} onChange={e => setQ(e.target.value)} style={{ maxWidth: 240 }} /></div>}>
        <Loader res={res}>
          {all => {
            const term = q.trim().toLowerCase();
            const rows = term ? all.filter(u => `${u.full_name} ${u.email}`.toLowerCase().includes(term)) : all;
            return rows.length ? (
              <Table
                cols={[{ h: 'Name' }, { h: 'Email' }, { h: 'Role' }, { h: 'Facilities', wrap: 1 }, { h: 'Status' }, { h: '' }]}
                rows={rows.map(u => [
                  <b>{u.full_name || '—'}</b>, u.email, title(u.role),
                  (u.assigned_facility_ids || []).map(id => names[id]).filter(Boolean).join(', ') || <span className="text-secondary">None</span>,
                  <Pill kind={u.is_active ? 'good' : 'neutral'}>{u.is_active ? 'Active' : 'Inactive'}</Pill>,
                  manageable(u) ? (
                    <ButtonGroup size="sm">
                      <Button variant="outline-secondary" onClick={() => setEditing(u)}>Edit access</Button>
                      {isAdmin && u.id !== user.id && (
                        <Button variant={u.is_active ? 'outline-danger' : 'outline-success'} onClick={() => toggleActive(u)}>{u.is_active ? 'Deactivate' : 'Activate'}</Button>
                      )}
                    </ButtonGroup>
                  ) : '',
                ])} />
            ) : <Empty>{term ? 'No users match your search.' : 'No users yet.'}</Empty>;
          }}
        </Loader>
      </Card>
      {adding && (
        <AddUserDialog roles={roles} facilities={facilities} isAdmin={isAdmin} onClose={() => setAdding(false)}
          onCreated={c => { setAdding(false); setCreds(c); res.reload(); }} />
      )}
      {creds && <CredentialsDialog creds={creds} onClose={() => setCreds(null)} />}
      {editing && (
        <AccessDialog target={editing} facilities={facilities} onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); res.reload(); }} />
      )}
    </div>
  );
}
