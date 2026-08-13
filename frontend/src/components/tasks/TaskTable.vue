<script setup lang="ts">
import type { Algorithm } from '@/types/algorithm'
import type { InferenceTask } from '@/types/task'

const props = defineProps<{ tasks: InferenceTask[]; algorithms: Algorithm[] }>()

function algorithmName(id: string) {
  return props.algorithms.find((item) => item.id === id)?.name ?? '未知算法'
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <div v-if="tasks.length" class="task-table">
    <div class="task-row task-head"><span>任务</span><span>算法</span><span>状态</span><span>创建时间</span></div>
    <RouterLink v-for="task in tasks" :key="task.id" :to="`/tasks/${task.id}`" class="task-row">
      <span class="mono">{{ task.id.slice(0, 8) }}</span>
      <span>{{ algorithmName(task.algorithm_version_id) }}</span>
      <span :class="`task-status task-${task.status}`"><i class="status-dot" /> {{ task.status }}</span>
      <span>{{ formatTime(task.created_at) }}</span>
    </RouterLink>
  </div>
  <div v-else class="empty-state">尚无任务。选择算法并创建第一个推理任务。</div>
</template>
