import { apiUrl, projectContext, request, requestBlob } from './http'
import type { BatchUploadResponse, ImageAsset } from '@/types/asset'

export const assetsApi = {
  list: () => request<ImageAsset[]>('/assets'),
  get: (id: string) => request<ImageAsset>(`/assets/${id}`),
  contentUrl: (id: string) => {
    const projectId = projectContext.get()
    return apiUrl(`/assets/${id}/content${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''}`)
  },
  upload: (files: File[]) => {
    const body = new FormData()
    for (const file of files) body.append('files', file)
    return request<BatchUploadResponse>('/assets/upload', { method: 'POST', body })
  },
  download: (ids: string[]) => requestBlob('/assets/download', {
    method: 'POST', body: JSON.stringify(ids),
  }),
}
