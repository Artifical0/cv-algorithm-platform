<script setup lang="ts">
import { computed, ref } from 'vue'

import { tasksApi } from '@/api/tasks'
import TaskTable from '@/components/tasks/TaskTable.vue'
import { useAlgorithms } from '@/composables/useAlgorithms'
import { useTasks } from '@/composables/useTasks'

const { algorithms } = useAlgorithms()
const { tasks, loading, error, refresh, cancel, retry } = useTasks()
const algorithmFilter = ref('')
const statusFilter = ref('')
const assetFilter = ref('')
const createdAfter = ref('')
const selectedResults = ref<string[]>([])
const filteredTasks = computed(() => tasks.value.filter((task) =>
  (!algorithmFilter.value || task.algorithm_version_id === algorithmFilter.value)
  && (!statusFilter.value || task.status === statusFilter.value)
  && (!assetFilter.value || task.asset_id?.includes(assetFilter.value.trim()))
  && (!createdAfter.value || task.created_at >= new Date(createdAfter.value).toISOString()),
))

async function downloadArchive() {
  const blob = await tasksApi.archive(selectedResults.value)
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'cv-results.zip'
  link.click()
  URL.revokeObjectURL(link.href)
}
</script>

<template>
  <header class="page-heading"><span class="eyebrow">INFERENCE QUEUE</span><h1>任务中心</h1><p>追踪算法调用、参数快照和执行状态。</p></header>
  <p v-if="error" class="alert">{{ error }}</p>
  <div class="toolbar"><span>{{ tasks.length }} 个任务</span><button class="secondary-button" @click="refresh">刷新</button></div>
  <div class="algorithm-filters">
    <select v-model="algorithmFilter"><option value="">全部算法</option><option v-for="algorithm in algorithms" :key="algorithm.id" :value="algorithm.id">{{ algorithm.name }} · {{ algorithm.version }}</option></select>
    <select v-model="statusFilter"><option value="">全部状态</option><option v-for="status in ['queued','preparing','starting','running','completed','failed','cancelled']" :key="status" :value="status">{{ status }}</option></select>
    <input v-model="assetFilter" placeholder="按资源 ID 查询" />
    <input v-model="createdAfter" type="datetime-local" title="创建时间不早于" />
  </div>
  <div v-if="loading" class="empty-state">正在加载…</div>
  <template v-else>
    <TaskTable :tasks="filteredTasks" :algorithms="algorithms" />
    <div v-if="filteredTasks.length" class="task-actions-list">
      <div v-for="task in filteredTasks" :key="task.id">
        <input v-if="task.status === 'completed'" v-model="selectedResults" type="checkbox" :value="task.id" title="加入结果归档" />
        <span class="mono">{{ task.id.slice(0, 8) }}</span>
        <button
          v-if="!['completed', 'failed', 'cancelled'].includes(task.status)"
          class="secondary-button danger-button"
          @click="cancel(task.id)"
        >取消</button>
        <button
          v-if="['failed', 'cancelled'].includes(task.status)"
          class="secondary-button"
          @click="retry(task.id)"
        >重试</button>
      </div>
    </div>
    <button v-if="selectedResults.length" class="primary-button compact-button archive-button" @click="downloadArchive">下载 {{ selectedResults.length }} 个结果 ZIP</button>
  </template>
</template>
