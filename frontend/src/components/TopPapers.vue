<template>
  <div class="card">
    <h2 class="section-title">
      近 5 年高影响力论文 Top {{ papers.length }}
      <el-tooltip
        content="影响力指标为真实引用次数，来自 NIH iCite API（PubMed 不提供 JCR 影响因子）"
        placement="top"
      >
        <el-icon class="info-icon"><InfoFilled /></el-icon>
      </el-tooltip>
    </h2>
    <p class="note">
      筛选 {{ recentStart }} 年以来的论文，按引用次数降序；点击标题跳转 PubMed 原文
      <template v-if="!citationAvailable">（iCite 引用数据暂不可用，当前按年份排序展示）</template>
    </p>

    <el-table :data="pageData" stripe class="paper-table">
      <el-table-column label="#" width="56" align="center">
        <template #default="{ $index }">
          <span class="rank" :class="{ top3: rankOf($index) <= 3 }">{{ rankOf($index) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="标题" min-width="320">
        <template #default="{ row }">
          <a :href="`https://pubmed.ncbi.nlm.nih.gov/${row.pmid}/`" target="_blank" class="paper-link">
            {{ row.title }}
          </a>
        </template>
      </el-table-column>
      <el-table-column prop="year" label="年份" width="70" align="center" />
      <el-table-column label="期刊" width="180">
        <template #default="{ row }">
          <span class="journal" :title="row.journal">{{ row.journal || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="作者" width="180">
        <template #default="{ row }">
          <span class="authors">{{ formatAuthors(row.authors) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="引用数" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.citation_count != null" :type="row.citation_count >= 100 ? 'danger' : 'info'" size="small" effect="plain">
            {{ row.citation_count }}
          </el-tag>
          <span v-else class="na">N/A</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="papers.length"
      layout="total, prev, pager, next"
      background
      class="pager"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import type { Paper } from '../api/research'

const props = defineProps<{
  papers: Paper[]
  citationAvailable: boolean
  recentStart: number
}>()

const page = ref(1)
const pageSize = 10

const pageData = computed(() =>
  props.papers.slice((page.value - 1) * pageSize, page.value * pageSize)
)

function rankOf(index: number): number {
  return (page.value - 1) * pageSize + index + 1
}

function formatAuthors(authors: string[]): string {
  if (!authors.length) return '—'
  return authors.length > 2 ? `${authors.slice(0, 2).join(', ')} 等` : authors.join(', ')
}
</script>

<style scoped>
.info-icon {
  color: #c0c4cc;
  cursor: help;
  font-size: 14px;
}
.note {
  margin: -8px 0 12px;
  font-size: 12px;
  color: #c0c4cc;
}
.paper-table {
  width: 100%;
}
.paper-link {
  color: #1a2a4f;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.4;
}
.paper-link:hover {
  color: #2f7cf6;
  text-decoration: underline;
}
.rank {
  color: #909399;
  font-weight: 600;
}
.rank.top3 {
  color: #f56c6c;
}
.journal,
.authors {
  font-size: 12px;
  color: #606266;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.na {
  color: #c0c4cc;
  font-size: 12px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
