import { useRef, useState } from 'react';
import { api } from '../api.js';
import { useApp } from '../context.js';
import { useAsync } from '../hooks.js';
import { LOAD_NAMES, SOURCE_NAMES, list, nf, title } from '../format.js';
import { Card, Empty, Loader, Modal, Pill, Table, useToast } from '../components/ui.jsx';

const SOURCES = [['grid', 'Utility Grid'], ['solar', 'Solar PV'], ['diesel_generator', 'Diesel Generator'], ['gas', 'Natural Gas'], ['water', 'Water']];
const LOADS = [['main_incomer', 'Main Incomer'], ['hvac', 'HVAC & Chillers'], ['lighting', 'Lighting Circuits'], ['it_infrastructure', 'IT & Server Room'], ['auxiliary_pumps', 'Auxiliary Pumps'], ['elevators', 'Elevators'], ['ev_chargers', 'EV Chargers']];
const BLANK = { name: '', meter_identifier: '', energy_source: 'grid', load_category: 'main_incomer', physical_location: '' };

function MeterDialog({ facility, onClose, onDone }) {
  const toast = useToast();
  const [f, setF] = useState(BLANK);
  const [saving, setSaving] = useState(false);
  const set = k => e => setF(s => ({ ...s, [k]: e.target.value }));
  const submit = async e => {
    e.preventDefault();
    setSaving(true);
    const body = { ...f, name: f.name.trim(), meter_identifier: f.meter_identifier.trim(), physical_location: f.physical_location.trim() };
    try {
      await api(`facilities/${facility.id}/meters/`, { method: 'POST', body });
      toast(`Registered meter ${body.meter_identifier}`);
      onDone();
    } catch (err) { toast(err.message, true); setSaving(false); }
  };
  return (
    <Modal onClose={onClose}>
      <form onSubmit={submit}>
        <h2>Register Meter</h2>
        <div className="muted small">{facility.name}</div>
        <label>Meter Name<input required placeholder="e.g. Substation Feeder 2" value={f.name} onChange={set('name')} /></label>
        <label>Meter Identifier<input required placeholder="e.g. MTR-FEEDER-02" value={f.meter_identifier} onChange={set('meter_identifier')} /></label>
        <label>Energy Source<select value={f.energy_source} onChange={set('energy_source')}>{SOURCES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
        <label>Load Category<select value={f.load_category} onChange={set('load_category')}>{LOADS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
        <label>Physical Location<input placeholder="e.g. Electrical Room B1" value={f.physical_location} onChange={set('physical_location')} /></label>
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" type="submit" disabled={saving}>Register</button>
        </div>
      </form>
    </Modal>
  );
}

export default function Facilities() {
  const { facilities, user } = useApp();
  const toast = useToast();
  const fileRef = useRef();
  const [meterFor, setMeterFor] = useState(null);
  const isEng = user && (user.role === 'admin' || user.role === 'field_engineer' || user.is_superuser);
  const res = useAsync(
    () => Promise.all(facilities.map(f => api(`facilities/${f.id}/meters/`).then(list).catch(() => []))),
    [facilities],
  );

  const upload = async e => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      toast('Uploading CSV telemetry batch...');
      const r = await api('ingestion/readings/upload-csv/', { method: 'POST', body: fd, isFormData: true });
      toast(`CSV accepted: ${r.accepted || r.ingested || 0} readings processed.`);
      res.reload();
    } catch (err) { toast(err.message || 'Upload failed', true); }
  };

  if (!facilities.length) return <Card><Empty>No facilities.</Empty></Card>;
  return (
    <Loader res={res}>
      {meters => (
        <>
          <input ref={fileRef} type="file" accept=".csv" hidden onChange={upload} />
          {facilities.map((f, i) => (
            <Card key={f.id} head={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                <div>{f.name} <span className="muted small">· {f.code}</span></div>
                {isEng && (
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn small primary" onClick={() => setMeterFor(f)}>+ Register Meter</button>
                    <button className="btn small ghost" onClick={() => fileRef.current.click()}>Upload CSV</button>
                  </div>
                )}
              </div>
            }>
              <div className="grid kpis" style={{ marginBottom: 14 }}>
                <div><div className="muted small">Type</div><b>{title(f.facility_type)}</b></div>
                <div><div className="muted small">Location</div><b>{f.city}, {f.state}</b></div>
                <div><div className="muted small">Floor area</div><b className="num">{nf(f.gross_floor_area_sqm)} m²</b></div>
                <div><div className="muted small">Sanctioned demand</div><b className="num">{nf(f.sanctioned_demand_kva)} kVA</b></div>
              </div>
              <Table
                cols={[{ h: 'Meter' }, { h: 'ID' }, { h: 'Source' }, { h: 'Load' }, { h: 'Location' }, { h: 'Active' }]}
                rows={(meters[i] || []).map(m => [
                  <b>{m.name}</b>, <code>{m.meter_identifier}</code>, SOURCE_NAMES[m.energy_source] || m.energy_source,
                  LOAD_NAMES[m.load_category] || m.load_category, m.physical_location,
                  m.is_active ? <Pill kind="good">Yes</Pill> : <Pill kind="neutral">No</Pill>,
                ])} />
            </Card>
          ))}
          {meterFor && <MeterDialog facility={meterFor} onClose={() => setMeterFor(null)} onDone={() => { setMeterFor(null); res.reload(); }} />}
        </>
      )}
    </Loader>
  );
}
