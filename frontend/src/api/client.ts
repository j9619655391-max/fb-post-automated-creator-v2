const API_BASE = import.meta.env.VITE_API_BASE ?? '';
const TOKEN_KEY = 'content_platform_token';

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') search.set(k, String(v));
  });
  const s = search.toString();
  return s ? `?${s}` : '';
}

export function apiUrl(path: string, params: Record<string, string | number | undefined> = {}): string {
  const prefix = path.startsWith('/') ? '' : '/';
  return `${API_BASE}/api/v1${prefix}${path}${qs(params)}`;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { params?: Record<string, string | number | undefined>; timeoutMs?: number } = {}
): Promise<T> {
  const { params = {}, timeoutMs, ...init } = options;
  const url = apiUrl(path, params);

  const token = localStorage.getItem(TOKEN_KEY);
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string>),
  };

  // Only set application/json if not FormData (browser sets boundary for FormData)
  if (!(init.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;
  const requestInit: RequestInit = { ...init, headers };
  if (timeoutMs !== undefined) {
    controller = new AbortController();
    requestInit.signal = controller.signal;
    timeoutId = setTimeout(() => controller?.abort(), timeoutMs);
  }

  let res: Response;
  try {
    res = await fetch(url, requestInit);
  } finally {
    if (timeoutId !== undefined) clearTimeout(timeoutId);
  }

  // Only an unauthenticated response means the stored token is invalid or expired.
  // A 403 is an authorization/role failure; keep the session intact so users do not
  // appear to be logged out when they open an admin-only route.
  if (res.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('content_platform_user');
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(Array.isArray(err.detail) ? JSON.stringify(err.detail) : err.detail ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function apiGet<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  return apiFetch<T>(path, { method: 'GET', params });
}

export function apiPost<T>(
  path: string,
  body?: object | FormData,
  params?: Record<string, string | number | undefined>
): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    params,
    body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined)
  });
}

export function apiPut<T>(path: string, body: object, params?: Record<string, string | number | undefined>): Promise<T> {
  return apiFetch<T>(path, { method: 'PUT', params, body: JSON.stringify(body) });
}

export function apiPatch<T>(path: string, body: object, params?: Record<string, string | number | undefined>): Promise<T> {

  return apiFetch<T>(path, { method: 'PATCH', params, body: JSON.stringify(body) });
}

export function apiDelete(path: string, params?: Record<string, string | number | undefined>): Promise<void> {
  return apiFetch(path, { method: 'DELETE', params });
}
