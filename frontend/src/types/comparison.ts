import type { InferenceTask } from './task'

export interface AlgorithmComparison {
  id: string
  asset_id: string
  tasks: InferenceTask[]
  created_at: string
}

export interface CreateComparisonPayload {
  asset_id: string
  algorithm_version_ids: string[]
  parameters: Record<string, Record<string, unknown>>
}
