import axios from 'axios'

/** 与后端 Paper 模型一致的数据结构 */
export interface Paper {
  pmid: string
  title: string
  abstract: string
  authors: string[]
  journal: string
  year: number | null
  keywords: string[]
  mesh_terms: string[]
  doi: string | null
  country: string | null
  citation_count: number | null
}

export interface SearchResponse {
  total: number
  papers: Paper[]
  cached?: boolean
}

export interface YearStat { year: number; count: number }
export interface CountryStat { country: string; count: number }
export interface KeywordFreq { word: string; count: number }

export interface AnalyzeResponse {
  total: number
  by_year: YearStat[]
  by_country: CountryStat[]
  top_keywords: KeywordFreq[]
  recent_5y_count: number
  year_range: { start: number | null; end: number | null; recent_start: number }
  top100: Paper[]
  citation_available: boolean
}

const http = axios.create({
  baseURL: '/api',
  timeout: 180000, // PubMed 大批量检索可能较慢
})

/** 搜索 PubMed 并批量获取论文详情（含引用数） */
export async function searchPapers(query: string, limit: number): Promise<SearchResponse> {
  const { data } = await http.post<SearchResponse>('/search', { query, limit })
  return data
}

/** 对已获取的论文做确定性统计分析 */
export async function analyzePapers(papers: Paper[]): Promise<AnalyzeResponse> {
  const { data } = await http.post<AnalyzeResponse>('/analyze', { papers })
  return data
}

export interface Direction {
  name: string
  description: string
  evidence_pmids: string[]
}

export interface AIAnalyzeResponse {
  directions: Direction[]
  hotspots: string[]
  future_directions: string[]
}

/** AI 研究方向分析（基于代表性论文，需配置 LLM_API_KEY） */
export async function aiAnalyze(query: string, papers: Paper[]): Promise<AIAnalyzeResponse> {
  const { data } = await http.post<AIAnalyzeResponse>('/ai/analyze', { query, papers })
  return data
}

/** AI 生成约 500 字中文综述（Markdown） */
export async function aiReport(query: string, papers: Paper[]): Promise<string> {
  const { data } = await http.post<{ report: string }>('/ai/report', { query, papers })
  return data.report
}
