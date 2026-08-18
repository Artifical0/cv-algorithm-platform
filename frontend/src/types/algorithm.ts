export type AlgorithmStatus =
  | 'uploaded'
  | 'validating'
  | 'building'
  | 'testing'
  | 'available'
  | 'disabled'
  | 'failed'

type ParameterMetadata = {
  title?: string
  description?: string
}

export type NumberParameter = ParameterMetadata & {
  type: 'number'
  default: number
  minimum?: number
  maximum?: number
  step?: number
}

export type IntegerParameter = ParameterMetadata & {
  type: 'integer'
  default: number
  minimum?: number
  maximum?: number
  step?: number
}

export type BooleanParameter = ParameterMetadata & { type: 'boolean'; default: boolean }
export type StringParameter = ParameterMetadata & { type: 'string'; default: string; options?: string[] }
export type ParameterSpec = NumberParameter | IntegerParameter | BooleanParameter | StringParameter

export interface Algorithm {
  id: string
  key: string
  name: string
  version: string
  description: string
  task_type: 'object_detection' | 'classification' | 'segmentation' | 'ocr' | 'pose_estimation'
  device: 'cpu' | 'gpu' | 'auto'
  framework: string
  status: AlgorithmStatus
  image: string
  parameters: Record<string, ParameterSpec>
  created_at: string
  package_sha256: string | null
  image_digest: string | null
  created_by: string
  traffic_weight: number
  container_status: string
  last_called_at: string | null
  project_id: string
}

export interface BuildJob {
  id: string
  algorithm_version_id: string
  status: 'queued' | 'building' | 'testing' | 'completed' | 'failed'
  logs: string[]
  created_at: string
  updated_at: string
  image_digest: string | null
  error_message: string | null
}
