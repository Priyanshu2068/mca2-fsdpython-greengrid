import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { title } from '../format.js';

/* ---------- toast ---------- */
const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [t, setT] = useState({ msg: '', err: false, show: false });
  const timer = useRef();
  const toast = useCallback((msg, err = false) => {
    setT({ msg, err, show: true });
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setT(x => ({ ...x, show: false })), 3200);
  }, []);
  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className={`toast${t.err ? ' err' : ''}${t.show ? ' show' : ''}`} role="status" aria-live="polite">{t.msg}</div>
    </ToastCtx.Provider>
  );
}

/* ---------- atoms ---------- */
export const Card = ({ head, className = '', children }) => (
  <section className={`card ${className}`}>
    {head ? <div className="card-head"><h2>{head}</h2></div> : null}
    {children}
  </section>
);

export const Kpi = ({ label, value, unit, sub, children }) => (
  <div className="card kpi">
    <div className="label">{label}</div>
    <div className="value num">{value}{unit ? <small>{unit}</small> : null}</div>
    <div className="sub">{sub}</div>
    {children}
  </div>
);

export const Pill = ({ kind = 'neutral', children }) => <span className={`pill ${kind}`}>{children}</span>;
export const sevKind = s => ({ critical: 'bad', high: 'bad', medium: 'warn', low: 'info' }[s] || 'neutral');
export const Empty = ({ children }) => <div className="empty">{children}</div>;
export const Meter = ({ pct, cls = '', color }) => (
  <div className={`meter-bar ${cls}`}><i style={{ width: `${pct}%`, ...(color ? { background: color } : {}) }} /></div>
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
    <div className="table-wrap">
      <table>
        <thead><tr>{cols.map((c, i) => <th key={i} className={c.r ? 'r' : ''}>{c.h}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri}>{r.map((c, i) => <td key={i} className={`${cols[i].r ? 'r num' : ''} ${cols[i].wrap ? 'wrap' : ''}`}>{c}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Seg({ options, value, onChange }) {
  return (
    <div className="seg">
      {options.map(o => {
        const [v, label] = Array.isArray(o) ? o : [o, title(o)];
        return <button key={v} className={v === value ? 'on' : ''} onClick={() => onChange(v)}>{label}</button>;
      })}
    </div>
  );
}

export function Skeleton() {
  return (
    <>
      <div className="grid kpis"><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /></div>
      <div className="skeleton" style={{ height: 280 }} />
    </>
  );
}

/** Renders children(data) once loaded; skeleton / error card otherwise. */
export function Loader({ res, children }) {
  if (res.error && !res.data) {
    return (
      <div className="card empty">
        Could not load this page.<br /><span className="small">{res.error.message}</span><br /><br />
        <button className="btn" onClick={res.reload}>Retry</button>
      </div>
    );
  }
  if (!res.data) return <Skeleton />;
  return children(res.data);
}

/* ---------- modal (native <dialog>) ---------- */
export function Modal({ onClose, children }) {
  const ref = useRef();
  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
  }, []);
  return (
    <dialog ref={ref} onCancel={e => { e.preventDefault(); onClose(); }}>
      {children}
    </dialog>
  );
}

export function PromptDialog({ heading, label, required, onSubmit, onCancel }) {
  const [text, setText] = useState('');
  return (
    <Modal onClose={onCancel}>
      <form onSubmit={e => { e.preventDefault(); onSubmit(text.trim()); }}>
        <h2>{heading}</h2>
        <label>{label}<textarea rows={3} required={required} value={text} onChange={e => setText(e.target.value)} autoFocus /></label>
        <div className="actions">
          <button type="button" className="btn" onClick={onCancel}>Cancel</button>
          <button className="btn primary" type="submit">Confirm</button>
        </div>
      </form>
    </Modal>
  );
}
