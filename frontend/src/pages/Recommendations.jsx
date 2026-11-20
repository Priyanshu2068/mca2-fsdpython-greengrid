import { useState } from 'react';
import { Alert, Button, Card as BCard, Col, Placeholder, Row } from 'react-bootstrap';
import { api, qs } from '../api.js';
import { useApp, hasRole } from '../context.js';
import { useAsync } from '../hooks.js';
import { inr, kwh, list, nf, num, title } from '../format.js';
import { Card, Empty, Kpi, KpiRow, Pill, PromptDialog, Seg, useToast } from '../components/ui.jsx';

function Rec({ x, busy, onAct, canAct }) {
  return (
    <BCard className="rec">
      <BCard.Body className="d-grid gap-2">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-2">
          <div>
            <h3 className="h6 mb-0">{x.title}</h3>
            <div className="text-secondary small">{title(x.rule_category)}{x.meter_identifier ? ` · ${x.meter_identifier}` : ''}</div>
          </div>
          <Pill kind={x.status === 'active' ? 'info' : x.status === 'dismissed' ? 'neutral' : 'good'}>{title(x.status)}</Pill>
        </div>
        <div>{x.description}</div>
        <div className="stats">
          <div><span>Savings / year</span><b className="num" style={{ color: 'var(--good)' }}>{inr(x.estimated_annual_savings_inr)}</b></div>
          <div><span>Energy saved</span><b className="num">{kwh(x.estimated_annual_kwh_savings)}</b></div>
          <div><span>Investment</span><b className="num">{inr(x.implementation_cost_inr)}</b></div>
          <div><span>Payback</span><b className="num">{nf(x.estimated_payback_months, 1)} mo</b></div>
        </div>
        <details><summary className="fw-semibold" style={{ cursor: 'pointer', color: 'var(--brand)' }}>Action plan</summary><pre>{x.action_plan}</pre></details>
        {x.status === 'dismissed' && x.dismissal_reason && <div className="small text-secondary">Dismissed: {x.dismissal_reason}</div>}
        <div className="d-flex flex-wrap gap-2">
          {canAct && x.status === 'active' && (
            <>
              <Button size="sm" variant="primary" disabled={busy} onClick={() => onAct(x, 'accepted')}>Accept</Button>
              <Button size="sm" variant="outline-danger" disabled={busy} onClick={() => onAct(x, 'dismissed')}>Dismiss…</Button>
            </>
          )}
          {canAct && x.status === 'accepted' && <Button size="sm" variant="primary" disabled={busy} onClick={() => onAct(x, 'implemented')}>Mark implemented</Button>}
        </div>
      </BCard.Body>
    </BCard>
  );
}

export default function Recommendations() {
  const { fid, user } = useApp();
  const canAct = hasRole(user, 'admin', 'customer');
  const toast = useToast();
  const [status, setStatus] = useState('active');
  const [busy, setBusy] = useState(null);
  const [prompt, setPrompt] = useState(null); // rec being dismissed
  const summary = useAsync(() => api(`recommendations/summary/?facility_id=${fid}`), [fid]);
  const recs = useAsync(
    async () => list(await api('recommendations/?' + qs({ facility_id: fid, status: status === 'all' ? '' : status }))),
    [fid, status],
  );

  const update = async (x, newStatus, reason) => {
    setBusy(x.id);
    try {
      const body = { status: newStatus };
      if (reason) body.dismissal_reason = reason;
      await api(`recommendations/${x.id}/`, { method: 'PATCH', body });
      toast(`Recommendation ${newStatus}`);
      recs.reload(); summary.reload();
    } catch (err) { toast(err.message, true); }
    setBusy(null);
  };
  const onAct = (x, a) => (a === 'dismissed' ? setPrompt(x) : update(x, a));

  const s = summary.data;
  return (
    <div className="d-grid gap-3">
      {s ? (
        <KpiRow>
          <Kpi label="Potential savings" value={inr(s.total_potential_savings_inr)} sub={`${nf(num(s.total_potential_kwh_savings) / 1000)} MWh per year`} />
          <Kpi label="Accepted" value={inr(s.accepted_annual_savings_inr)} sub={`${s.accepted_count} measure${s.accepted_count === 1 ? '' : 's'} committed`} />
          <Kpi label="Active ideas" value={s.active_count} sub={`of ${s.total_recommendations} generated`} />
          <Kpi label="Dismissed" value={s.dismissed_count} sub="with recorded reasons" />
        </KpiRow>
      ) : (
        <Row xs={1} sm={2} xl={4} className="g-3">
          {[0, 1, 2, 3].map(i => <Col key={i}><BCard><BCard.Body><Placeholder as="div" animation="glow"><Placeholder xs={6} /><Placeholder xs={10} size="lg" /></Placeholder></BCard.Body></BCard></Col>)}
        </Row>
      )}
      <div className="d-flex flex-wrap align-items-center gap-3">
        <Seg value={status} onChange={setStatus} options={['active', 'accepted', 'implemented', 'dismissed', 'all']} />
        {!canAct && <span className="text-secondary small">View only: recommendations are decided by administrators and customers.</span>}
      </div>
      {recs.error && <Alert variant="danger" className="small mb-0">{recs.error.message}</Alert>}
      <div className="d-grid gap-3">
        {recs.data && (recs.data.length
          ? recs.data.map(x => <Rec key={x.id} x={x} busy={busy === x.id} onAct={onAct} canAct={canAct} />)
          : <Card><Empty>Nothing here. Try another filter.</Empty></Card>)}
        {!recs.data && !recs.error && <BCard><BCard.Body><Placeholder as="div" animation="glow"><Placeholder xs={4} /><Placeholder xs={12} /><Placeholder xs={9} /></Placeholder></BCard.Body></BCard>}
      </div>
      {prompt && (
        <PromptDialog heading="Dismiss recommendation" label="Why is this not applicable?" required
          onCancel={() => setPrompt(null)}
          onSubmit={reason => { const x = prompt; setPrompt(null); update(x, 'dismissed', reason); }} />
      )}
    </div>
  );
}
