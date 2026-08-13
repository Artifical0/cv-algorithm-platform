export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = 'HTTP_ERROR',
  ) {
    super(message)
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const tokenKey = 'cv-platform-token'
const projectKey = 'cv-platform-project-id'

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      ...(init?.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
      ...(localStorage.getItem(projectKey) ? { 'X-Project-ID': localStorage.getItem(projectKey)! } : {}),
    },
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { code?: string; message?: string }
      | null
    if (response.status === 401 && !path.startsWith('/auth/')) {
      localStorage.removeItem(tokenKey)
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    throw new ApiError(payload?.message ?? '请求失败，请稍后重试', response.status, payload?.code)
  }

  if (response.status === 204) return undefined as T

  return (await response.json()) as T
}

export async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: 'same-origin',
    headers: {
      Accept: 'application/octet-stream, application/zip',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
      ...(localStorage.getItem(projectKey) ? { 'X-Project-ID': localStorage.getItem(projectKey)! } : {}),
    },
  })
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { code?: string; message?: string } | null
    if (response.status === 401) {
      localStorage.removeItem(tokenKey)
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    throw new ApiError(payload?.message ?? '文件下载失败', response.status, payload?.code)
  }
  return response.blob()
}

export function apiUrl(path: string): string {
  return `${apiBaseUrl}${path}`
}

export const apiBase = apiBaseUrl

export const sessionToken = {
  get: () => localStorage.getItem(tokenKey),
  set: () => localStorage.setItem(tokenKey, 'cookie-session'),
  clear: () => localStorage.removeItem(tokenKey),
}

export const projectContext = {
  get: () => localStorage.getItem(projectKey),
  set: (id: string) => localStorage.setItem(projectKey, id),
  clear: () => localStorage.removeItem(projectKey),
}
