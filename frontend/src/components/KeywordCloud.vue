<template>
  <div class="card">
    <h2 class="section-title">研究热点关键词</h2>
    <div ref="el" class="chart"></div>
    <p class="note">* 词频统计自论文标题、摘要、作者关键词与 MeSH 主题词，已去除停用词与宽泛术语</p>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { KeywordFreq } from '../api/research'

const props = defineProps<{ data: KeywordFreq[] }>()

const el = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 科研蓝青色系
const PALETTE = ['#2456a6', '#2f7cf6', '#36cfc9', '#5b8ff9', '#13c2c2', '#4096ff', '#1d39c4', '#08979c']

function render() {
  if (!chart || !props.data.length) return
  // value 传的是 sqrt(count)，tooltip 需要查表显示原始词频
  const countMap = new Map(props.data.map((d) => [d.word, d.count]))
  chart.setOption({
    tooltip: {
      show: true,
      formatter: (p: { name: string }) => `${p.name}：${countMap.get(p.name) ?? ''} 次`,
    },
    series: [
      {
        type: 'wordCloud',
        shape: 'circle',
        width: '95%', // 默认 70%/80% 会把词云限制在中央小区域，放大盒子让词铺满横向
        height: '100%',
        gridSize: 10, // 网格稍大 → 排布更松散 → 铺得更开
        sizeRange: [18, 78],
        rotationRange: [-30, 30],
        rotationStep: 30,
        drawOutOfBound: false,
        textStyle: {
          color: () => PALETTE[Math.floor(Math.random() * PALETTE.length)],
        },
        emphasis: {
          textStyle: { fontWeight: 'bold', textShadowBlur: 8, textShadowColor: 'rgba(36,86,166,0.3)' },
        },
        // 词频是 Zipf 分布（少数大词 + 大量小词），线性映射会让大多数词贴着最小字号、
        // 词云缩成一团；sqrt 压缩量纲、抬升中低频词，词云才能铺满整个卡片
        data: props.data.map((d) => ({ name: d.word, value: Math.sqrt(d.count) })),
      },
    ],
  } as echarts.EChartsOption)
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
  height: 320px;
}
.note {
  margin: 4px 0 0;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
