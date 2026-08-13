<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { assetsApi } from '@/api/assets'
import { tasksApi } from '@/api/tasks'
import DetectionCanvas from '@/components/results/DetectionCanvas.vue'
import ClassificationRenderer from '@/components/results/ClassificationRenderer.vue'
import OcrRenderer from '@/components/results/OcrRenderer.vue'
import PoseRenderer from '@/components/results/PoseRenderer.vue'
import SegmentationRenderer from '@/components/results/SegmentationRenderer.vue'
import type { AlgorithmResult, InferenceTask } from '@/types/task'

const route = useRoute()
const task = ref<InferenceTask | null>(null)
const result = ref<AlgorithmResult | null>(null)
const error = ref('')
const confidence = ref(0)
const showAnnotations = ref(true)
const hiddenLabels = ref<string[]>([])
const taskId = computed(() => String(route.params.id))
const labels = computed(() =>
  result.value?.type === 'object_detection'
    ? [...new Set(result.value.data.detections.map((item) => item.label))].sort()
    : [],
)
const visibleLabels = computed(() => labels.value.filter((label) => !hiddenLabels.value.includes(label)))
const imageUrl = computed(() => task.value?.asset_id ? assetsApi.contentUrl(task.value.asset_id) : '')
let eventSource: EventSource | null = null

async function load() {
  try {
    task.value = await tasksApi.get(taskId.value)
    if (task.value.status === 'completed') {
      result.value = (await tasksApi.result(taskId.value)).result
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '加载任务失败'
  }
}

function toggleLabel(label: string) {
  hiddenLabels.value = hiddenLabels.value.includes(label)
    ? hiddenLabels.value.filter((item) => item !== label)
    : [...hiddenLabels.value, label]
}

function downloadJson() {
  if (!result.value) return
  const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json' })
  const link = document.createElement('a')
  link.download = `result-${taskId.value}.json`
  link.href = URL.createObjectURL(blob)
  link.click()
  URL.revokeObjectURL(link.href)
}

onMounted(async () => {
  await load()
  if (task.value && !['completed', 'failed', 'cancelled'].includes(task.value.status)) {
    eventSource = tasksApi.subscribe(taskId.value, () => void load())
  }
})
const polling = window.setInterval(() => {
  if (task.value && !['completed', 'failed', 'cancelled'].includes(task.value.status)) void load()
}, 1500)
onUnmounted(() => {
  window.clearInterval(polling)
  eventSource?.close()
})
</script>

<template>
  <header class="page-heading">
    <span class="eyebrow">RESULT INSPECTOR</span>
    <h1>任务详情</h1>
    <p class="mono">{{ taskId }}</p>
  </header>
  <p v-if="error" class="alert">{{ error }}</p>
  <div v-if="!task" class="empty-state">正在加载任务…</div>
  <template v-else>
    <section class="task-summary">
      <div><span>状态</span><strong>{{ task.status }}</strong></div>
      <div><span>容器</span><strong class="mono">{{ task.container_id?.slice(0, 12) ?? '—' }}</strong></div>
      <div><span>错误</span><strong>{{ task.error_message ?? '—' }}</strong></div>
    </section>
    <div v-if="task.status === 'failed'" class="alert">{{ task.error_code }} · {{ task.error_message }}</div>
    <div v-else-if="task.status !== 'completed'" class="empty-state">任务正在执行：{{ task.status }}</div>
    <template v-else-if="result">
      <section class="result-controls">
        <label>最低置信度 <output>{{ confidence.toFixed(2) }}</output>
          <input v-model.number="confidence" type="range" min="0" max="1" step="0.01" />
        </label>
        <label class="check-control"><input v-model="showAnnotations" type="checkbox" /> 显示结果图层</label>
        <button class="secondary-button" @click="downloadJson">下载标准 JSON</button>
      </section>
      <div class="filter-chips">
        <button
          v-for="label in labels"
          :key="label"
          :class="{ disabled: hiddenLabels.includes(label) }"
          @click="toggleLabel(label)"
        >{{ label }}</button>
      </div>
      <DetectionCanvas
        v-if="result.type === 'object_detection'"
        :image-url="imageUrl"
        :result="result"
        :confidence="confidence"
        :visible-labels="visibleLabels"
        :show-annotations="showAnnotations"
      />
      <ClassificationRenderer
        v-else-if="result.type === 'classification'"
        :result="result"
        :confidence="confidence"
      />
      <SegmentationRenderer
        v-else-if="result.type === 'segmentation'"
        :image-url="imageUrl"
        :result="result"
        :confidence="confidence"
      />
      <OcrRenderer v-else-if="result.type === 'ocr'" :image-url="imageUrl" :result="result" :confidence="confidence" />
      <PoseRenderer
        v-else-if="result.type === 'pose_estimation'"
        :image-url="imageUrl"
        :result="result"
        :confidence="confidence"
      />
      <section class="timing-grid">
        <div><span>预处理</span><strong>{{ result.timing.preprocess_ms.toFixed(1) }} ms</strong></div>
        <div><span>推理</span><strong>{{ result.timing.inference_ms.toFixed(1) }} ms</strong></div>
        <div><span>后处理</span><strong>{{ result.timing.postprocess_ms.toFixed(1) }} ms</strong></div>
        <div><span>结果类型</span><strong>{{ result.type }}</strong></div>
      </section>
    </template>
  </template>
</template>
