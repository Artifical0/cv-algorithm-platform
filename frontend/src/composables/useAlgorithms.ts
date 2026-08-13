import { computed, onMounted, ref } from 'vue'

import { algorithmsApi } from '@/api/algorithms'
import type { Algorithm } from '@/types/algorithm'

export function useAlgorithms() {
  const algorithms = ref<Algorithm[]>([])
  const loading = ref(false)
  const error = ref('')

  const availableAlgorithms = computed(() =>
    algorithms.value.filter((algorithm) => algorithm.status === 'available'),
  )

  async function refresh() {
    loading.value = true
    error.value = ''
    try {
      algorithms.value = await algorithmsApi.list()
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '加载算法失败'
    } finally {
      loading.value = false
    }
  }

  onMounted(refresh)

  return { algorithms, availableAlgorithms, loading, error, refresh }
}

