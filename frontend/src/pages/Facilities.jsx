import { useRef, useState } from 'react';
import { api } from '../api.js';
import { useApp } from '../context.js';
import { useAsync } from '../hooks.js';
import { LOAD_NAMES, SOURCE_NAMES, list, nf, title } from '../format.js';
import { hasRole } from '../context.js';
import { Card, Empty, Loader, Modal, Pill, Table, useToast } from '../components/ui.jsx';

const SOURCES = [['grid', 'Utility Grid'], ['solar', 'Solar PV'], ['diesel_generator', 'Diesel Generator'], ['gas', 'Natural Gas'], ['water', 'Water']];
const LOADS = [['main_incomer', 'Main Incomer'], ['hvac', 'HVAC & Chillers'], ['lighting', 'Lighting Circuits'], ['it_infrastructure', 'IT & Server Room'], ['auxiliary_pumps', 'Auxiliary Pumps'], ['elevators', 'Elevators'], ['ev_chargers', 'EV Chargers']];
const BLANK = { name: '', meter_identifier: '', energy_source: 'grid', load_category: 'main_incomer', physical_location: '' };
const FACILITY_TYPES = [['commercial_office', 'Commercial Office'], ['tech_park', 'Technology Park'], ['hospital', 'Hospital & Healthcare'], ['retail_mall', 'Retail Mall'], ['hotel', 'Hospitality & Hotel'], ['educational_campus', 'Educational Campus']];
const FACILITY_BLANK = {
  name: '', code: '', facility_type: 'commercial_office', gross_floor_area_sqm: '', sanctioned_demand_kva: '',
  operating_hours_per_week: '50', address: '', city: '', state: '', pin_code: '',
};
const twoCols = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 };

/** Admin-only: adds a new facility (building / site) to the system. */
function FacilityDialog({ onClose, onCreated }) {
  const toast = useToast();
  const [f, setF] = useState(FACILITY_BLANK);
  const [saving, setSaving] = useState(false);
  const set = k => e => setF(s => ({ ...s, [k]: e.target.value }));
  const submit = async e => {
    e.preventDefault();
    setSaving(true);
    try {
      const body = { ...f, name: f.name.trim(), code: f.code.trim().toUpperCase(), address: f.address.trim(), city: f.city.trim(), state: f.state.trim(), pin_code: f.pin_code.trim() };
      const created = await api('facilities/', { method: 'POST', body });
      toast(`Added facility ${created.name}`);
      onCreated(created);
    } catch (err) { toast(err.message, true); setSaving(false); }
  };
  return (
    <Modal onClose={onClose}>
      <form onSubmit={submit} style={{ minWidth: 340 }}>
        <h2>Add facility</h2>
        <div style={twoCols}>
          <label>Facility name<input required placeholder="e.g. Pune Corporate Park" value={f.name} onChange={set('name')} autoFocus /></label>
          <label>Code<input required placeholder="e.g. PNQ-CP-01" value={f.code} onChange={set('code')} style={{ textTransform: 'uppercase' }} /></label>
        </div>
        <label>Type<select value={f.facility_type} onChange={set('facility_type')}>{FACILITY_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
        <div style={twoCols}>
          <label>Floor area (m²)<input type="number" required min="1" step="0.01" value={f.gross_floor_area_sqm} onChange={set('gross_floor_area_sqm')} /></label>
          <label>Sanctioned demand (kVA)<input type="number" required min="1" step="0.01" value={f.sanctioned_demand_kva} onChange={set('sanctioned_demand_kva')} /></label>
        </div>
        <label>Operating hours per week<input type="number" required min="1" max="168" step="0.5" value={f.operating_hours_per_week} onChange={set('operating_hours_per_week')} /></label>
        <label>Address<input required value={f.address} onChange={set('address')} /></label>
        <div style={twoCols}>
          <label>City<input required value={f.city} onChange={set('city')} /></label>
          <label>State<input required value={f.state} onChange={set('state')} /></label>
        </div>
        <label>PIN code<input required value={f.pin_code} onChange={set('pin_code')} /></label>
        <div className="hint">After adding it, register its meters and upload readings, then give users access from the Users page.</div>
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" type="submit" disabled={saving}>Add facility</button>
        </div>
      </form>
    </Modal>
  );
}

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
  const { facilities, user, refreshFacilities } = useApp();
  const toast = useToast();
  const fileRef = useRef();
  const [meterFor, setMeterFor] = useState(null);
  const [addingFacility, setAddingFacility] = useState(false);
  const isEng = hasRole(user, 'admin', 'field_engineer');
  const isAdmin = hasRole(user, 'admin');
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

  const addFacilityUi = (
    <>
      {isAdmin && (
        <div className="toolbar" style={{ justifyContent: 'flex-end' }}>
          <button className="btn primary" onClick={() => setAddingFacility(true)}>+ Add facility</button>
        </div>
      )}
      {addingFacility && (
        <FacilityDialog onClose={() => setAddingFacility(false)} onCreated={c => { setAddingFacility(false); refreshFacilities(c.id); }} />
      )}
    </>
  );

  if (!facilities.length) {
    return <>{addFacilityUi}<Card><Empty>No facilities yet.{isAdmin ? ' Use "+ Add facility" to create the first one.' : ''}</Empty></Card></>;
  }
  return (
    <Loader res={res}>
      {meters => (
        <>
          {addFacilityUi}
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
