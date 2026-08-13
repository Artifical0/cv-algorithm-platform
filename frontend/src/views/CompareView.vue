<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { assetsApi } from '@/api/assets'
import { comparisonsApi } from '@/api/comparisons'
import { tasksApi } from '@/api/tasks'
import DetectionCanvas from '@/components/results/DetectionCanvas.vue'
import { useAlgorithms } from '@/composables/useAlgorithms'
import { useAssets } from '@/composables/useAssets'
import type { AlgorithmComparison } from '@/types/comparison'
import type { ObjectDetectionResult } from '@/types/task'

const route = useRoute()
const router = useRouter()
const { algorithms } = useAlgorithms()
const { assets } = useAssets()
const selectedAssetId = ref('')
const selectedAlgorithms = ref<string[]>([])
const comparison = ref<AlgorithmComparison | null>(null)
const results = ref<Record<string, ObjectDetectionResult>>({})
const confidence = ref(0)
const overlay = ref(false)
const error = ref('')
const comparisonId = computed(() => String(route.params.id ?? ''))
const selectedAsset = computed(() => assets.value.find((item) => item.id === selectedAssetId.value))

async function createComparison() {
  if (!selectedAssetId.value || selectedAlgorithms.value.length < 2) return
  try {
    const parameters = Object.fromEntries(
      selectedAlgorithms.value.map((id) => [id, { confidence: 0.5 }]),
    )
    const created = await comparisonsApi.create({
      asset_id: selectedAssetId.value,
      algorithm_version_ids: selectedAlgorithms.value,
      parameters,
    })
    await router.push(`/compare/${created.id}`)
    comparison.value = created
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '创建对比失败'
  }
}

async function loadComparison() {
  if (!comparisonId.value) return
  comparison.value = await comparisonsApi.get(comparisonId.value)
  selectedAssetId.value = comparison.value.asset_id
  for (const task of comparison.value.tasks) {
    if (task.status === 'completed' && !results.value[task.id]) {
      const taskResult = (await tasksApi.result(task.id)).result
      if (taskResult.type === 'object_detection') results.value[task.id] = taskResult
    }
  }
}

function algorithmName(id: string) {
  return algorithms.value.find((item) => item.id === id)?.name ?? '未知算法'
}

function toggleAlgorithm(id: string) {
  selectedAlgorithms.value = selectedAlgorithms.value.includes(id)
    ? selectedAlgorithms.value.filter((item) => item !== id)
    : [...selectedAlgorithms.value, id]
}

onMounted(() => void loadComparison())
const polling = window.setInterval(() => {
  if (comparison.value?.tasks.some((task) => !['completed', 'failed', 'cancelled'].includes(task.status))) {
    void loadComparison()
  }
}, 1500)
onUnmounted(() => window.clearInterval(polling))
</script>

<template>
  <header class="page-heading">
    <span class="eyebrow">MULTI-ALGORITHM BENCH</span>
    <h1>结果对比</h1>
    <p>同一张原图并行调用多个兼容算法，并排显示版本、参数、耗时和标准检测结果。</p>
  </header>
  <p v-if="error" class="alert">{{ error }}</p>

  <section v-if="!comparisonId" class="comparison-builder">
    <label>选择图片
      <select v-model="selectedAssetId">
        <option value="" disabled>请选择已上传图片</option>
        <option v-for="asset in assets" :key="asset.id" :value="asset.id">{{ asset.original_name }}</option>
      </select>
    </label>
    <div class="comparison-options">
      <button
        v-for="algorithm in algorithms"
        :key="algorithm.id"
        :class="{ selected: selectedAlgorithms.includes(algorithm.id) }"
        @click="toggleAlgorithm(algorithm.id)"
      >{{ algorithm.name }}<small>v{{ algorithm.version }}</small></button>
    </div>
    <button
      class="primary-button"
      :disabled="!selectedAssetId || selectedAlgorithms.length < 2"
      @click="createComparison"
    >创建并行对比</button>
  </section>

  <template v-else-if="comparison">
    <section class="result-controls">
      <label>统一置信度过滤 <output>{{ confidence.toFixed(2) }}</output>
        <input v-model.number="confidence" type="range" min="0" max="1" step="0.01" />
      </label>
      <RouterLink class="secondary-button" to="/compare">新建对比</RouterLink>
      <label class="check-control"><input v-model="overlay" type="checkbox" /> 叠加视图</label>
    </section>
    <div :class="['comparison-grid', { 'overlay-mode': overlay }]">
      <article v-for="task in comparison.tasks" :key="task.id" class="comparison-panel">
        <header>
          <div><strong>{{ algorithmName(task.algorithm_version_id) }}</strong><span>{{ task.status }}</span></div>
          <small class="mono">{{ JSON.stringify(task.parameters) }}</small>
        </header>
        <DetectionCanvas
          v-if="results[task.id] && selectedAsset"
          :image-url="assetsApi.contentUrl(selectedAsset.id)"
          :result="results[task.id]!"
          :confidence="confidence"
          :visible-labels="[...new Set(results[task.id]!.data.detections.map((item) => item.label))]"
          :show-annotations="true"
        />
        <div v-else class="empty-state">{{ task.error_message ?? `正在执行：${task.status}` }}</div>
        <footer v-if="results[task.id]">
          <span>推理 {{ results[task.id]!.timing.inference_ms.toFixed(1) }} ms</span>
          <span>{{ results[task.id]!.data.detections.length }} 个检测</span>
        </footer>
      </article>
    </div>
  </template>
</template>
