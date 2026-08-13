export type InstanceStatus = 'created' | 'starting' | 'healthy' | 'stopped' | 'failed'

export interface RuntimeInstance {
  id: string
  algorithm_version_id: string
  image: string
  container_name: string
  endpoint: string
  status: InstanceStatus
  device: 'cpu' | 'gpu' | 'auto'
  created_at: string
  updated_at: string
  error: string | null
  last_used_at: string | null
  node_id: string
  gpu_device_ids: string[]
}
