<script setup lang="ts">
import { useRouter } from 'vue-router'
import { computed } from 'vue'

import { authenticationMode, authApi, sessionRole } from '@/api/auth'

const router = useRouter()
const authenticationEnabled = authenticationMode.get()
const navigation = [
  { label: '工作台', to: '/', icon: '⌂' },
  { label: '算法中心', to: '/algorithms', icon: '◇' },
  { label: '资源中心', to: '/assets', icon: '▧' },
  { label: '运行实例', to: '/instances', icon: '▣' },
  { label: '任务中心', to: '/tasks', icon: '↗' },
  { label: '结果对比', to: '/compare', icon: '⇄' },
  { label: '系统管理', to: '/system', icon: '⚙', roles: ['admin'] },
  { label: '高级编排', to: '/advanced', icon: '⌘', roles: ['admin'] },
  { label: '项目成员', to: '/projects', icon: '◎' },
  { label: '用户角色', to: '/users', icon: '♙', roles: ['admin'] },
]
const visibleNavigation = computed(() => navigation.filter((item) => !item.roles || item.roles.includes(sessionRole.get() ?? 'user')))

async function logout() {
  await authApi.logout()
  await router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">CV</span>
        <span><strong>Algorithm</strong><small>Studio</small></span>
      </RouterLink>

      <nav aria-label="主导航">
        <RouterLink v-for="item in visibleNavigation" :key="item.to" :to="item.to" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>{{ item.label }}
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <span class="status-dot" />
        <div><strong>平台在线</strong><small>PostgreSQL 持久化</small></div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div>
          <p>工作空间</p>
          <strong>多算法计算机视觉平台</strong>
        </div>
        <span class="phase-badge">服务运行中</span>
        <button v-if="authenticationEnabled" class="secondary-button" @click="logout">退出</button>
      </header>
      <div class="page-content"><slot /></div>
    </main>
  </div>
</template>
