import { createContext, useCallback, useContext, useRef, useState } from 'react';
import {
  Badge, Button, ButtonGroup, Card as BCard, Col, Modal as BModal, Placeholder, Row, Spinner, Table as BTable, Toast, ToastContainer,
} from 'react-bootstrap';
import { title } from '../format.js';

/* ---------- toast ---------- */
const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [t, setT] = useState({ msg: '', err: false, show: false });
  const seq = useRef(0);
  const toast = useCallback((msg, err = false) => {
    seq.current += 1;
    setT({ msg, err, show: true, key: seq.current });
  }, []);
  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <ToastContainer position="bottom-center" className="p-3" style={{ zIndex: 2100, position: 'fixed' }}>
        <Toast key={t.key} show={t.show} onClose={() => setT(x => ({ ...x, show: false }))} autohide delay={3200}
          bg={t.err ? 'danger' : 'dark'} role="status" aria-live="polite">
          <Toast.Body className="text-white d-flex justify-content-between align-items-center gap-3">
            <span>{t.msg}</span>
            <button type="button" className="btn-close btn-close-white" aria-label="Close" onClick={() => setT(x => ({ ...x, show: false }))} />
          </Toast.Body>
        </Toast>
      </ToastContainer>
    </ToastCtx.Provider>
  );
}

/* ---------- layout atoms ---------- */
export const Card = ({ head, className = '', children, bodyClassName = '' }) => (
  <BCard className={`h-100 ${className}`}>
    {head ? <BCard.Header className="bg-transparent py-3"><div className="card-head d-flex flex-wrap align-items-center gap-2 w-100">{head}</div></BCard.Header> : null}
    <BCard.Body className={bodyClassName}>{children}</BCard.Body>
  </BCard>
);

/** Responsive row of KPI tiles: 1 per row on phones, 2 on tablets, 4 on desktops. */
export const KpiRow = ({ children }) => <Row xs={1} sm={2} xl={4} className="g-3">{children}</Row>;

export const Kpi = ({ label, value, unit, sub, children }) => (
  <Col>
    <BCard className="kpi h-100">
      <BCard.Body>
        <div className="label">{label}</div>
        <div className="value num">{value}{unit ? <small>{unit}</small> : null}</div>
        <div className="sub">{sub}</div>
        {children}
      </BCard.Body>
    </BCard>
  </Col>
);

const PILL = {
  good: ['success-subtle', 'success-emphasis'],
  warn: ['warning-subtle', 'warning-emphasis'],
  bad: ['danger-subtle', 'danger-emphasis'],
  info: ['info-subtle', 'info-emphasis'],
  neutral: ['secondary-subtle', 'secondary-emphasis'],
};
export const Pill = ({ kind = 'neutral', children }) => {
  const [bg, text] = PILL[kind] || PILL.neutral;
  return <Badge pill bg={bg} text={text} className="fw-semibold">{children}</Badge>;
};
export const sevKind = s => ({ critical: 'bad', high: 'bad', medium: 'warn', low: 'info' }[s] || 'neutral');

export const Empty = ({ children }) => <div className="text-center text-secondary py-4 px-2">{children}</div>;

export const Meter = ({ pct, cls = '', color }) => (
  <div className="progress mt-2" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
    <div className={`progress-bar ${cls}`} style={{ width: `${pct}%`, ...(color ? { background: color } : {}) }} />
  </div>
);

export const Swatch = ({ color }) => (
  <i style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 3, background: color, marginRight: 8 }} />
);

export function Stars({ n }) {
  return (
    <span className="stars" aria-label={`${n} of 5 stars`}>
      {'★'.repeat(n)}<span className="off">{'★'.repeat(5 - n)}</span>
    </span>
  );
}

/** cols: [{h, r?, wrap?}], rows: ReactNode[][] */
export function Table({ cols, rows }) {
  if (!rows.length) return null;
  return (
    <BTable responsive hover size="sm" className="mb-0 align-middle">
      <thead><tr>{cols.map((c, i) => <th key={i} className={c.r ? 'r' : ''}>{c.h}</th>)}</tr></thead>
      <tbody>
        {rows.map((r, ri) => (
          <tr key={ri}>{r.map((c, i) => <td key={i} className={`${cols[i].r ? 'r num' : ''} ${cols[i].wrap ? 'wrap' : ''}`}>{c}</td>)}</tr>
        ))}
      </tbody>
    </BTable>
  );
}

export function Seg({ options, value, onChange }) {
  return (
    <ButtonGroup size="sm" aria-label="Filter">
      {options.map(o => {
        const [v, label] = Array.isArray(o) ? o : [o, title(o)];
        return (
          <Button key={v} className="btn-seg" variant={v === value ? 'primary' : 'outline-secondary'} onClick={() => onChange(v)}>{label}</Button>
        );
      })}
    </ButtonGroup>
  );
}

export function Skeleton() {
  return (
    <>
      <Row xs={1} sm={2} xl={4} className="g-3 mb-3">
        {[0, 1, 2, 3].map(i => (
          <Col key={i}><BCard><BCard.Body><Placeholder as="div" animation="glow"><Placeholder xs={6} /><Placeholder xs={10} size="lg" /><Placeholder xs={8} /></Placeholder></BCard.Body></BCard></Col>
        ))}
      </Row>
      <BCard><BCard.Body style={{ height: 260 }} className="d-flex align-items-center justify-content-center"><Spinner animation="border" variant="primary" /></BCard.Body></BCard>
    </>
  );
}

/** Renders children(data) once loaded; skeleton / error card otherwise. */
export function Loader({ res, children }) {
  if (res.error && !res.data) {
    return (
      <BCard>
        <BCard.Body className="text-center text-secondary">
          Could not load this page.<br /><span className="small">{res.error.message}</span><br /><br />
          <Button variant="outline-secondary" onClick={res.reload}>Retry</Button>
        </BCard.Body>
      </BCard>
    );
  }
  if (!res.data) return <Skeleton />;
  return children(res.data);
}

/* ---------- forms ---------- */
export const Field = ({ label, children, className = 'mb-3' }) => (
  <div className={className}>
    <label className="form-label small text-secondary mb-1">{label}</label>
    {children}
  </div>
);

/* ---------- modal ---------- */
export function Modal({ onClose, children, size }) {
  return (
    <BModal show onHide={onClose} centered size={size} backdrop="static" keyboard>
      <BModal.Body className="p-4">{children}</BModal.Body>
    </BModal>
  );
}

export function PromptDialog({ heading, label, required, onSubmit, onCancel }) {
  const [text, setText] = useState('');
  return (
    <Modal onClose={onCancel}>
      <form onSubmit={e => { e.preventDefault(); onSubmit(text.trim()); }}>
        <h2 className="h5 mb-3">{heading}</h2>
        <Field label={label}>
          <textarea className="form-control" rows={3} required={required} value={text} onChange={e => setText(e.target.value)} autoFocus />
        </Field>
        <div className="d-flex justify-content-end gap-2">
          <Button type="button" variant="outline-secondary" onClick={onCancel}>Cancel</Button>
          <Button type="submit" variant="primary">Confirm</Button>
        </div>
      </form>
    </Modal>
  );
}
