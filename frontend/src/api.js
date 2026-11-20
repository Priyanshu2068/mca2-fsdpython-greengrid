// Same-origin session auth against the Django REST API (cookies + CSRF header).
let onUnauthorized = () => {};
export const setUnauthorizedHandler = fn => { onUnauthorized = fn; };

const cookie = n => (document.cookie.match('(?:^|; )' + n + '=([^;]*)') || [])[1] || '';

export async function ensureCsrf() {
  await fetch('/api/v1/accounts/csrf/', { credentials: 'same-origin' });
}

export async function api(path, { method = 'GET', body, isFormData } = {}) {
  const headers = { 'X-CSRFToken': decodeURIComponent(cookie('csrftoken')) };
  if (!isFormData) headers['Content-Type'] = 'application/json';
  const res = await fetch('/api/v1/' + path, {
    method,
    credentials: 'same-origin',
    headers,
    body: isFormData ? body : (body ? JSON.stringify(body) : undefined),
  });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    const msg = (data && data.error && data.error.message) || '';
    const authFail = res.status === 401 || (res.status === 403 && /authentication|credentials|not authenticated/i.test(msg));
    if (authFail && path !== 'accounts/login/' && path !== 'accounts/me/') onUnauthorized();
    const err = new Error(msg || (data && data.error && JSON.stringify(data.error.details)) || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const qs = o => Object.entries(o)
  .filter(([, v]) => v !== undefined && v !== '' && v !== null)
  .map(([k, v]) => k + '=' + encodeURIComponent(v))
  .join('&');
