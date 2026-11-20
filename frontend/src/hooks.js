import { useCallback, useEffect, useState } from 'react';

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
