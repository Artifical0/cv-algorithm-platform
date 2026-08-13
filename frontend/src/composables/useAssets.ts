import { onMounted, ref } from 'vue'

import { assetsApi } from '@/api/assets'
import type { ImageAsset } from '@/types/asset'

export function useAssets() {
  const assets = ref<ImageAsset[]>([])
  const loading = ref(false)
  const uploading = ref(false)
  const error = ref('')

  async function refresh() {
    loading.value = true
    error.value = ''
    try {
      assets.value = await assetsApi.list()
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '加载图片失败'
    } finally {
      loading.value = false
    }
  }

  async function upload(files: File[]) {
    uploading.value = true
    error.value = ''
    try {
      const response = await assetsApi.upload(files)
      const byId = new Map(assets.value.map((asset) => [asset.id, asset]))
      for (const asset of response.assets) byId.set(asset.id, asset)
      assets.value = [...byId.values()].sort((a, b) => b.created_at.localeCompare(a.created_at))
      return response.assets
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '上传图片失败'
      throw reason
    } finally {
      uploading.value = false
    }
  }

  onMounted(refresh)
  return { assets, loading, uploading, error, refresh, upload }
}
