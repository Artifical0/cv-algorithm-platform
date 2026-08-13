import { createRouter, createWebHistory } from 'vue-router'
import { sessionToken } from '@/api/http'
import { sessionRole } from '@/api/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    { path: '/', name: 'workspace', component: () => import('@/views/WorkspaceView.vue') },
    { path: '/algorithms', name: 'algorithms', component: () => import('@/views/AlgorithmsView.vue') },
    { path: '/assets', name: 'assets', component: () => import('@/views/AssetsView.vue') },
    { path: '/instances', name: 'instances', component: () => import('@/views/InstancesView.vue') },
    { path: '/tasks', name: 'tasks', component: () => import('@/views/TasksView.vue') },
    { path: '/tasks/:id', name: 'task-detail', component: () => import('@/views/TaskDetailView.vue') },
    { path: '/compare/:id?', name: 'compare', component: () => import('@/views/CompareView.vue') },
    { path: '/system', name: 'system', component: () => import('@/views/SystemView.vue'), meta: { roles: ['admin'] } },
    { path: '/advanced', name: 'advanced', component: () => import('@/views/AdvancedView.vue'), meta: { roles: ['admin'] } },
    { path: '/projects', name: 'projects', component: () => import('@/views/ProjectsView.vue') },
    { path: '/users', name: 'users', component: () => import('@/views/UsersView.vue'), meta: { roles: ['admin'] } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.public && !sessionToken.get()) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.name === 'login' && sessionToken.get()) return { name: 'workspace' }
  const roles = to.meta.roles as string[] | undefined
  if (roles && !roles.includes(sessionRole.get() ?? 'user')) return { name: 'workspace' }
})
