import { request } from './http'
import type { Algorithm, BuildJob } from '@/types/algorithm'

export const algorithmsApi = {
  list: () => request<Algorithm[]>('/algorithms'),
  get: (id: string) => request<Algorithm>(`/algorithms/${id}`),
  importPackage: (file: File) => {
    const body = new FormData()
    body.append('package', file)
    return request<Algorithm>('/algorithms/import', { method: 'POST', body })
  },
  build: (id: string) => request<BuildJob>(`/algorithm-versions/${id}/build`, { method: 'POST' }),
  buildJob: (id: string) => request<BuildJob>(`/build-jobs/${id}`),
  enable: (id: string) => request<Algorithm>(`/algorithm-versions/${id}/enable`, { method: 'POST' }),
  disable: (id: string) => request<Algorithm>(`/algorithm-versions/${id}/disable`, { method: 'POST' }),
  rollback: (id: string) => request<Algorithm[]>(`/algorithm-versions/${id}/rollback`, { method: 'POST' }),
  remove: (id: string, removeImage = false) =>
    request<void>(`/algorithm-versions/${id}?remove_image=${removeImage}`, { method: 'DELETE' }),
}
