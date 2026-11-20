import { useCallback, useEffect, useRef, useState } from 'react';

/** Run an async loader whenever deps change; ignores out-of-date responses. */
export function useAsync(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let live = true;
    setState(s => ({ ...s, error: null, loading: true }));
    fn().then(
      data => live && setState({ data, error: null, loading: false }),
      error => live && setState(s => ({ data: s.data, error, loading: false })),
    );
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  const reload = useCallback(() => setTick(t => t + 1), []);
  return { ...state, reload };
}

/** Minimal hash router: "#/alerts" -> "alerts". */
export function useHashRoute() {
  const read = () => (window.location.hash.replace(/^#\/?/, '') || 'overview').split('?')[0];
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const on = () => setRoute(read());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}

/**
 * App-wide live refresh. Bumps `tick` every `ms` while the tab is visible, and again when a
 * hidden tab becomes visible after being idle. Pages add `tick` to their data dependencies.
 */
export function useLiveTick(ms = 30000) {
  const [tick, setTick] = useState(0);
  const [at, setAt] = useState(() => new Date());
  const last = useRef(Date.now());
  const refresh = useCallback(() => {
    last.current = Date.now();
    setAt(new Date());
    setTick(t => t + 1);
  }, []);
  useEffect(() => {
    const id = setInterval(() => { if (document.visibilityState === 'visible') refresh(); }, ms);
    const onVisible = () => { if (document.visibilityState === 'visible' && Date.now() - last.current > ms) refresh(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => { clearInterval(id); document.removeEventListener('visibilitychange', onVisible); };
  }, [ms, refresh]);
  return { tick, at, refresh };
}
