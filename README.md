# PubMed AI 文献分析助手

输入英文关键词（如 `lung cancer`）→ PubMed 真实检索 → 统计分析 + 可视化图表 + 近 5 年高影响力 Top100 文献 + AI 研究方向总结 + 500 字中文综述。

## 笔试要求逐条实现说明

### 1) 统计相关研究数量、年份、分区、影响因子

| 子项 | 实现方式 | 数据口径 |
|---|---|---|
| 研究数量 | 后端调 PubMed **ESearch** 返回 `count`（全网命中总量，如 lung cancer ≈ 51 万），同时按用户选择的 limit（50/100/200/500）经 **EFetch** 批量拉取论文详情做分析样本 | 真实 PubMed 数据 |
| 年份分布 | 解析 EFetch 返回 XML 中每篇论文的 `PubDate`，Python `Counter` 按年统计 | ECharts 折线图展示，数据全部来自检索样本 |
| 分区 | **PubMed 不提供中科院/JCR 分区数据**，且无免费公开可靠 API。Demo 方案：解析第一作者单位地址（affiliation）中的国家/地区，按国家统计发文量并注明 | ECharts 横向柱状图，解析不出的归入 Unknown 并在图下注明数量 |
| 影响因子 | **PubMed 不提供 JCR Impact Factor，禁止伪造**。Demo 采用 **NIH iCite API** 按 PMID 批量查询**真实引用次数**作为影响力指标 | 界面多处注明「引用数据来自 NIH iCite」；iCite 不可用时降级为 null 并提示 |

### 2) 生成词云、研究方向总结概括、可视化图表

- **词云**：双通道词频统计（纯 Python Counter，不用 LLM 算数），取 Top 50 由 `echarts-wordcloud` 渲染
  - **短语通道**：作者关键词 + MeSH 主题词，保留完整短语形态（如 `lung adenocarcinoma` 不拆散）；归一化（小写 + 去尾部标点）后过滤 21 个短语级宽泛术语（humans / risk factors 等）
  - **单词通道**：title + abstract 正则分词（`[a-z][a-z0-9-]{2,}`，≥3 字符、字母开头、允许连字符，能保留 `pd-l1`、`covid-19`），过滤约 150 个停用词（英文虚词 + 医学论文高频套话 study/patients/results/conclusion 等）
  - **合并排序**：两个 Counter 等权相加（同一术语在关键词与摘要中重复出现时频次自然叠加），`most_common(50)` 降序取前 50，输出 `[{word, count}]`
  - **前端渲染**：`echarts-wordcloud` 圆形布局，字号随词频缩放（13~44px），随机 ±30° 旋转，科研蓝青 8 色系，词超出画布自动丢弃
  - **为什么这样设计**：① 词频是可验证的精确计数，交给 LLM 只会引入不确定性与成本，LLM 只用于方向总结这类真正需要语义理解的任务 ② MeSH/作者关键词是人工标注的多词短语，走单词分词会被拆散丢语义，故必须双通道分离处理 ③ 通用英文停用词表挡不住医学论文套话（study/patients 几乎每篇摘要都有），不加领域层过滤词云会被无意义词霸榜 ④ MeSH 里 humans/male/risk factors 等宽泛术语同理，需独立的短语级停用表 ⑤ 归一化（小写+去标点）避免 `"Lung Cancer"`/`"lung cancer."` 被计成两个词、稀释频次 ⑥ 等权合并是刻意简化——同一术语在关键词与摘要同时出现时频次自然叠加，等于隐性的相关性加成，无需额外权重超参 ⑦ 取 Top 50 是词云可读性的视觉上限，再多的词渲染出来不可读
- **研究方向总结**：筛选**近 5 年按引用数排序的 Top 25 代表性论文**（标题+截断摘要+关键词）提交给 DeepSeek（OpenAI 兼容格式），要求输出结构化 JSON（研究方向/热点/未来方向），Pydantic 校验 + **PMID 幻觉过滤**（证据引用必须属于输入集合）
- **可视化**：ECharts 折线图（年份趋势）、横向柱状图（国家分布）、词云

### 3) 影响力排序，5 年内前 100 文献

- 纯 Python 实现：过滤 `year >= 当前年-4` 的论文，按 `citation_count`（iCite 真实引用数）降序取 Top 100
- 前端 el-table 展示：排名/标题/年份/期刊/作者/引用数，分页浏览，标题点击跳转对应 PubMed 页面
- iCite 不可用时退化为按年份排序并明确提示，不展示伪造数据

### 4) 基于文献摘要生成 500 字中文综述，分点呈现

- **素材来源**：与方向分析共用 `pick_representative()` 选出的同一批 Top 25 代表性论文——近 5 年按 iCite 真实引用数降序，不足 25 篇时用更老的高被引论文补齐。选 25 篇是覆盖面与 token 成本的平衡（500 篇全塞会爆上下文）；按引用数排序保证综述围绕领域主流工作，不跑偏到冷门文献
- **输入压缩**：每篇论文压成三行紧凑文本（`PMID | 年份 | 标题` + 摘要截断 600 字符 + 前 8 个关键词/MeSH 词），25 篇总量控制在可接受的 prompt 规模内
- **Prompt 约束**：system 层红线「严禁编造论文/数据/结论/PMID」；user 层锁结构——六小节（研究背景/主要研究方向/研究热点/当前研究进展/未来研究方向/参考文献）、正文严格 500~600 字、参考文献只能使用输入集合中的 PMID；调用参数 `temperature=0.3` 压低随机性，让综述贴紧输入材料而非自由发挥；此处不用 JSON mode（综述是 Markdown 自由文本，区别于方向分析的结构化输出）
- **结果处理（防幻觉兜底）**：返回后用正则 `\b\d{7,9}\b`（PMID 位数特征）抓出综述中全部疑似 PMID，逐个对照输入论文的 PMID 白名单，不在集合中的直接从文本抹除——提示词约束是第一道防线，代码白名单是第二道，LLM 即使编造引用也到不了用户眼前
- **前端呈现**：接口返回纯 Markdown 字符串（`{"report": ...}`），前端 markdown-it 渲染为分小节排版的综述

## 技术架构

```
Vue3 + TS + Element Plus + ECharts
  │  axios (vite proxy /api → :8000)
  ▼
FastAPI (Python)
  ├── pubmed_service   ESearch 取 PMID → EFetch 批量取 XML → 解析为 Paper
  ├── icite_service    iCite 批量补 citation_count(失败降级)
  ├── analysis_service 纯 Python 统计(不用 LLM 算数)
  └── llm_service      DeepSeek(httpx 直连 OpenAI 兼容接口)
```

**论文统一数据结构**：pmid / title / abstract / authors / journal / year / keywords / mesh_terms / doi / country / citation_count

## 目录结构

```
backend/
  app/
    main.py                  FastAPI 入口 + CORS
    api/    search.py  analyze.py  ai.py
    services/ pubmed_service.py  icite_service.py  analysis_service.py  llm_service.py
    models/ paper.py         Paper 数据结构
    core/   config.py        .env 配置(pydantic-settings)
frontend/
  src/
    views/  ResearchDashboard.vue
    components/ SearchBox Statistics YearChart CountryChart KeywordCloud TopPapers AIAnalysis AIReport
    api/    research.ts
```

## 环境变量

`.env.example` 已内置演示用 DeepSeek key，**解压即用、无需任何配置**；如需换成自己的 key，复制为 `backend/.env` 后修改：

```env
LLM_API_KEY=sk-xxx                      # DeepSeek key（不配置则 AI 功能提示未配置，其余功能正常）
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
PUBMED_EMAIL=                           # 可选，NCBI 建议携带
PUBMED_API_KEY=                         # 可选，提高限流额度 3/s → 10/s
```

## 启动方式

```bash
# 后端(首次: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
cd backend && .venv\Scripts\python -m uvicorn app.main:app --port 8000

# 前端(首次: npm install,需 Node ≥ 14.18)
cd frontend && npx vite --port 5173
```

打开 http://localhost:5173 。API 文档：http://localhost:8000/docs

## API 一览

| 接口 | 说明 |
|---|---|
| `POST /api/search` | `{query, limit}` → ESearch + EFetch 批量(200/批)→ `{total, papers}` |
| `POST /api/analyze` | `{papers}` → 年份/国家/关键词/近5年/Top100 统计(纯 Python) |
| `POST /api/ai/analyze` | `{query, papers}` → 研究方向/热点/未来方向(JSON,Pydantic 校验) |
| `POST /api/ai/report` | `{query, papers}` → 500~600 字中文综述(Markdown) |

前端回传 papers 做分析，避免二次请求 PubMed。

## 数据口径与已知限制

1. **影响因子**:PubMed 无 JCR IF 数据。本项目统一使用 NIH iCite 真实引用次数，界面已注明
2. **分区**:同上,以国家/地区分布替代并注明
3. **国家解析**:取第一作者 affiliation 字符串匹配国家名,约 75% 可解析,其余归 Unknown(简化方案)
4. **检索语言**:PubMed 为英文库,请使用英文关键词
5. **检索样本**:统计与 AI 分析基于 limit 内的样本(最多 500 篇),非全网总量
6. **网络**：直连 NCBI 偶发超时，已内置重试（5 次递增退避）；EFetch 批次与 iCite 引用数并行请求、XML gzip 压缩传输，实测 50 篇约 10 秒、500 篇约 10~20 秒
7. **缓存**:`/api/search` 按「关键词+limit」做进程内内存缓存(TTL 30 分钟),同一检索二次请求秒级返回,重启即清;命中时响应含 `cached: true`,前端显示提示

## 演示流程(3~5 分钟)

0. 首页(OpenAlex 风格):大标题 + 搜索框,可点「试试」快捷词
1. 输入 `lung cancer`,选 200 篇,点搜索 → 自动跳转结果页,说明批量检索与真实数据
2. 统计卡片 + 年份/国家图表 → 说明纯 Python 统计、国家口径
3. 词云 → 说明文本来源与停用词清洗
4. Top100 表格 → 点标题跳 PubMed,说明 iCite 引用数口径(可提及「不伪造影响因子」的决策)
5. 点「生成 AI 分析」→ 方向卡片 + PMID 证据 + 500 字综述,说明代表性论文选择与幻觉过滤
