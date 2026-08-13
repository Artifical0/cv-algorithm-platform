<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { advancedApi, type MediaRun, type MediaSource, type RuntimeNode, type ScalingPolicy, type Workflow, type WorkflowRun } from '@/api/advanced'
import { useAlgorithms } from '@/composables/useAlgorithms'
import { useAssets } from '@/composables/useAssets'

const { algorithms } = useAlgorithms()
const { assets } = useAssets()
const media = ref<MediaSource[]>([])
const mediaRuns = ref<MediaRun[]>([])
const workflows = ref<Workflow[]>([])
const workflowRuns = ref<WorkflowRun[]>([])
const nodes = ref<RuntimeNode[]>([])
const policies = ref<ScalingPolicy[]>([])
const metrics = ref<Record<string, unknown>>({})
const error = ref('')
const sourceName = ref('')
const sourceType = ref<'video' | 'rtsp' | 'camera'>('rtsp')
const sourceUri = ref('')
const workflowName = ref('')
const workflowMode = ref<'sequential' | 'parallel'>('sequential')
const workflowAlgorithms = ref<string[]>([])
const node = ref<RuntimeNode>({ id: '', name: '', manager_url: '', enabled: true })
const deploymentText = ref('')
const mediaSourceId = ref('')
const mediaAlgorithmId = ref('')
const mediaInterval = ref(1)
const mediaMaxFrames = ref(100)
const workflowId = ref('')
const workflowAssetId = ref('')
const scalingAlgorithmId = ref('')
const minReplicas = ref(0)
const maxReplicas = ref(2)
const targetConcurrency = ref(1)
const idleSeconds = ref(1800)
const trafficFamily = ref('')
const trafficWeights = ref<Record<string, number>>({})
const algorithmFamilies = computed(() => [...new Set(algorithms.value.map((item) => item.key))])
const trafficVersions = computed(() => algorithms.value.filter((item) => item.key === trafficFamily.value))

async function exportFirst(backend: 'docker' | 'bentoml' | 'kserve') {
  const algorithm = algorithms.value[0]
  if (algorithm) await exportDeployment(algorithm.id, backend)
}

async function refresh() {
  try {
    ;[media.value, mediaRuns.value, workflows.value, workflowRuns.value, nodes.value, policies.value, metrics.value] = await Promise.all([
      advancedApi.mediaSources(), advancedApi.mediaRuns(), advancedApi.workflows(), advancedApi.workflowRuns(), advancedApi.runtimeNodes(), advancedApi.scalingPolicies(), advancedApi.metrics(),
    ])
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '高级功能加载失败' }
}

async function addSource() {
  await advancedApi.createMediaSource({ name: sourceName.value, source_type: sourceType.value, uri: sourceUri.value })
  sourceName.value = ''; sourceUri.value = ''; await refresh()
}

async function uploadVideo(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  await advancedApi.uploadVideo(file)
  input.value = ''
  await refresh()
}

async function startMediaRun() {
  await advancedApi.startMediaRun(mediaSourceId.value, {
    algorithm_version_id: mediaAlgorithmId.value,
    parameters: {}, interval_seconds: mediaInterval.value, max_frames: mediaMaxFrames.value,
  })
  await refresh()
}

async function addWorkflow() {
  const nodes = workflowAlgorithms.value.map((id, index) => ({
    id: `step_${index + 1}`, algorithm_version_id: id, parameters: {}, depends_on: index ? [`step_${index}`] : [],
  }))
  await advancedApi.createWorkflow({ name: workflowName.value, mode: workflowMode.value, nodes })
  workflowName.value = ''; workflowAlgorithms.value = []; await refresh()
}

async function startWorkflow() {
  await advancedApi.startWorkflow(workflowId.value, workflowAssetId.value)
  await refresh()
}

async function addNode() { await advancedApi.registerNode(node.value); await refresh() }
async function saveScaling() {
  await advancedApi.setScalingPolicy(scalingAlgorithmId.value, {
    min_replicas: minReplicas.value, max_replicas: maxReplicas.value,
    target_concurrency: targetConcurrency.value, idle_seconds: idleSeconds.value,
  })
  await advancedApi.reconcileScaling(); await refresh()
}
async function saveTraffic() {
  await advancedApi.setTraffic(Object.fromEntries(trafficVersions.value.map((item) => [item.id, Number(trafficWeights.value[item.id] ?? item.traffic_weight)])))
  await refresh()
}
async function exportDeployment(id: string, backend: 'docker' | 'bentoml' | 'kserve') {
  const result = await advancedApi.deploymentManifest(id, backend)
  deploymentText.value = Object.entries(result.files).map(([name, value]) => `# ${name}\n${value}`).join('\n')
}
onMounted(refresh)
const polling = window.setInterval(() => void refresh(), 5000)
onUnmounted(() => window.clearInterval(polling))
</script>

<template>
  <header class="page-heading"><span class="eyebrow">V2 LAB</span><h1>高级编排</h1><p>媒体源、DAG 工作流、多运行节点与部署后端适配。</p></header>
  <p v-if="error" class="alert">{{ error }}</p>
  <div class="advanced-grid">
    <section class="section-block"><h2>媒体源</h2>
      <label class="secondary-button upload-button">上传视频<input type="file" accept="video/mp4,video/webm,video/quicktime,video/x-msvideo,.mkv" @change="uploadVideo" /></label>
      <input v-model="sourceName" placeholder="名称" /><select v-model="sourceType"><option value="rtsp">RTSP</option><option value="camera">摄像头</option><option value="video">视频文件</option></select><input v-model="sourceUri" placeholder="rtsp://... / camera:0 / file:///data/..." /><button class="primary-button" @click="addSource">注册媒体源</button>
      <p v-for="item in media" :key="item.id" class="mono">{{ item.name }} · {{ item.source_type }}</p>
      <h3>发起媒体推理</h3><select v-model="mediaSourceId"><option value="">选择媒体源</option><option v-for="item in media" :key="item.id" :value="item.id">{{ item.name }}</option></select><select v-model="mediaAlgorithmId"><option value="">选择算法</option><option v-for="item in algorithms" :key="item.id" :value="item.id">{{ item.name }} · {{ item.version }}</option></select><input v-model.number="mediaInterval" type="number" min="0.1" max="60" step="0.1" title="抽帧间隔秒" /><input v-model.number="mediaMaxFrames" type="number" min="1" max="10000" title="最大帧数" /><button class="primary-button" :disabled="!mediaSourceId || !mediaAlgorithmId" @click="startMediaRun">开始媒体推理</button>
      <p v-for="run in mediaRuns" :key="run.id" class="mono">{{ run.id.slice(0, 8) }} · {{ run.status }} · {{ run.frame_task_ids.length }} 帧</p>
    </section>
    <section class="section-block"><h2>DAG 工作流</h2>
      <input v-model="workflowName" placeholder="工作流名称" /><select v-model="workflowMode"><option value="sequential">串行执行</option><option value="parallel">并行就绪节点</option></select>
      <label v-for="algorithm in algorithms" :key="algorithm.id" class="check-control"><input v-model="workflowAlgorithms" type="checkbox" :value="algorithm.id" />{{ algorithm.name }}</label>
      <button class="primary-button" :disabled="!workflowName || !workflowAlgorithms.length" @click="addWorkflow">创建 DAG</button>
      <p v-for="item in workflows" :key="item.id">{{ item.name }} · {{ item.nodes.length }} 节点</p>
      <h3>运行工作流</h3><select v-model="workflowId"><option value="">选择工作流</option><option v-for="item in workflows" :key="item.id" :value="item.id">{{ item.name }}</option></select><select v-model="workflowAssetId"><option value="">选择图片</option><option v-for="item in assets" :key="item.id" :value="item.id">{{ item.original_name }}</option></select><button class="primary-button" :disabled="!workflowId || !workflowAssetId" @click="startWorkflow">运行 DAG</button>
      <p v-for="run in workflowRuns" :key="run.id" class="mono">{{ run.id.slice(0, 8) }} · {{ run.status }} · {{ Object.keys(run.node_tasks).length }} 节点</p>
    </section>
    <section class="section-block"><h2>运行节点</h2>
      <input v-model="node.id" placeholder="node-id" /><input v-model="node.name" placeholder="节点名称" /><input v-model="node.manager_url" placeholder="http://manager:8010/api/v1" /><button class="primary-button" @click="addNode">注册节点</button>
      <p v-for="item in nodes" :key="item.id" class="mono">{{ item.id }} · {{ item.manager_url }}</p>
    </section>
    <section class="section-block"><h2>部署与指标</h2>
      <pre>{{ JSON.stringify(metrics, null, 2) }}</pre>
      <template v-if="algorithms.length"><button class="secondary-button" @click="exportFirst('docker')">Docker</button><button class="secondary-button" @click="exportFirst('bentoml')">BentoML</button><button class="secondary-button" @click="exportFirst('kserve')">KServe</button></template>
      <pre v-if="deploymentText">{{ deploymentText }}</pre>
    </section>
    <section class="section-block"><h2>自动扩缩容</h2>
      <select v-model="scalingAlgorithmId"><option value="">选择算法版本</option><option v-for="item in algorithms" :key="item.id" :value="item.id">{{ item.name }} · {{ item.version }}</option></select>
      <label>最小副本<input v-model.number="minReplicas" type="number" min="0" max="100" /></label><label>最大副本<input v-model.number="maxReplicas" type="number" min="1" max="100" /></label><label>单副本并发<input v-model.number="targetConcurrency" type="number" min="1" max="1000" /></label><label>空闲秒数<input v-model.number="idleSeconds" type="number" min="30" max="86400" /></label><button class="primary-button" :disabled="!scalingAlgorithmId" @click="saveScaling">保存并立即协调</button>
      <p v-for="item in policies" :key="item.algorithm_version_id" class="mono">{{ item.algorithm_version_id.slice(0, 8) }} · {{ item.min_replicas }}~{{ item.max_replicas }} 副本</p>
    </section>
    <section class="section-block"><h2>灰度流量</h2>
      <select v-model="trafficFamily"><option value="">选择算法族</option><option v-for="key in algorithmFamilies" :key="key" :value="key">{{ key }}</option></select>
      <label v-for="item in trafficVersions" :key="item.id">{{ item.version }} 权重（%）<input v-model.number="trafficWeights[item.id]" type="number" min="0" max="100" :placeholder="String(item.traffic_weight)" /></label><button class="primary-button" :disabled="!trafficFamily" @click="saveTraffic">发布权重（合计 100）</button>
    </section>
  </div>
</template>
