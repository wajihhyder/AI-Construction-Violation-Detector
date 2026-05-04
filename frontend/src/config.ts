/** API origin without trailing slash. Empty = relative URLs (Vite dev/proxy or SPA served from API). */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

/** Absolute URL for an API path (e.g. `/api/foo` → `http://localhost:8000/api/foo` when configured). */
export function apiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return API_BASE_URL ? `${API_BASE_URL}${p}` : p
}
