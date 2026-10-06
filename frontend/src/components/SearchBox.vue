<template>
  <div class="search-box">
    <el-input
      v-model="query"
      size="large"
      clearable
      placeholder="输入英文关键词，如 lung cancer、crispr、alzheimer's disease"
      :disabled="loading"
      @keyup.enter="emitSearch"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <el-select v-model="limit" size="large" class="limit-select" :disabled="loading">
      <el-option v-for="n in [50, 100, 200, 500]" :key="n" :value="n" :label="`${n} 篇`" />
    </el-select>
    <el-button type="primary" size="large" :loading="loading" class="search-btn" @click="emitSearch">
      {{ loading ? '检索中…' : '搜索' }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps<{ loading: boolean; initialQuery?: string; initialLimit?: number }>()
const emit = defineEmits<{ search: [query: string, limit: number] }>()

const query = ref(props.initialQuery ?? '')
const limit = ref(props.initialLimit ?? 50)

// 外部传入新关键词/新 limit 时同步(如从首页跳入、结果页刷新后回显实际搜索量)
watch(
  () => props.initialQuery,
  (v) => {
    if (v !== undefined) query.value = v
  }
)
watch(
  () => props.initialLimit,
  (v) => {
    if (v !== undefined) limit.value = v
  }
)

function emitSearch() {
  const q = query.value.trim()
  if (!q || props.loading) return // 空词与重复提交拦截
  emit('search', q, limit.value)
}
</script>

<style scoped>
.search-box {
  display: flex;
  gap: 12px;
  width: 100%;
  max-width: 860px;
}
.search-box :deep(.el-input__wrapper) {
  border-radius: 8px;
}
.limit-select {
  width: 110px;
  flex-shrink: 0;
}
.search-btn {
  width: 110px;
  flex-shrink: 0;
  border-radius: 8px;
  font-weight: 600;
}
</style>
