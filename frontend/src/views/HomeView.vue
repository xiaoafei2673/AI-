<template>
  <div class="home">
    <!-- 顶部导航：与结果页同宽（1200px + 24px 内边距）、同款白色底 + 细分隔线 -->
    <nav class="nav">
      <div class="nav-inner">
        <div class="brand">
          <span class="logo">PubMed<span class="logo-accent">AI</span></span>
          <span class="nav-hint">文献分析助手</span>
        </div>
        <div class="nav-links">
          <a class="nav-link">关于</a>
          <a class="nav-link">使用指南</a>
          <el-avatar :size="32" class="nav-avatar">
            <el-icon :size="18"><UserFilled /></el-icon>
          </el-avatar>
        </div>
      </div>
    </nav>

    <!-- 中央 Hero 区 -->
    <main class="hero">
      <h1 class="hero-title">揭开文献研究的<br />数据面纱</h1>
      <p class="hero-subtitle">
        基于 PubMed 真实数据，一键获得统计分析、关键词词云、<br />
        高影响力文献榜单与 AI 生成的研究方向综述。
      </p>
      <div class="hero-search">
        <SearchBox :loading="loading" @search="onSearch" />
      </div>
      <p v-if="loading" class="hero-tip">正在检索 PubMed，大批量约需 10~60 秒…</p>
      <div class="examples">
        <span class="examples-label">试试：</span>
        <a
          v-for="w in ['lung cancer', 'crispr', 'alzheimer disease']"
          :key="w"
          class="example-word"
          @click="onSearch(w, 50)"
        >{{ w }}</a>
      </div>
    </main>

    <footer class="footer">数据来源：PubMed E-utilities · NIH iCite · DeepSeek</footer>
  </div>
</template>

<script setup lang="ts">
import { UserFilled } from '@element-plus/icons-vue'
import SearchBox from '../components/SearchBox.vue'

defineProps<{ loading: boolean }>()
const emit = defineEmits<{ search: [query: string, limit: number] }>()

function onSearch(query: string, limit: number) {
  emit('search', query, limit)
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
}
/* 导航：宽度与结果页 header-inner / content 一致，左右边缘对齐 */
.nav {
  background: #fff;
  border-bottom: 1px solid #e8eaf0;
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.logo {
  font-size: 22px;
  font-weight: 800;
  color: #1a2a4f;
  letter-spacing: -0.5px;
}
.logo-accent {
  color: #2f7cf6;
}
.nav-hint {
  font-size: 13px;
  color: #909399;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}
.nav-link {
  font-size: 13px;
  color: #606266;
  cursor: pointer;
}
.nav-link:hover {
  color: #2f7cf6;
}
.nav-avatar {
  background: #f0f2f5;
  color: #909399;
}
.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px 80px;
  text-align: center;
}
.hero-title {
  font-size: 52px;
  font-weight: 800;
  color: #1a2a4f; /* 与结果页标题同色，统一视觉体系 */
  line-height: 1.25;
  margin: 0 0 24px;
  letter-spacing: 1px;
}
.hero-subtitle {
  font-size: 16px;
  color: #606266;
  line-height: 1.8;
  margin: 0 0 40px;
}
.hero-search {
  display: flex;
  justify-content: center;
  width: 100%;
}
.hero-search :deep(.search-box) {
  max-width: 720px;
}
/* 胶囊化：输入框 + 下拉框 + 按钮三件套统一圆角与投影 */
.hero-search :deep(.el-input__wrapper),
.hero-search :deep(.el-select__wrapper) {
  border-radius: 24px;
  padding: 4px 16px;
  box-shadow: 0 2px 12px rgba(26, 42, 79, 0.08);
  min-height: 40px;
}
.hero-search :deep(.search-btn) {
  border-radius: 24px;
}
.hero-tip {
  margin: 16px 0 0;
  font-size: 13px;
  color: #909399;
}
.examples {
  margin-top: 28px;
  font-size: 13px;
  color: #909399;
}
.example-word {
  color: #2f7cf6;
  margin-left: 12px;
  cursor: pointer;
}
.example-word:hover {
  text-decoration: underline;
}
.footer {
  text-align: center;
  padding: 20px;
  font-size: 12px;
  color: #c0c4cc;
}
@media (max-width: 640px) {
  .hero-title {
    font-size: 34px;
  }
  .nav-links .nav-link {
    display: none; /* 窄屏只留 logo 与头像 */
  }
}
</style>
