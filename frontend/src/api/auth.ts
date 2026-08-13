import { projectContext, request, sessionToken } from './http'

export interface Session {
  user_id: string
  username: string
  role: string
  default_project_id: string | null
  expires_at: string
}
export interface User {
  id: string; username: string; role: 'admin' | 'developer' | 'user'; enabled: boolean; created_at: string
}

export const authApi = {
  login: async (username: string, password: string) => {
    const session = await request<Session>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    sessionToken.set()
    sessionRole.set(session.role)
    if (session.default_project_id) projectContext.set(session.default_project_id)
    return session
  },
  me: () => request<Session>('/auth/me'),
  users: () => request<User[]>('/users'),
  createUser: (payload: { username: string; password: string; role: User['role'] }) =>
    request<User>('/users', { method: 'POST', body: JSON.stringify(payload) }),
  updateUser: (id: string, payload: { role?: User['role']; enabled?: boolean }) =>
    request<User>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  logout: async () => {
    await request<void>('/auth/logout', { method: 'POST' })
    sessionToken.clear()
    sessionRole.clear()
    projectContext.clear()
  },
}

const sessionRoleKey = 'cv-platform-session-role'
export const sessionRole = {
  get: () => localStorage.getItem(sessionRoleKey),
  set: (role: string) => localStorage.setItem(sessionRoleKey, role),
  clear: () => localStorage.removeItem(sessionRoleKey),
}
