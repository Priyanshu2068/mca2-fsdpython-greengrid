import { api, qs } from '../api.js';
import { useApp } from '../context.js';
import { useAsync } from '../hooks.js';
import { dOnly, inr, list, nf, num, title } from '../format.js';
import { Card, Empty, Kpi, Loader, Pill, Table } from '../components/ui.jsx';

const REC_STATUS = {
  verified_within_tolerance: ['Verified', 'good'],
  variance_minor: ['Minor variance', 'warn'],
  variance_action_required: ['Action required', 'bad'],
};

export default function Billing() {
  const { fid, facility } = useApp();
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
          <>
            <div className="grid kpis">
              <Kpi label="Bills on record" value={B.length} sub={facility.name} />
              <Kpi label="Total billed" value={inr(totalBilled)} sub="across all cycles" />
              <Kpi label="Flagged for audit" value={flagged.length} sub={flagged.length ? 'variance above 2.5%' : 'No disputes needed'} />
              <Kpi label="Potential over-billing" value={inr(leak)} sub="billed vs sub-metered energy" />
            </div>
            <Card head={<>Bill reconciliation <span className="muted small">· utility bill vs. metered energy</span></>}>
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
                    <><b>{b.bill_number}</b><div className="muted small">{b.tariff_name}</div></>,
                    `${dOnly(b.billing_cycle_start)} – ${dOnly(b.billing_cycle_end)}`, dOnly(b.due_date),
                    nf(b.billed_kwh), nf(b.billed_max_demand_kva), inr(b.billed_amount_inr), nf(b.effective_cost_per_kwh_inr, 2),
                    <Pill kind={b.payment_status === 'paid' ? 'good' : b.payment_status === 'disputed' ? 'bad' : 'warn'}>{title(b.payment_status)}</Pill>,
                  ])} />
              ) : <Empty>No bills recorded for this facility.</Empty>}
            </Card>
          </>
        );
      }}
    </Loader>
  );
}
