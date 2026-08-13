export interface ImageAsset {
  id: string
  original_name: string
  sha256: string
  media_type: string
  width: number
  height: number
  size_bytes: number
  created_at: string
  owner_id: string
  project_id: string
}

export interface BatchUploadResponse {
  assets: ImageAsset[]
}
