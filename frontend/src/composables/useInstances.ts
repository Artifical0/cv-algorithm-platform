import { onMounted, ref } from 'vue'

import { instancesApi } from '@/api/instances'
import type { RuntimeInstance } from '@/types/instance'

export function useInstances() {
  const instances = ref<RuntimeInstance[]>([])
  const loading = ref(false)
  const pendingId = ref('')
  const error = ref('')

  async function refresh() {
    loading.value = true
    error.value = ''
    try {
      instances.value = await instancesApi.list()
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '加载实例失败'
    } finally {
      loading.value = false
    }
  }

  async function start(algorithmId: string) {
    pendingId.value = algorithmId
    error.value = ''
    try {
      const instance = await instancesApi.startAlgorithm(algorithmId)
      const index = instances.value.findIndex((item) => item.id === instance.id)
      if (index >= 0) instances.value[index] = instance
      else instances.value.unshift(instance)
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '启动实例失败'
    } finally {
      pendingId.value = ''
    }
  }

  async function stop(instanceId: string) {
    pendingId.value = instanceId
    try {
      const instance = await instancesApi.stop(instanceId)
      const index = instances.value.findIndex((item) => item.id === instance.id)
      if (index >= 0) instances.value[index] = instance
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '停止实例失败'
    } finally {
      pendingId.value = ''
    }
  }

  async function remove(instanceId: string) {
    pendingId.value = instanceId
    try {
      await instancesApi.remove(instanceId)
      instances.value = instances.value.filter((item) => item.id !== instanceId)
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '删除实例失败'
    } finally {
      pendingId.value = ''
    }
  }

  onMounted(refresh)
  return { instances, loading, pendingId, error, refresh, start, stop, remove }
}
