import { useState } from 'react';
import { api, qs } from '../api.js';
import { useApp, hasRole } from '../context.js';
import { useAsync } from '../hooks.js';
import { dt, list, title } from '../format.js';
import { Card, Empty, Pill, PromptDialog, Seg, Table, sevKind, useToast } from '../components/ui.jsx';

export default function Alerts() {
  const { fid, refreshBadge, user } = useApp();
  const canAct = hasRole(user, 'admin', 'field_engineer');
  const toast = useToast();
  const [status, setStatus] = useState('open');
  const [busy, setBusy] = useState(null);
  const [prompt, setPrompt] = useState(null); // {id, action}
  const res = useAsync(
    async () => list(await api('analytics/alerts/?' + qs({ facility_id: fid, status: status === 'all' ? '' : status, page_size: 200 }))),
    [fid, status],
  );

  const update = async (id, action, notes = '') => {
    setBusy(id);
    try {
      await api(`analytics/alerts/${id}/`, { method: 'PATCH', body: { status: action, resolution_notes: notes } });
      toast('Alert updated');
      res.reload();
      refreshBadge();
    } catch (err) { toast(err.message, true); }
    setBusy(null);
  };

  const act = (a, action) => {
    if (action === 'acknowledged') update(a.id, action);
    else setPrompt({ id: a.id, action });
  };

  const rows = res.data || [];
  return (
    <Card head="Anomaly alerts">
      <div className="toolbar" style={{ marginBottom: 12 }}>
        <Seg value={status} onChange={setStatus} options={['open', 'acknowledged', 'resolved', 'all']} />
      </div>
      {!canAct && <div className="muted small" style={{ marginBottom: 10 }}>View only: alerts are handled by administrators and field engineers.</div>}
      {res.error && <div className="form-error" role="alert">{res.error.message}</div>}
      {res.data && (rows.length ? (
        <Table
          cols={[{ h: 'Severity' }, { h: 'Type' }, { h: 'Meter' }, { h: 'Details', wrap: 1 }, { h: 'Detected' }, { h: 'Status' }, ...(canAct ? [{ h: '' }] : [])]}
          rows={rows.map(a => [
            <Pill kind={sevKind(a.severity)}>{a.severity}</Pill>,
            title(a.anomaly_type), a.meter_identifier, a.reason, dt(a.detected_at),
            <Pill kind={a.status === 'open' ? 'warn' : a.status === 'resolved' ? 'good' : 'neutral'}>{title(a.status)}</Pill>,
            ...(!canAct ? [] : [(a.status === 'open' || a.status === 'acknowledged') ? (
              <div className="actions">
                {a.status === 'open' && <button className="btn small" disabled={busy === a.id} onClick={() => act(a, 'acknowledged')}>Acknowledge</button>}
                <button className="btn small" disabled={busy === a.id} onClick={() => act(a, 'resolved')}>Resolve</button>
                <button className="btn small ghost" disabled={busy === a.id} onClick={() => act(a, 'false_positive')}>False positive</button>
              </div>
            ) : '']),
          ])} />
      ) : <Empty>{status === 'open' ? '✓ No open alerts. Everything looks healthy.' : 'No alerts match this filter.'}</Empty>)}
      {!res.data && !res.error && <div className="skeleton" />}
      {prompt && (
        <PromptDialog
          heading={prompt.action === 'resolved' ? 'Resolve alert' : 'Mark as false positive'}
          label="Resolution notes" required
          onCancel={() => setPrompt(null)}
          onSubmit={notes => { const p = prompt; setPrompt(null); update(p.id, p.action, notes); }} />
      )}
    </Card>
  );
}
