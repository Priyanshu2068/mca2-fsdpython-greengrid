import { useState } from 'react';
import { Button, Col, Form, Row } from 'react-bootstrap';
import { api, qs } from '../api.js';
import { useApp, hasRole } from '../context.js';
import { useAsync } from '../hooks.js';
import { dOnly, inr, list, nf, num, title } from '../format.js';
import { Card, Empty, Field, Kpi, KpiRow, Loader, Modal, Pill, Table, useToast } from '../components/ui.jsx';

const REC_STATUS = {
  verified_within_tolerance: ['Verified', 'good'],
  variance_minor: ['Minor variance', 'warn'],
  variance_action_required: ['Action required', 'bad'],
};

const BLANK = {
  tariff: '', bill_number: '', billing_cycle_start: '', billing_cycle_end: '', due_date: '',
  billed_kwh: '', billed_max_demand_kva: '', billed_amount_inr: '', payment_status: 'unpaid',
};

/** Manual bill entry (admins and field engineers, e.g. emergency or offline entry). */
function BillDialog({ facilityId, facilityName, onClose, onDone }) {
  const toast = useToast();
  const tariffs = useAsync(async () => list(await api('billing/tariffs/')), []);
  const [f, setF] = useState(BLANK);
  const [saving, setSaving] = useState(false);
  const set = k => e => setF(s => ({ ...s, [k]: e.target.value }));
  const submit = async e => {
    e.preventDefault();
    setSaving(true);
    try {
      const body = { ...f, facility: facilityId, tariff: Number(f.tariff), bill_number: f.bill_number.trim() };
      await api('billing/bills/', { method: 'POST', body });
      toast(`Recorded bill ${body.bill_number}`);
      onDone();
    } catch (err) { toast(err.message, true); setSaving(false); }
  };
  const num2 = (k, label, step) => (
    <Field label={label}><Form.Control type="number" required min="0" step={step} value={f[k]} onChange={set(k)} /></Field>
  );
  return (
    <Modal onClose={onClose}>
      <form onSubmit={submit}>
        <h2 className="h5 mb-1">Record utility bill</h2>
        <div className="text-secondary small mb-3">{facilityName}</div>
        <Field label="Tariff">
          <Form.Select required value={f.tariff} onChange={set('tariff')}>
            <option value="" disabled>{tariffs.loading ? 'Loading…' : 'Select tariff'}</option>
            {(tariffs.data || []).map(t => <option key={t.id} value={t.id}>{t.provider_name} · {t.tariff_name}</option>)}
          </Form.Select>
        </Field>
        <Field label="Bill number"><Form.Control required placeholder="e.g. BESCOM-2026-03-0142" value={f.bill_number} onChange={set('bill_number')} /></Field>
        <Row className="g-3">
          <Col xs={6}><Field label="Cycle start"><Form.Control type="date" required value={f.billing_cycle_start} onChange={set('billing_cycle_start')} /></Field></Col>
          <Col xs={6}><Field label="Cycle end"><Form.Control type="date" required value={f.billing_cycle_end} onChange={set('billing_cycle_end')} /></Field></Col>
        </Row>
        <Field label="Due date"><Form.Control type="date" required value={f.due_date} onChange={set('due_date')} /></Field>
        <Row className="g-3">
          <Col xs={6}>{num2('billed_kwh', 'Billed kWh', '0.0001')}</Col>
          <Col xs={6}>{num2('billed_max_demand_kva', 'Max demand (kVA)', '0.01')}</Col>
        </Row>
        {num2('billed_amount_inr', 'Billed amount (₹)', '0.01')}
        <Field label="Payment status">
          <Form.Select value={f.payment_status} onChange={set('payment_status')}>
            <option value="unpaid">Unpaid</option><option value="paid">Paid</option><option value="disputed">Disputed</option>
          </Form.Select>
        </Field>
        <div className="small text-secondary mb-3">The bill is reconciled against metered energy automatically.</div>
        <div className="d-flex justify-content-end gap-2">
          <Button type="button" variant="outline-secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={saving}>{saving ? 'Saving…' : 'Record bill'}</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function Billing() {
  const { fid, facility, user } = useApp();
  const [adding, setAdding] = useState(false);
  const canRecord = hasRole(user, 'admin', 'field_engineer');
  const res = useAsync(async () => {
    const [bills, recs] = await Promise.all([
      api('billing/bills/?' + qs({ facility_id: fid, page_size: 100 })),
      api('billing/reconciliations/?' + qs({ facility_id: fid })),
    ]);
    return { B: list(bills), R: list(recs) };
  }, [fid]);

  return (
    <Loader res={res}>
      {({ B, R }) => {
        const flagged = R.filter(r => r.reconciliation_status === 'variance_action_required');
        const totalBilled = B.reduce((a, b) => a + num(b.billed_amount_inr), 0);
        const leak = R.reduce((a, r) => a + Math.max(0, num(r.variance_cost_inr)), 0);
        return (
          <div className="d-grid gap-3">
            {canRecord && (
              <div className="d-flex flex-wrap align-items-center justify-content-end gap-2">
                <span className="text-secondary small">Manual entry, e.g. emergency or offline bills</span>
                <Button variant="primary" onClick={() => setAdding(true)}>+ Record bill</Button>
              </div>
            )}
            {adding && (
              <BillDialog facilityId={fid} facilityName={facility.name} onClose={() => setAdding(false)}
                onDone={() => { setAdding(false); res.reload(); }} />
            )}
            <KpiRow>
              <Kpi label="Bills on record" value={B.length} sub={facility.name} />
              <Kpi label="Total billed" value={inr(totalBilled)} sub="across all cycles" />
              <Kpi label="Flagged for audit" value={flagged.length} sub={flagged.length ? 'variance above 2.5%' : 'No disputes needed'} />
              <Kpi label="Potential over-billing" value={inr(leak)} sub="billed vs sub-metered energy" />
            </KpiRow>
            <Card head={<>Bill reconciliation <span className="text-secondary small fw-normal">· utility bill vs. metered energy</span></>}>
              {R.length ? (
                <Table
                  cols={[{ h: 'Bill' }, { h: 'Billed kWh', r: 1 }, { h: 'Metered kWh', r: 1 }, { h: 'Variance', r: 1 }, { h: 'Cost impact', r: 1 }, { h: 'Result' }, { h: 'Note', wrap: 1 }]}
                  rows={R.map(r => {
                    const [label, kind] = REC_STATUS[r.reconciliation_status] || [r.reconciliation_status, 'neutral'];
                    return [<b>{r.bill_number}</b>, nf(r.billed_kwh), nf(r.metered_kwh), `${nf(r.discrepancy_percentage, 2)}%`, inr(r.variance_cost_inr), <Pill kind={kind}>{label}</Pill>, r.notes];
                  })} />
              ) : <Empty>No reconciliations yet.</Empty>}
            </Card>
            <Card head="Utility bills">
              {B.length ? (
                <Table
                  cols={[{ h: 'Bill' }, { h: 'Cycle' }, { h: 'Due' }, { h: 'kWh', r: 1 }, { h: 'Max kVA', r: 1 }, { h: 'Amount', r: 1 }, { h: '₹/kWh', r: 1 }, { h: 'Status' }]}
                  rows={B.map(b => [
                    <><b>{b.bill_number}</b><div className="text-secondary small">{b.tariff_name}</div></>,
                    `${dOnly(b.billing_cycle_start)} – ${dOnly(b.billing_cycle_end)}`, dOnly(b.due_date),
                    nf(b.billed_kwh), nf(b.billed_max_demand_kva), inr(b.billed_amount_inr), nf(b.effective_cost_per_kwh_inr, 2),
                    <Pill kind={b.payment_status === 'paid' ? 'good' : b.payment_status === 'disputed' ? 'bad' : 'warn'}>{title(b.payment_status)}</Pill>,
                  ])} />
              ) : <Empty>No bills recorded for this facility.</Empty>}
            </Card>
          </div>
        );
      }}
    </Loader>
  );
}
