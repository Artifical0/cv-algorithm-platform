<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { assetsApi } from '@/api/assets'
import AlgorithmCard from '@/components/algorithms/AlgorithmCard.vue'
import TaskTable from '@/components/tasks/TaskTable.vue'
import { useAlgorithms } from '@/composables/useAlgorithms'
import { useAssets } from '@/composables/useAssets'
import { useTasks } from '@/composables/useTasks'
import type { Algorithm, ParameterSpec } from '@/types/algorithm'

const router = useRouter()
const { algorithms, availableAlgorithms, loading, error } = useAlgorithms()
const { assets, uploading, error: assetError, upload } = useAssets()
const { tasks, submitting, error: taskError, create } = useTasks()
const selected = ref<Algorithm | null>(null)
const selectedAssetId = ref('')
const parameterValues = ref<Record<string, string | number | boolean>>({})
const notice = ref('')

const activeSelection = computed(() => selected.value ?? availableAlgorithms.value[0] ?? null)
const selectedAsset = computed(() => assets.value.find((asset) => asset.id === selectedAssetId.value))

watch(activeSelection, (algorithm) => {
  parameterValues.value = Object.fromEntries(
    Object.entries(algorithm?.parameters ?? {}).map(([name, spec]) => [name, spec.default]),
  )
}, { immediate: true })

watch(assets, (items) => {
  if (!selectedAssetId.value && items[0]) selectedAssetId.value = items[0].id
}, { immediate: true })

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (!files.length) return
  const uploaded = await upload(files)
  if (uploaded[0]) selectedAssetId.value = uploaded[0].id
  input.value = ''
}

function numericBounds(spec: ParameterSpec) {
  return spec.type === 'number' || spec.type === 'integer'
    ? { min: spec.minimum, max: spec.maximum, step: spec.type === 'integer' ? 1 : 0.01 }
    : {}
}

async function submitTask() {
  if (!activeSelection.value || !selectedAssetId.value) return
  const task = await create({
    algorithm_version_id: activeSelection.value.id,
    asset_id: selectedAssetId.value,
    parameters: parameterValues.value,
  })
  notice.value = `任务 ${task.id.slice(0, 8)} 已进入队列`
  await router.push(`/tasks/${task.id}`)
}
</script>

<template>
  <section class="hero">
    <div>
      <span class="eyebrow">LOCAL ASYNC INFERENCE</span>
      <h1>上传一张图片，运行不同的<br /><em>视觉算法容器</em></h1>
      <p>PostgreSQL 持久化模式已支持受控图片存储、异步任务、容器复用和标准结果校验。</p>
    </div>
    <div class="hero-metric">
      <span>已注册算法</span><strong>{{ algorithms.length.toString().padStart(2, '0') }}</strong>
      <small>{{ availableAlgorithms.length }} 个可用于推理</small>
    </div>
  </section>

  <p v-if="error || taskError || assetError" class="alert">{{ error || taskError || assetError }}</p>

  <section class="section-block">
    <header class="section-heading">
      <div><span>01</span><h2>选择算法</h2></div>
      <RouterLink to="/algorithms">进入算法中心 →</RouterLink>
    </header>
    <div v-if="loading" class="empty-state">正在加载算法…</div>
    <div v-else class="algorithm-grid">
      <AlgorithmCard
        v-for="algorithm in algorithms"
        :key="algorithm.id"
        :algorithm="algorithm"
        :selected="activeSelection?.id === algorithm.id"
        @select="selected = $event"
      />
    </div>
  </section>

  <section class="runner-grid">
    <div class="section-block task-form">
      <header class="section-heading"><div><span>02</span><h2>图片与参数</h2></div></header>
      <label class="upload-dropzone">
        {{ uploading ? '正在校验并上传…' : '上传 JPG / PNG / BMP / WebP' }}
        <input
          type="file"
          accept="image/jpeg,image/png,image/bmp,image/webp"
          :disabled="uploading"
          @change="handleUpload"
        />
      </label>
      <label v-if="assets.length">输入资源
        <select v-model="selectedAssetId">
          <option v-for="asset in assets" :key="asset.id" :value="asset.id">
            {{ asset.original_name }} · {{ asset.width }}×{{ asset.height }}
          </option>
        </select>
      </label>
      <img
        v-if="selectedAsset"
        class="selected-asset-preview"
        :src="assetsApi.contentUrl(selectedAsset.id)"
        :alt="selectedAsset.original_name"
      />
      <template v-for="(spec, name) in activeSelection?.parameters ?? {}" :key="name">
        <label v-if="spec.type === 'number' || spec.type === 'integer'">
          {{ name }} <output>{{ parameterValues[name] }}</output>
          <input
            v-model.number="parameterValues[name]"
            type="range"
            v-bind="numericBounds(spec)"
          />
        </label>
        <label v-else-if="spec.type === 'boolean'" class="check-control">
          <input v-model="parameterValues[name]" type="checkbox" /> {{ name }}
        </label>
        <label v-else>{{ name }}
          <select v-if="spec.options" v-model="parameterValues[name]">
            <option v-for="option in spec.options" :key="option" :value="option">{{ option }}</option>
          </select>
          <input v-else v-model="parameterValues[name]" />
        </label>
      </template>
      <div class="selected-algorithm">
        <span>将调用</span><strong>{{ activeSelection?.name ?? '暂无可用算法' }}</strong>
      </div>
      <button
        class="primary-button"
        :disabled="!activeSelection || !selectedAssetId || submitting"
        @click="submitTask"
      >{{ submitting ? '正在提交…' : '提交到任务队列' }}</button>
      <p v-if="notice" class="success-message">{{ notice }}</p>
    </div>
    <div class="section-block protocol-panel">
      <header class="section-heading"><div><span>03</span><h2>任务执行链路</h2></div></header>
      <code><b>1</b> queued / preparing</code>
      <code><b>2</b> starting / running</code>
      <code><b>3</b> schema validation</code>
      <code><b>4</b> completed / failed</code>
      <p>进程内线程队列提供本地异步行为，部署服务器时可替换为 Redis/Celery。</p>
    </div>
  </section>

  <section class="section-block">
    <header class="section-heading"><div><span>04</span><h2>最近任务</h2></div><RouterLink to="/tasks">全部任务 →</RouterLink></header>
    <TaskTable :tasks="tasks.slice(0, 5)" :algorithms="algorithms" />
  </section>
</template>
