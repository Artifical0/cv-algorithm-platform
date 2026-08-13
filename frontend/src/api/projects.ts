import { request } from './http'

export interface Project {
  id: string; name: string; description: string; role: 'owner' | 'editor' | 'viewer'; created_at: string
}
export interface ProjectMember {
  user_id: string; username: string; role: 'owner' | 'editor' | 'viewer'; joined_at: string
}

export const projectsApi = {
  list: () => request<Project[]>('/projects'),
  create: (payload: { name: string; description: string }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(payload) }),
  members: (id: string) => request<ProjectMember[]>(`/projects/${id}/members`),
  addMember: (id: string, payload: { username: string; role: ProjectMember['role'] }) =>
    request<ProjectMember>(`/projects/${id}/members`, { method: 'POST', body: JSON.stringify(payload) }),
}
