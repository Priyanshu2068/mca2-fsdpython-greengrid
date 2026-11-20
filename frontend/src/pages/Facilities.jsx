import { useRef, useState } from 'react';
import { Button, Col, Form, Row } from 'react-bootstrap';
import { api } from '../api.js';
import { useApp, hasRole } from '../context.js';
import { useAsync } from '../hooks.js';
import { LOAD_NAMES, SOURCE_NAMES, list, nf, title } from '../format.js';
import { Card, Empty, Field, Loader, Modal, Pill, Table, useToast } from '../components/ui.jsx';

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
        <h2 className="h5 mb-1">Register Meter</h2>
        <div className="text-secondary small mb-3">{facility.name}</div>
        <Field label="Meter Name"><Form.Control required placeholder="e.g. Substation Feeder 2" value={f.name} onChange={set('name')} /></Field>
        <Field label="Meter Identifier"><Form.Control required placeholder="e.g. MTR-FEEDER-02" value={f.meter_identifier} onChange={set('meter_identifier')} /></Field>
        <Row className="g-3">
          <Col sm={6}><Field label="Energy Source"><Form.Select value={f.energy_source} onChange={set('energy_source')}>{SOURCES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</Form.Select></Field></Col>
          <Col sm={6}><Field label="Load Category"><Form.Select value={f.load_category} onChange={set('load_category')}>{LOADS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</Form.Select></Field></Col>
        </Row>
        <Field label="Physical Location"><Form.Control placeholder="e.g. Electrical Room B1" value={f.physical_location} onChange={set('physical_location')} /></Field>
        <div className="d-flex justify-content-end gap-2">
          <Button type="button" variant="outline-secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={saving}>{saving ? 'Registering…' : 'Register'}</Button>
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
  const isEng = hasRole(user, 'admin', 'field_engineer');
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
        <div className="d-grid gap-3">
          <input ref={fileRef} type="file" accept=".csv" hidden onChange={upload} />
          {facilities.map((f, i) => (
            <Card key={f.id} head={
              <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 w-100">
                <span>{f.name} <span className="text-secondary small fw-normal">· {f.code}</span></span>
                {isEng && (
                  <span className="d-flex gap-2">
                    <Button size="sm" variant="primary" onClick={() => setMeterFor(f)}>+ Register Meter</Button>
                    <Button size="sm" variant="outline-secondary" onClick={() => fileRef.current.click()}>Upload CSV</Button>
                  </span>
                )}
              </div>
            }>
              <Row xs={2} md={4} className="g-3 mb-3">
                <Col><div className="text-secondary small">Type</div><b>{title(f.facility_type)}</b></Col>
                <Col><div className="text-secondary small">Location</div><b>{f.city}, {f.state}</b></Col>
                <Col><div className="text-secondary small">Floor area</div><b className="num">{nf(f.gross_floor_area_sqm)} m²</b></Col>
                <Col><div className="text-secondary small">Sanctioned demand</div><b className="num">{nf(f.sanctioned_demand_kva)} kVA</b></Col>
              </Row>
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
        </div>
      )}
    </Loader>
  );
}
