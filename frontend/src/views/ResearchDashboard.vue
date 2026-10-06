<template>
  <div class="dashboard">
    <!-- 顶部吸顶栏:logo + 搜索 + 返回首页 -->
    <header class="header">
      <div class="header-inner">
        <div class="brand" @click="emit('back')">
          <h1 class="title">PubMed<span class="accent">AI</span></h1>
        </div>
        <SearchBox :loading="loading" :initial-query="initialQuery" :initial-limit="searchedLimit" @search="onSearch" />
        <a class="back-link" @click="emit('back')">← 返回首页</a>
      </div>
    </header>

    <main class="content">
      <!-- 错误提示 -->
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        :closable="true"
        class="error-alert"
        @close="error = ''"
      />

      <!-- 初始空状态 -->
      <el-empty
        v-if="!loading && !analysis && !error"
        description="输入关键词开始检索 PubMed 文献（请使用英文关键词）"
        :image-size="140"
      >
        <template #image>
          <el-icon :size="64" color="#c0c4cc"><Document /></el-icon>
        </template>
      </el-empty>

      <!-- 加载骨架 -->
      <div v-if="loading" class="card loading-card">
        <el-skeleton :rows="6" animated />
        <p class="loading-tip">
          正在检索 PubMed 并批量获取论文详情（美国服务器，跨境较慢）… 已等待 {{ elapsed }} 秒
        </p>
      </div>

      <template v-if="analysis && !loading">
        <!-- 缓存命中提示 -->
        <p v-if="fromCache" class="cache-tip">⚡ 该关键词结果来自 30 分钟内缓存,秒级返回</p>

        <!-- 统计卡片 -->
        <Statistics :analysis="analysis" :hit-total="hitTotal" />

        <!-- 年份趋势 + 国家分布 -->
        <el-row :gutter="16" class="chart-row">
          <el-col :xs="24" :md="14">
            <YearChart :data="analysis.by_year" />
          </el-col>
          <el-col :xs="24" :md="10">
            <CountryChart :data="analysis.by_country" />
          </el-col>
        </el-row>

        <!-- 关键词词云 -->
        <KeywordCloud :data="analysis.top_keywords" />

        <!-- 近5年高影响力 Top100 -->
        <TopPapers
          :papers="analysis.top100"
          :citation-available="analysis.citation_available"
          :recent-start="analysis.year_range.recent_start"
        />

        <!-- AI 分析触发区 -->
        <div class="card ai-trigger">
          <div>
            <h2 class="section-title">AI 智能分析</h2>
            <p class="ai-desc">基于近 5 年高引用代表性论文（≤25 篇），生成研究方向分析与约 500 字中文综述</p>
          </div>
          <el-button
            type="primary"
            size="large"
            :loading="aiLoading"
            :disabled="aiDone"
            @click="runAI"
          >
            {{ aiLoading ? 'AI 分析中…' : aiDone ? '已生成' : '生成 AI 分析' }}
          </el-button>
        </div>
        <el-alert
          v-if="aiError"
          :title="aiError"
          type="warning"
          show-icon
          :closable="true"
          @close="aiError = ''"
        />

        <!-- AI 结果 -->
        <template v-if="aiDone">
          <AIAnalysis :result="aiResult" />
          <AIReport :report="report" />
        </template>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Document } from '@element-plus/icons-vue'
import SearchBox from '../components/SearchBox.vue'
import Statistics from '../components/Statistics.vue'
import YearChart from '../components/YearChart.vue'
import CountryChart from '../components/CountryChart.vue'
import KeywordCloud from '../components/KeywordCloud.vue'
import TopPapers from '../components/TopPapers.vue'
import AIAnalysis from '../components/AIAnalysis.vue'
import AIReport from '../components/AIReport.vue'
import {
  aiAnalyze,
  aiReport,
  analyzePapers,
  searchPapers,
  type AIAnalyzeResponse,
  type AnalyzeResponse,
  type Paper,
} from '../api/research'

const props = withDefaults(defineProps<{ initialQuery?: string; initialLimit?: number }>(), {
  initialQuery: '',
  initialLimit: 50,
})
const emit = defineEmits<{ back: [] }>()

const loading = ref(false)
const elapsed = ref(0) // 检索等待秒数（感知优化：慢网环境下让用户知道仍在进行）
let elapsedTimer: ReturnType<typeof setInterval> | undefined
const error = ref('')
const analysis = ref<AnalyzeResponse | null>(null)
const papers = ref<Paper[]>([])
const hitTotal = ref(0)
const currentQuery = ref('')
const searchedLimit = ref(props.initialLimit) // 实际执行的检索量，回显到顶部下拉框
const fromCache = ref(false)

// AI 分析状态
const aiLoading = ref(false)
const aiError = ref('')
const aiResult = ref<AIAnalyzeResponse | null>(null)
const report = ref('')
const aiDone = ref(false)

async function onSearch(query: string, limit: number) {
  loading.value = true
  elapsed.value = 0
  clearInterval(elapsedTimer)
  elapsedTimer = setInterval(() => {
    elapsed.value += 1
  }, 1000)
  error.value = ''
  analysis.value = null
  // 新搜索时重置 AI 状态
  currentQuery.value = query
  searchedLimit.value = limit
  aiDone.value = false
  aiResult.value = null
  report.value = ''
  aiError.value = ''
  try {
    // 1) 搜索 + 批量详情 + 引用数
    const res = await searchPapers(query, limit)
    hitTotal.value = res.total
    papers.value = res.papers
    fromCache.value = !!res.cached
    if (res.papers.length === 0) {
      error.value = '未检索到相关论文，请更换关键词（PubMed 为英文库，请使用英文）'
      return
    }
    // 2) 确定性统计（回传 papers，避免二次请求 PubMed）
    analysis.value = await analyzePapers(res.papers)
  } catch (e: unknown) {
    error.value = extractError(e)
  } finally {
    loading.value = false
    clearInterval(elapsedTimer)
  }
}

function extractError(e: unknown): string {
  if (typeof e === 'object' && e !== null) {
    const resp = (e as { response?: { data?: { detail?: string } } }).response
    if (resp?.data?.detail) return `检索失败：${resp.data.detail}`
    if (e instanceof Error && e.message.includes('timeout')) return '请求超时，PubMed 服务响应较慢，请重试'
  }
  return '网络异常或服务不可用，请稍后重试'
}

async function runAI() {
  if (!papers.value.length || aiLoading.value) return
  aiLoading.value = true
  aiError.value = ''
  try {
    // 方向分析与综述生成并行，共用同一批代表性论文
    const [a, r] = await Promise.all([
      aiAnalyze(currentQuery.value, papers.value),
      aiReport(currentQuery.value, papers.value),
    ])
    aiResult.value = a
    report.value = r
    aiDone.value = true
  } catch (e: unknown) {
    aiError.value = extractError(e).replace('检索失败', 'AI 分析失败')
  } finally {
    aiLoading.value = false
  }
}

// 从首页带关键词进入时自动执行搜索
onMounted(() => {
  if (props.initialQuery.trim()) {
    onSearch(props.initialQuery.trim(), props.initialLimit)
  }
})
</script>

<style scoped>
.header {
  background: #fff;
  border-bottom: 1px solid #e8eaf0;
  padding: 14px 0; /* 水平内边距交给 header-inner，与下方 content 精确对齐 */
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px; /* 与 .content 同样的水平内边距，保证左右边缘对齐 */
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.brand {
  cursor: pointer;
  flex-shrink: 0;
}
.brand .title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #1a2a4f;
  letter-spacing: -0.5px;
}
.brand .accent {
  color: #2f7cf6;
}
.header-inner :deep(.search-box) {
  flex: 1;
  min-width: 300px;
  max-width: none; /* 组件默认限宽 860px 是给首页用的，导航栏里取消以撑满整行、右缘与内容列对齐 */
}
.back-link {
  font-size: 13px;
  color: #909399;
  cursor: pointer;
  flex-shrink: 0;
}
.back-link:hover {
  color: #2f7cf6;
}
.cache-tip {
  margin: 0 0 12px;
  font-size: 12px;
  color: #e6a23c;
}
.content {
  max-width: 1200px;
  margin: 24px auto 0;
  padding: 0 24px 48px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.error-alert {
  border-radius: var(--radius);
}
/* 年份/国家两卡片底边对齐：el-row 已让列等高，卡片再撑满列高 */
.chart-row :deep(.el-col) {
  display: flex;
  flex-direction: column;
}
.chart-row :deep(.el-col) > .card {
  flex: 1;
}
.loading-card {
  padding: 32px;
}
.loading-tip {
  color: #909399;
  font-size: 13px;
  text-align: center;
  margin: 16px 0 0;
}
.ai-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.ai-trigger .section-title {
  margin-bottom: 4px;
}
.ai-desc {
  margin: 0;
  font-size: 13px;
  color: #909399;
}
</style>
