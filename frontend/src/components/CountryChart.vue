<template>
  <div class="card">
    <h2 class="section-title">国家/地区分布 Top 10</h2>
    <div ref="el" class="chart"></div>
    <p v-if="unknownCount > 0" class="note">
      * 国家解析自第一作者单位末段国家词，另有 {{ unknownCount }} 篇无法识别
    </p>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { CountryStat } from '../api/research'

const props = defineProps<{ data: CountryStat[] }>()

const el = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 剔除 Unknown 取前 10，横向柱状图（y 轴倒序使最大值在上）
const top10 = computed(() => props.data.filter((d) => d.country !== 'Unknown').slice(0, 10))
const unknownCount = computed(
  () => props.data.find((d) => d.country === 'Unknown')?.count ?? 0
)

function render() {
  if (!chart || !top10.value.length) return
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 30, top: 10, bottom: 10, containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#909399' },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: top10.value.map((d) => d.country),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#606266' },
    },
    series: [
      {
        type: 'bar',
        data: top10.value.map((d) => d.count),
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 7, 7, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#2456a6' },
            { offset: 1, color: '#2f7cf6' },
          ]),
        },
        label: { show: true, position: 'right', color: '#909399' },
      },
    ],
  })
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  chart = echarts.init(el.value!)
  render()
  window.addEventListener('resize', resize)
})
watch(() => props.data, render)
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})
</script>

<style scoped>
.chart {
  height: 300px;
}
.note {
  margin: 4px 0 0;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
