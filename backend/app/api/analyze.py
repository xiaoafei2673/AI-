"""统计分析接口：POST /api/analyze（纯 Python 确定性统计，不经 LLM）"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.paper import Paper
from app.services.analysis_service import analyze_papers
from app.services.icite_service import fill_citations

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    # 前端回传 /api/search 拿到的论文列表，避免二次请求 PubMed
    papers: list[Paper] = Field(max_length=500)


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> dict:
    papers = req.papers
    # 若引用数全空则补查一次 iCite（搜索时已填充过则跳过）
    if papers and not any(p.citation_count is not None for p in papers):
        await fill_citations(papers)
    return analyze_papers(papers)
