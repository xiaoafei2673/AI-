<template>
  <HomeView v-if="view === 'home'" :loading="false" @search="goDashboard" />
  <ResearchDashboard
    v-else
    :initial-query="query"
    :initial-limit="limit"
    @back="view = 'home'"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ResearchDashboard from './views/ResearchDashboard.vue'

// 简单视图状态机:home ↔ dashboard(不引入 vue-router)
const view = ref<'home' | 'dashboard'>('home')
const query = ref('')
const limit = ref(50)

function goDashboard(q: string, l: number) {
  query.value = q
  limit.value = l
  view.value = 'dashboard'
}
</script>
