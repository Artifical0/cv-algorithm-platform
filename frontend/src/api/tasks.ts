import { apiBase, projectContext, request, requestBlob } from './http'
import type { CreateTaskPayload, InferenceTask, TaskResultResponse } from '@/types/task'

export const tasksApi = {
  list: () => request<InferenceTask[]>('/tasks'),
  get: (id: string) => request<InferenceTask>(`/tasks/${id}`),
  result: (id: string) => request<TaskResultResponse>(`/tasks/${id}/result`),
  create: (payload: CreateTaskPayload) =>
    request<InferenceTask>('/tasks', { method: 'POST', body: JSON.stringify(payload) }),
  cancel: (id: string) => request<InferenceTask>(`/tasks/${id}/cancel`, { method: 'POST' }),
  retry: (id: string) => request<InferenceTask>(`/tasks/${id}/retry`, { method: 'POST' }),
  archive: (taskIds: string[]) => requestBlob('/tasks/results/archive', {
    method: 'POST', body: JSON.stringify({ task_ids: taskIds }),
  }),
  subscribe: (
    id: string,
    onUpdate: (event: { status: InferenceTask['status'] }) => void,
  ) => {
    const projectId = projectContext.get()
    const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
    const source = new EventSource(`${apiBase}/task-events/${id}${query}`, { withCredentials: true })
    source.addEventListener('task', (event: MessageEvent<string>) => onUpdate(JSON.parse(event.data)))
    return source
  },
}
