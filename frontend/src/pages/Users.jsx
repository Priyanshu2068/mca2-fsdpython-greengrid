import { useState } from 'react';
import { api } from '../api.js';
import { useApp, hasRole } from '../context.js';
import { useAsync } from '../hooks.js';
import { list, title } from '../format.js';
import { Card, Empty, Loader, Modal, Pill, Table, useToast } from '../components/ui.jsx';

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

const checkRow = { display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text)', fontSize: 14 };

function FacilityChecks({ facilities, value, onChange }) {
  const toggle = id => onChange(value.includes(id) ? value.filter(x => x !== id) : [...value, id]);
  return (
    <div style={{ display: 'grid', gap: 6, maxHeight: 180, overflowY: 'auto' }}>
      {facilities.map(f => (
        <label key={f.id} style={checkRow}>
          <input type="checkbox" checked={value.includes(f.id)} onChange={() => toggle(f.id)} style={{ width: 16, height: 16 }} />
          {f.name} <span className="muted small">{f.code}</span>
        </label>
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
      <form onSubmit={submit} style={{ minWidth: 340 }}>
        <h2>Add user</h2>
        <label>Email<input type="email" required value={f.email} onChange={set('email')} placeholder="name@company.com" autoFocus /></label>
        <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <label>First name<input required value={f.first_name} onChange={set('first_name')} /></label>
          <label>Last name<input value={f.last_name} onChange={set('last_name')} /></label>
        </div>
        <label>Phone<input value={f.phone} onChange={set('phone')} placeholder="optional" /></label>
        <label>Role
          <select value={f.role} onChange={set('role')} disabled={roles.length === 1}>
            {roles.map(r => <option key={r} value={r}>{title(r)}</option>)}
          </select>
        </label>
        <label>Temporary password
          <div style={{ display: 'flex', gap: 8 }}>
            <input required minLength={8} value={f.password} onChange={set('password')} style={{ flex: 1, fontFamily: 'Consolas, monospace' }} />
            <button type="button" className="btn small" onClick={() => setF(s => ({ ...s, password: generatePassword() }))}>Generate</button>
          </div>
        </label>
        <div>
          <div className="small muted" style={{ marginBottom: 6 }}>
            Facility access{isAdmin ? ' (optional)' : ' (at least one)'}
          </div>
          <FacilityChecks facilities={facilities} value={fids} onChange={setFids} />
        </div>
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" type="submit" disabled={saving}>Create user</button>
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
      <div style={{ display: 'grid', gap: 12, minWidth: 320 }}>
        <h2>User created</h2>
        <div className="muted small">Share these sign-in details securely. The password is shown only now and cannot be retrieved later.</div>
        <pre style={{ margin: 0, padding: 12, background: 'var(--surface-2)', borderRadius: 8, fontFamily: 'Consolas, monospace', fontSize: 14, whiteSpace: 'pre-wrap' }}>{text}</pre>
        <div className="actions">
          <button className="btn" onClick={copy}>Copy</button>
          <button className="btn primary" onClick={onClose}>Done</button>
        </div>
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
      <form onSubmit={save} style={{ minWidth: 320 }}>
        <h2>Facility access</h2>
        <div className="muted small">{target.full_name || target.email} · {target.email}</div>
        <FacilityChecks facilities={facilities} value={fids} onChange={setFids} />
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" type="submit" disabled={saving}>Save</button>
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
    <>
      <div className="toolbar" style={{ justifyContent: 'space-between' }}>
        <span className="muted small">
          {isAdmin ? 'Create customers and field engineers and choose which facilities they can see.'
            : 'Add customers for your facilities and manage which of your facilities they can see.'}
        </span>
        <button className="btn primary" onClick={() => setAdding(true)}>+ Add user</button>
      </div>
      <Card head="Users">
        <Loader res={res}>
          {rows => (rows.length ? (
            <Table
              cols={[{ h: 'Name' }, { h: 'Email' }, { h: 'Role' }, { h: 'Facilities', wrap: 1 }, { h: 'Status' }, { h: '' }]}
              rows={rows.map(u => [
                <b>{u.full_name || '—'}</b>, u.email, title(u.role),
                (u.assigned_facility_ids || []).map(id => names[id]).filter(Boolean).join(', ') || <span className="muted">None</span>,
                <Pill kind={u.is_active ? 'good' : 'neutral'}>{u.is_active ? 'Active' : 'Inactive'}</Pill>,
                manageable(u) ? (
                  <div className="actions">
                    <button className="btn small" onClick={() => setEditing(u)}>Edit access</button>
                    {isAdmin && u.id !== user.id && (
                      <button className="btn small ghost" onClick={() => toggleActive(u)}>{u.is_active ? 'Deactivate' : 'Activate'}</button>
                    )}
                  </div>
                ) : '',
              ])} />
          ) : <Empty>No users yet.</Empty>)}
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
    </>
  );
}
