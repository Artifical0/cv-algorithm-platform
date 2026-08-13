<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { authApi } from '@/api/auth'

const router = useRouter()
const username = ref('admin')
const password = ref('')
const submitting = ref(false)
const error = ref('')

async function login() {
  submitting.value = true
  error.value = ''
  try {
    await authApi.login(username.value, password.value)
    await router.push('/')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '登录失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <form class="login-panel" @submit.prevent="login">
      <span class="brand-mark">CV</span>
      <p class="eyebrow">LOCAL ADMIN CONSOLE</p>
      <h1>登录平台</h1>
      <p>本地开发阶段使用环境变量配置的单管理员账号。</p>
      <div v-if="error" class="alert">{{ error }}</div>
      <label>用户名<input v-model="username" autocomplete="username" /></label>
      <label>密码<input v-model="password" type="password" autocomplete="current-password" /></label>
      <button class="primary-button" :disabled="submitting || password.length < 12">
        {{ submitting ? '正在验证…' : '登录' }}
      </button>
    </form>
  </main>
</template>
