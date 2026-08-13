<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { authApi, type User } from '@/api/auth'

const users = ref<User[]>([])
const username = ref('')
const password = ref('')
const role = ref<User['role']>('user')
const error = ref('')
async function refresh() { try { users.value = await authApi.users() } catch (reason) { error.value = reason instanceof Error ? reason.message : '用户加载失败' } }
async function createUser() { await authApi.createUser({ username: username.value, password: password.value, role: role.value }); username.value = ''; password.value = ''; await refresh() }
async function save(user: User) { await authApi.updateUser(user.id, { role: user.role, enabled: user.enabled }); await refresh() }
onMounted(refresh)
</script>

<template>
  <header class="page-heading"><span class="eyebrow">PLATFORM RBAC</span><h1>用户与角色</h1><p>管理员创建账号并设置 admin、developer、user 平台角色；项目权限在项目成员页设置。</p></header>
  <p v-if="error" class="alert">{{ error }}</p>
  <section class="section-block user-create"><h2>创建用户</h2><input v-model="username" placeholder="用户名" /><input v-model="password" type="password" placeholder="至少 12 位密码" /><select v-model="role"><option value="user">普通用户</option><option value="developer">算法开发者</option><option value="admin">管理员</option></select><button class="primary-button compact-button" :disabled="!username || password.length < 12" @click="createUser">创建</button></section>
  <section class="section-block"><div class="user-table"><div v-for="user in users" :key="user.id" class="user-row"><span>{{ user.username }}</span><select v-model="user.role"><option value="user">user</option><option value="developer">developer</option><option value="admin">admin</option></select><label><input v-model="user.enabled" type="checkbox" />启用</label><button class="secondary-button" @click="save(user)">保存</button></div></div></section>
</template>
