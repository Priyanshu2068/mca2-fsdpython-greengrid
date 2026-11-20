import { useState } from 'react';
import { api } from '../api.js';
import { Modal, useToast } from './ui.jsx';

/** Lets any signed-in user change their own password (the session stays signed in). */
export default function ChangePasswordDialog({ onClose }) {
  const toast = useToast();
  const [f, setF] = useState({ old_password: '', new_password: '', confirm: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const set = k => e => { setF(s => ({ ...s, [k]: e.target.value })); setError(''); };

  const submit = async e => {
    e.preventDefault();
    if (f.new_password.length < 8) { setError('New password must be at least 8 characters.'); return; }
    if (f.new_password !== f.confirm) { setError('The new passwords do not match.'); return; }
    if (f.new_password === f.old_password) { setError('New password must be different from the current one.'); return; }
    setSaving(true);
    try {
      await api('accounts/change-password/', { method: 'POST', body: { old_password: f.old_password, new_password: f.new_password } });
      toast('Password changed');
      onClose();
    } catch (err) { setError(err.message); setSaving(false); }
  };

  return (
    <Modal onClose={onClose}>
      <form onSubmit={submit} style={{ minWidth: 320 }}>
        <h2>Change password</h2>
        <label>Current password
          <input type="password" required autoComplete="current-password" value={f.old_password} onChange={set('old_password')} autoFocus />
        </label>
        <label>New password
          <input type="password" required minLength={8} autoComplete="new-password" value={f.new_password} onChange={set('new_password')} />
        </label>
        <label>Confirm new password
          <input type="password" required minLength={8} autoComplete="new-password" value={f.confirm} onChange={set('confirm')} />
        </label>
        <div className="hint">At least 8 characters, different from your current password.</div>
        <div className="form-error" role="alert">{error}</div>
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" type="submit" disabled={saving}>Change password</button>
        </div>
      </form>
    </Modal>
  );
}
