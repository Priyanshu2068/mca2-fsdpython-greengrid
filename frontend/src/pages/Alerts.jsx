import { useState } from 'react';
import { Alert, Button, ButtonGroup } from 'react-bootstrap';
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
      <div className="mb-3">
        <Seg value={status} onChange={setStatus} options={['open', 'acknowledged', 'resolved', 'all']} />
      </div>
      {!canAct && <Alert variant="secondary" className="small py-2">View only: alerts are handled by administrators and field engineers.</Alert>}
      {res.error && <Alert variant="danger" className="small">{res.error.message}</Alert>}
      {res.data && (rows.length ? (
        <Table
          cols={[{ h: 'Severity' }, { h: 'Type' }, { h: 'Meter' }, { h: 'Details', wrap: 1 }, { h: 'Detected' }, { h: 'Status' }, ...(canAct ? [{ h: '' }] : [])]}
          rows={rows.map(a => [
            <Pill kind={sevKind(a.severity)}>{a.severity}</Pill>,
            title(a.anomaly_type), a.meter_identifier, a.reason, dt(a.detected_at),
            <Pill kind={a.status === 'open' ? 'warn' : a.status === 'resolved' ? 'good' : 'neutral'}>{title(a.status)}</Pill>,
            ...(!canAct ? [] : [(a.status === 'open' || a.status === 'acknowledged') ? (
              <ButtonGroup size="sm">
                {a.status === 'open' && <Button variant="outline-secondary" disabled={busy === a.id} onClick={() => act(a, 'acknowledged')}>Acknowledge</Button>}
                <Button variant="outline-success" disabled={busy === a.id} onClick={() => act(a, 'resolved')}>Resolve</Button>
                <Button variant="outline-secondary" disabled={busy === a.id} onClick={() => act(a, 'false_positive')}>False positive</Button>
              </ButtonGroup>
            ) : '']),
          ])} />
      ) : <Empty>{status === 'open' ? '✓ No open alerts. Everything looks healthy.' : 'No alerts match this filter.'}</Empty>)}
      {!res.data && !res.error && <div className="placeholder-glow"><span className="placeholder col-12" style={{ height: 120 }} /></div>}
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
