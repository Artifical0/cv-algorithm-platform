import { request } from './http'
import type { RuntimeInstance } from '@/types/instance'

export const instancesApi = {
  list: () => request<RuntimeInstance[]>('/instances'),
  startAlgorithm: (algorithmId: string) =>
    request<RuntimeInstance>(`/algorithms/${algorithmId}/start`, { method: 'POST' }),
  stop: (instanceId: string) =>
    request<RuntimeInstance>(`/instances/${instanceId}/stop`, { method: 'POST' }),
  remove: (instanceId: string) => request<void>(`/instances/${instanceId}`, { method: 'DELETE' }),
}
