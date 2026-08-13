<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { projectContext } from '@/api/http'
import { projectsApi, type Project, type ProjectMember } from '@/api/projects'

const projects = ref<Project[]>([])
const members = ref<ProjectMember[]>([])
const selectedId = ref(projectContext.get() ?? '')
const name = ref('')
const description = ref('')
const memberUsername = ref('')
const memberRole = ref<ProjectMember['role']>('viewer')
const error = ref('')
const selectedProject = () => projects.value.find((item) => item.id === selectedId.value)

async function refresh() {
  try {
    projects.value = await projectsApi.list()
    if (!selectedId.value && projects.value[0]) selectedId.value = projects.value[0].id
    await loadMembers()
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '项目加载失败' }
}
async function loadMembers() {
  if (!selectedId.value) return
  projectContext.set(selectedId.value)
  members.value = await projectsApi.members(selectedId.value)
}
async function createProject() {
  const project = await projectsApi.create({ name: name.value, description: description.value })
  name.value = ''; description.value = ''; selectedId.value = project.id; projectContext.set(project.id); await refresh()
}
async function addMember() {
  await projectsApi.addMember(selectedId.value, { username: memberUsername.value, role: memberRole.value })
  memberUsername.value = ''; await loadMembers()
}
function activateProject() {
  projectContext.set(selectedId.value)
  window.location.assign('/')
}
onMounted(refresh)
</script>

<template>
  <header class="page-heading"><span class="eyebrow">PROJECT RBAC</span><h1>项目与成员</h1><p>项目隔离算法、图片、任务、媒体源和工作流；成员按 owner/editor/viewer 授权。</p></header>
  <p v-if="error" class="alert">{{ error }}</p>
  <div class="project-grid">
    <section class="section-block"><h2>当前项目</h2><select v-model="selectedId" @change="loadMembers"><option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }} · {{ item.role }}</option></select><button class="primary-button" :disabled="!selectedId" @click="activateProject">切换并进入工作台</button><p v-for="item in projects" :key="item.id" class="mono">{{ item.name }} · {{ item.description || '无描述' }}</p></section>
    <section class="section-block"><h2>新建项目</h2><input v-model="name" placeholder="项目名称" /><textarea v-model="description" placeholder="项目说明" /><button class="primary-button" :disabled="!name" @click="createProject">创建项目</button></section>
    <section class="section-block"><h2>项目成员</h2><p v-for="item in members" :key="item.user_id">{{ item.username }} · {{ item.role }}</p><template v-if="selectedProject()?.role === 'owner'"><input v-model="memberUsername" placeholder="已存在的用户名" /><select v-model="memberRole"><option value="editor">编辑者</option><option value="viewer">访客</option><option value="owner">所有者</option></select><button class="primary-button" :disabled="!memberUsername || !selectedId" @click="addMember">添加或更新成员</button></template></section>
  </div>
</template>
