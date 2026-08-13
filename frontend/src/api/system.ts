import { request } from './http'
import type { RuntimeInstance } from '@/types/instance'

export interface GpuInfo {
  index: number
  name: string
  memory_total_mb: number
  memory_used_mb: number
  utilization_percent: number
}

export interface AuditEvent {
  timestamp: string
  actor: string
  method: string
  path: string
  status_code: number
  request_id: string
}

export const systemApi = {
  gpus: () => request<GpuInfo[]>('/system/gpus'),
  instances: () => request<RuntimeInstance[]>('/instances'),
  logs: (instanceId: string) => request<string[]>(`/instances/${instanceId}/logs`),
  auditLogs: () => request<AuditEvent[]>('/system/audit-logs'),
  health: () => request<Record<string, unknown>>('/system/health'),
}
