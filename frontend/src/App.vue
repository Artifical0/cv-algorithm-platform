<script setup lang="ts">
import AppShell from '@/components/layout/AppShell.vue'
</script>

<template>
  <RouterView v-if="$route.meta.public" />
  <AppShell v-else><RouterView /></AppShell>
</template>
