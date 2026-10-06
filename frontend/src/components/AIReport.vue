<template>
  <div class="card">
    <h2 class="section-title">AI 中文综述（约 500 字）</h2>
    <p class="note">基于代表性论文摘要生成，内容仅供快速了解领域，引用以 PubMed 原文为准</p>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-if="report" class="markdown-body" v-html="html"></div>
    <el-empty v-else description="点击上方「生成 AI 分析」按钮" :image-size="60" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps<{ report: string }>()

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const html = computed(() => md.render(props.report || ''))
</script>

<style scoped>
.note {
  margin: -8px 0 16px;
  font-size: 12px;
  color: #c0c4cc;
}
.markdown-body {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-size: 15px;
  color: #1a2a4f;
  margin: 16px 0 8px;
}
.markdown-body :deep(p) {
  margin: 8px 0;
}
.markdown-body :deep(ol),
.markdown-body :deep(ul) {
  padding-left: 20px;
  margin: 8px 0;
}
.markdown-body :deep(strong) {
  color: #2456a6;
}
</style>
