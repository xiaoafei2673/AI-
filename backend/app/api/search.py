"""搜索接口：POST /api/search"""
import asyncio
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.paper import Paper
from app.services.icite_service import apply_citations, get_citations
from app.services.pubmed_service import PubMedError, esearch, fetch_papers

router = APIRouter(prefix="/api", tags=["search"])

# 简单内存缓存:key="query:limit" → (写入时间戳, 响应数据),进程内有效、重启即清
CACHE_TTL = 1800  # 30 分钟
_cache: dict[str, tuple[float, "SearchResponse"]] = {}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=50, ge=1, le=500)


class SearchResponse(BaseModel):
    total: int  # PubMed 命中总数（可能大于实际返回篇数）
    papers: list[Paper]
    cached: bool = False  # 是否命中缓存


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    key = f"{req.query.strip().lower()}:{req.limit}"

    # 命中缓存且未过期 → 直接返回(演示时同一关键词第二次秒出)
    if key in _cache:
        ts, resp = _cache[key]
        if time.time() - ts < CACHE_TTL:
            resp.cached = True
            return resp
        del _cache[key]

    try:
        total, pmids = await esearch(req.query.strip(), req.limit)
        # EFetch 详情与 iCite 引用数互不依赖（都只需 PMID），并行发起，总耗时取两者较大值
        papers, citations = await asyncio.gather(fetch_papers(pmids), get_citations(pmids))
    except PubMedError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    apply_citations(papers, citations)  # iCite 失败时返回 {}，自动降级为 None

    resp = SearchResponse(total=total, papers=papers)
    _cache[key] = (time.time(), resp)
    return resp
