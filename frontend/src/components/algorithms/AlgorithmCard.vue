<script setup lang="ts">
import type { Algorithm } from '@/types/algorithm'

defineProps<{ algorithm: Algorithm; selected?: boolean }>()
defineEmits<{ select: [algorithm: Algorithm] }>()

const taskLabels: Record<Algorithm['task_type'], string> = {
  object_detection: '目标检测',
  classification: '图像分类',
  segmentation: '图像分割',
  ocr: 'OCR',
  pose_estimation: '姿态估计',
}
</script>

<template>
  <button
    class="algorithm-card"
    :class="{ selected }"
    type="button"
    @click="$emit('select', algorithm)"
  >
    <div class="card-heading">
      <span class="algorithm-icon">{{ algorithm.key.startsWith('yolo') ? 'YO' : 'FR' }}</span>
      <span class="availability"><i /> {{ algorithm.status === 'available' ? '可用' : algorithm.status }}</span>
    </div>
    <strong>{{ algorithm.name }}</strong>
    <p>{{ algorithm.description }}</p>
    <div class="tag-row">
      <span>{{ taskLabels[algorithm.task_type] }}</span>
      <span>{{ algorithm.framework }}</span>
      <span>{{ algorithm.device.toUpperCase() }}</span>
    </div>
    <footer><span>v{{ algorithm.version }}</span><span>{{ algorithm.container_status }}</span></footer>
    <footer><span>最近调用</span><span>{{ algorithm.last_called_at ? new Date(algorithm.last_called_at).toLocaleString() : '暂无' }}</span></footer>
  </button>
</template>
