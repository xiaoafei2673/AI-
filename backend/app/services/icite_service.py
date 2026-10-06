"""NIH iCite API：按 PMID 批量查询真实引用次数（citation_count）。

说明：PubMed 本身不提供引用数/影响因子，citation_count 来自 NIH iCite 公开 API。
该服务不可用或超时时整体降级为 None，不影响主流程。
"""
import asyncio
import logging

from app.models.paper import Paper
from app.services.pubmed_service import PubMedError, _request_with_retry

logger = logging.getLogger(__name__)

ICITE_URL = "https://icite.od.nih.gov/api/pubs"
# GET 查询串有长度上限（实测 500 个 PMID 触发 413），单批 200 个 URL 约 2KB 安全
BATCH_SIZE = 200


async def _get_batch(batch: list[str]) -> dict[str, int]:
    resp = await _request_with_retry("GET", ICITE_URL, params={"pmids": ",".join(batch)})
    out: dict[str, int] = {}
    for item in resp.json().get("data", []):
        pmid, count = str(item.get("pmid", "")), item.get("citation_count")
        if pmid and count is not None:
            out[pmid] = int(count)
    return out


async def get_citations(pmids: list[str]) -> dict[str, int]:
    """批量并行查询引用次数，返回 {pmid: citation_count}；任何失败都返回 {} 降级。"""
    if not pmids:
        return {}
    batches = [pmids[i : i + BATCH_SIZE] for i in range(0, len(pmids), BATCH_SIZE)]
    try:
        parts = await asyncio.gather(*(_get_batch(b) for b in batches))
    except (PubMedError, ValueError, TypeError) as e:
        logger.warning("iCite 引用数获取失败，降级为空: %s", e)
        return {}
    result: dict[str, int] = {}
    for part in parts:
        result.update(part)
    return result


def apply_citations(papers: list[Paper], citations: dict[str, int]) -> bool:
    """把引用数填充到 papers.citation_count，返回是否成功拿到数据。"""
    for p in papers:
        p.citation_count = citations.get(p.pmid)
    if citations:
        logger.info("iCite 填充引用数: %d/%d 篇有数据", len(citations), len(papers))
    return bool(citations)


async def fill_citations(papers: list[Paper]) -> bool:
    """查询并就地填充引用数（供 /api/analyze 补数用），失败自动降级为 None。"""
    return apply_citations(papers, await get_citations([p.pmid for p in papers]))
