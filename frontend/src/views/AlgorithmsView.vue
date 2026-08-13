<script setup lang="ts">
import { computed, ref } from 'vue'

import { algorithmsApi } from '@/api/algorithms'
import AlgorithmCard from '@/components/algorithms/AlgorithmCard.vue'
import { useAlgorithms } from '@/composables/useAlgorithms'
import type { Algorithm, BuildJob } from '@/types/algorithm'
import { sessionRole } from '@/api/auth'

const { algorithms, loading, error, refresh } = useAlgorithms()
const actionError = ref('')
const importing = ref(false)
const selected = ref<Algorithm | null>(null)
const buildJob = ref<BuildJob | null>(null)
const query = ref('')
const taskType = ref('')
const algorithmStatus = ref('')
const filteredAlgorithms = computed(() => algorithms.value.filter((algorithm) =>
  (!query.value || algorithm.name.toLowerCase().includes(query.value.toLowerCase()) || algorithm.key.includes(query.value.toLowerCase()))
  && (!taskType.value || algorithm.task_type === taskType.value)
  && (!algorithmStatus.value || algorithm.status === algorithmStatus.value),
))
const canBuild = computed(() => ['admin', 'developer'].includes(sessionRole.get() ?? 'user'))
const isAdmin = computed(() => sessionRole.get() === 'admin')

async function importPackage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  importing.value = true
  actionError.value = ''
  try {
    selected.value = await algorithmsApi.importPackage(file)
    await refresh()
  } catch (reason) {
    actionError.value = reason instanceof Error ? reason.message : '导入算法包失败'
  } finally {
    importing.value = false
    input.value = ''
  }
}

async function buildAlgorithm() {
  if (!selected.value) return
  buildJob.value = await algorithmsApi.build(selected.value.id)
  pollBuild()
}

function pollBuild() {
  if (!buildJob.value) return
  window.setTimeout(async () => {
    if (!buildJob.value) return
    buildJob.value = await algorithmsApi.buildJob(buildJob.value.id)
    await refresh()
    if (!['completed', 'failed'].includes(buildJob.value.status)) pollBuild()
  }, 1500)
}

async function toggleEnabled() {
  if (!selected.value) return
  selected.value = selected.value.status === 'disabled'
    ? await algorithmsApi.enable(selected.value.id)
    : await algorithmsApi.disable(selected.value.id)
  await refresh()
}
async function rollbackVersion() {
  if (!selected.value || !window.confirm(`确认回滚到 ${selected.value.version}？`)) return
  await algorithmsApi.rollback(selected.value.id); await refresh()
}
async function deleteVersion() {
  if (!selected.value || !window.confirm(`确认删除版本 ${selected.value.version}？已有任务引用时会被拒绝。`)) return
  await algorithmsApi.remove(selected.value.id)
  selected.value = null; await refresh()
}
</script>

<template>
  <header class="page-heading">
    <span class="eyebrow">ALGORITHM REGISTRY</span>
    <h1>算法中心</h1>
    <p>算法版本、协议、受控包导入、构建日志和运行环境的统一入口。</p>
  </header>
  <p v-if="error || actionError" class="alert">{{ error || actionError }}</p>
  <div class="toolbar">
    <span>{{ algorithms.length }} 个算法版本</span>
    <div class="toolbar-actions">
      <button class="secondary-button" @click="refresh">刷新</button>
      <label v-if="canBuild" class="primary-button upload-button">
        {{ importing ? '校验中…' : '导入 ZIP' }}
        <input type="file" accept="application/zip,.zip" :disabled="importing" @change="importPackage" />
      </label>
    </div>
  </div>
  <div class="algorithm-filters">
    <input v-model="query" placeholder="搜索名称或算法 ID" />
    <select v-model="taskType"><option value="">全部任务类型</option><option value="object_detection">目标检测</option><option value="classification">分类</option><option value="segmentation">分割</option><option value="ocr">OCR</option><option value="pose_estimation">姿态</option></select>
    <select v-model="algorithmStatus"><option value="">全部状态</option><option value="available">可用</option><option value="disabled">停用</option><option value="uploaded">已上传</option><option value="building">构建中</option><option value="failed">失败</option></select>
  </div>
  <div v-if="loading" class="empty-state">正在加载…</div>
  <div v-else class="algorithm-grid">
    <AlgorithmCard
      v-for="item in filteredAlgorithms"
      :key="item.id"
      :algorithm="item"
      :selected="selected?.id === item.id"
      @select="selected = $event"
    />
  </div>
  <section v-if="selected" class="algorithm-detail section-block">
    <header class="section-heading">
      <div><span>VERSION</span><h2>{{ selected.name }} · {{ selected.version }}</h2></div>
    </header>
    <dl>
      <div><dt>镜像</dt><dd class="mono">{{ selected.image }}</dd></div>
      <div><dt>包 SHA-256</dt><dd class="mono">{{ selected.package_sha256 ?? '内置算法' }}</dd></div>
      <div><dt>镜像摘要</dt><dd class="mono">{{ selected.image_digest ?? '尚未构建' }}</dd></div>
      <div><dt>创建者</dt><dd>{{ selected.created_by }}</dd></div>
    </dl>
    <div class="runtime-actions">
      <button
        v-if="canBuild && ['uploaded', 'failed'].includes(selected.status)"
        class="primary-button compact-button"
        @click="buildAlgorithm"
      >构建并发布</button>
      <button
        v-if="isAdmin && ['available', 'disabled'].includes(selected.status)"
        class="secondary-button"
        @click="toggleEnabled"
      >{{ selected.status === 'disabled' ? '启用版本' : '停用版本' }}</button>
      <button v-if="isAdmin && ['available', 'disabled'].includes(selected.status)" class="secondary-button" @click="rollbackVersion">回滚到此版本</button>
      <button v-if="isAdmin" class="secondary-button danger-button" @click="deleteVersion">删除版本</button>
    </div>
    <div v-if="buildJob" class="build-log">
      <header><strong>构建日志</strong><span>{{ buildJob.status }}</span></header>
      <pre>{{ buildJob.logs.join('\n') || '等待构建 Worker…' }}</pre>
    </div>
  </section>
</template>
