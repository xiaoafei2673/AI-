<template>
  <div class="card">
    <h2 class="section-title">AI 研究方向分析</h2>
    <p class="note">基于近 5 年高引用代表性论文（≤25 篇）由 LLM 归纳，PMID 证据可点击跳转</p>

    <template v-if="result">
      <!-- 研究方向 -->
      <div class="directions">
        <div v-for="d in result.directions" :key="d.name" class="direction-item">
          <div class="direction-name">{{ d.name }}</div>
          <div class="direction-desc">{{ d.description }}</div>
          <div v-if="d.evidence_pmids.length" class="evidence">
            <span class="evidence-label">证据:</span>
            <a
              v-for="pmid in d.evidence_pmids"
              :key="pmid"
              :href="`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`"
              target="_blank"
              class="pmid-tag"
            >{{ pmid }}</a>
          </div>
        </div>
      </div>

      <!-- 热点 + 未来方向 -->
      <el-row :gutter="16" class="tags-row">
        <el-col :xs="24" :md="12">
          <div class="tags-block">
            <div class="tags-title">研究热点</div>
            <el-tag v-for="h in result.hotspots" :key="h" type="danger" effect="plain" class="tag">
              {{ h }}
            </el-tag>
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <div class="tags-block">
            <div class="tags-title">未来方向</div>
            <el-tag v-for="f in result.future_directions" :key="f" type="success" effect="plain" class="tag">
              {{ f }}
            </el-tag>
          </div>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else description="点击上方「生成 AI 分析」按钮" :image-size="60" />
  </div>
</template>

<script setup lang="ts">
import type { AIAnalyzeResponse } from '../api/research'

defineProps<{ result: AIAnalyzeResponse | null }>()
</script>

<style scoped>
.note {
  margin: -8px 0 16px;
  font-size: 12px;
  color: #c0c4cc;
}
.directions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.direction-item {
  padding: 12px 16px;
  border-left: 3px solid #2f7cf6;
  background: #f7faff;
  border-radius: 0 8px 8px 0;
}
.direction-name {
  font-weight: 600;
  color: #1a2a4f;
  font-size: 14px;
}
.direction-desc {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.evidence {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.evidence-label {
  font-size: 12px;
  color: #909399;
}
.pmid-tag {
  font-size: 12px;
  color: #2f7cf6;
  background: #ecf3ff;
  padding: 1px 8px;
  border-radius: 10px;
  text-decoration: none;
}
.pmid-tag:hover {
  background: #2f7cf6;
  color: #fff;
}
.tags-row {
  margin-top: 16px;
}
.tags-block {
  padding: 12px 16px;
  background: #fafbfc;
  border-radius: 8px;
}
.tags-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}
.tag {
  margin: 0 6px 6px 0;
}
</style>
