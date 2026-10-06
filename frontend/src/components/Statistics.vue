<template>
  <!-- 5 张卡片 flex 等分整行（24 栅格除不尽 5，el-row 会右侧留空） -->
  <div class="stat-row">
    <div v-for="card in cards" :key="card.label" class="card stat-card">
      <div class="stat-value">{{ card.value }}</div>
      <div class="stat-label">{{ card.label }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AnalyzeResponse } from '../api/research'

const props = defineProps<{ analysis: AnalyzeResponse; hitTotal: number }>()

const cards = computed(() => {
  const a = props.analysis
  return [
    { label: 'PubMed 命中总数', value: props.hitTotal.toLocaleString() },
    { label: '本次分析论文', value: a.total.toLocaleString() },
    {
      label: '年份范围',
      value: a.year_range.start ? `${a.year_range.start}~${a.year_range.end}` : 'N/A',
    },
    { label: '覆盖国家/地区', value: a.by_country.filter((c) => c.country !== 'Unknown').length },
    { label: `近5年论文(≥${a.year_range.recent_start})`, value: a.recent_5y_count },
  ]
})
</script>

<style scoped>
.stat-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.stat-card {
  flex: 1 1 0; /* 等分剩余宽度 */
  min-width: 150px; /* 窄屏自动换行：约 375px 宽时每行 2 张 */
  text-align: center;
  padding: 18px 12px;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a2a4f;
}
.stat-label {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>
