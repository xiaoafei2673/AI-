<template>
  <div class="card">
    <h2 class="section-title">年份发表趋势</h2>
    <div ref="el" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { YearStat } from '../api/research'

const props = defineProps<{ data: YearStat[] }>()

const el = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function render() {
  if (!chart || !props.data.length) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 44, right: 20, top: 20, bottom: 28 },
    xAxis: {
      type: 'category',
      data: props.data.map((d) => String(d.year)),
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#909399' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#909399' },
    },
    series: [
      {
        type: 'line',
        data: props.data.map((d) => d.count),
        smooth: true,
        symbolSize: 5,
        lineStyle: { width: 3, color: '#2f7cf6' },
        itemStyle: { color: '#2f7cf6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(47,124,246,0.25)' },
            { offset: 1, color: 'rgba(47,124,246,0.02)' },
          ]),
        },
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
</style>
