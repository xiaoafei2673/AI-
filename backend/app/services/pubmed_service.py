"""PubMed E-utilities 数据源：ESearch 检索 → EFetch 批量取详情 → XML 解析为 Paper。

要点：
- EFetch 批量请求（逗号拼接多个 PMID），单批 200 篇，禁止逐篇请求；
- httpx 超时 + 429 限流退避重试，失败统一抛 PubMedError；
- country 为简化解析：第一作者 affiliation 词边界匹配国家名单，匹配不到为 None。
"""
import asyncio
import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.core.config import settings
from app.models.paper import Paper

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EFETCH_BATCH_SIZE = 200  # NCBI 建议单批不超过 200
TIMEOUT = httpx.Timeout(30.0)
MAX_RETRY = 5  # 本机网络直连 NCBI 偶发 ConnectError（约 1/5 概率），重试即可成功

# 模块级共享 client：连接复用（keep-alive），减少新建连接次数以降低失败率
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        # 显式声明 gzip：EFetch 的 XML 压缩比约 8~10 倍，跨洋传输时间大头直接砍掉
        _client = httpx.AsyncClient(
            timeout=TIMEOUT, headers={"Accept-Encoding": "gzip, deflate"}
        )
    return _client


class PubMedError(Exception):
    """PubMed 接口调用失败（网络/限流/数据异常），由 API 层统一转 502。"""


# 国家/地区名单：长名在前优先匹配；value 为归一化后的展示名
COUNTRY_MAP: dict[str, str] = {
    "United States of America": "United States",
    "United States": "United States",
    "USA": "United States",
    "United Kingdom": "United Kingdom",
    "UK": "United Kingdom",
    "England": "United Kingdom",
    "Scotland": "United Kingdom",
    "South Korea": "South Korea",
    "Korea": "South Korea",
    "Hong Kong": "Hong Kong",
    "Taiwan": "Taiwan",
    "China": "China",
    "Japan": "Japan",
    "Germany": "Germany",
    "France": "France",
    "Italy": "Italy",
    "Spain": "Spain",
    "Canada": "Canada",
    "Australia": "Australia",
    "Netherlands": "Netherlands",
    "Sweden": "Sweden",
    "Switzerland": "Switzerland",
    "Belgium": "Belgium",
    "Denmark": "Denmark",
    "Norway": "Norway",
    "Finland": "Finland",
    "Poland": "Poland",
    "Austria": "Austria",
    "Israel": "Israel",
    "Russia": "Russia",
    "India": "India",
    "Brazil": "Brazil",
    "Turkey": "Turkey",
    "Iran": "Iran",
    "Singapore": "Singapore",
    "Saudi Arabia": "Saudi Arabia",
}
# 预编译：按 key 长度降序，词边界 + 忽略大小写，避免 India 误中 Indiana
_COUNTRY_PATTERNS = [
    (re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE), v)
    for k, v in sorted(COUNTRY_MAP.items(), key=lambda kv: -len(kv[0]))
]


def extract_country(affiliation: str | None) -> str | None:
    """从作者单位字符串中解析国家/地区（简化方案，解析不出返回 None）。"""
    if not affiliation:
        return None
    for pattern, name in _COUNTRY_PATTERNS:
        if pattern.search(affiliation):
            return name
    return None


def _auth_params() -> dict[str, str]:
    """可选的 NCBI 认证参数，配置后可提高限流额度。"""
    params: dict[str, str] = {}
    if settings.pubmed_email:
        params["email"] = settings.pubmed_email
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key
    return params


async def _request_with_retry(method: str, url: str, **kwargs) -> httpx.Response:
    """带退避重试的 HTTP 请求（429 限流 + 连接级错误），最终失败抛 PubMedError。"""
    last_err: Exception | None = None
    for attempt in range(MAX_RETRY):
        try:
            resp = await _get_client().request(method, url, **kwargs)
            if resp.status_code == 429:  # NCBI 限流
                wait = 1.5 * (attempt + 1)
                logger.warning("PubMed 限流(429)，%.1fs 后第 %d 次重试", wait, attempt + 1)
                await asyncio.sleep(wait)
                continue
            if 400 <= resp.status_code < 500:  # 其余 4xx（如 413 URL 过长）重试无意义，直接失败
                raise PubMedError(f"请求被拒（HTTP {resp.status_code}）: {resp.text[:200]}")
            resp.raise_for_status()
            return resp
        except httpx.HTTPError as e:
            last_err = e
            logger.warning(
                "PubMed 请求异常(第 %d/%d 次): %s: %s",
                attempt + 1, MAX_RETRY, type(e).__name__, e,
            )
            await asyncio.sleep(1.0 * (attempt + 1))
    err_msg = f"{type(last_err).__name__}: {last_err}" if last_err else "限流，请稍后重试"
    raise PubMedError(f"PubMed 请求失败（已重试 {MAX_RETRY} 次）: {err_msg}")


async def esearch(query: str, limit: int) -> tuple[int, list[str]]:
    """ESearch：返回 (命中总数, PMID 列表)。"""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": limit,
        "sort": "relevance",
        **_auth_params(),
    }
    resp = await _request_with_retry("GET", f"{EUTILS_BASE}/esearch.fcgi", params=params)
    try:
        result = resp.json().get("esearchresult", {})
        return int(result.get("count", 0)), list(result.get("idlist", []))
    except (ValueError, TypeError) as e:
        raise PubMedError(f"ESearch 返回数据解析失败: {e}") from e


async def efetch(pmids: list[str]) -> str:
    """EFetch：一批 PMID 一次请求，返回 XML 文本。"""
    params = {"db": "pubmed", "retmode": "xml", **_auth_params()}
    data = {"id": ",".join(pmids)}
    resp = await _request_with_retry("POST", f"{EUTILS_BASE}/efetch.fcgi", params=params, data=data)
    return resp.text


def _text(elem: ET.Element | None) -> str:
    """取元素全部文本（含内联标签内的文字）。"""
    return "".join(elem.itertext()).strip() if elem is not None else ""


def _parse_year(article: ET.Element) -> int | None:
    """年份优先级：ArticleDate > JournalIssue PubDate Year > MedlineDate 正则。"""
    year = article.findtext(".//ArticleDate/Year") or article.findtext(
        ".//JournalIssue/PubDate/Year"
    )
    if year and year.isdigit():
        return int(year)
    medline_date = article.findtext(".//JournalIssue/PubDate/MedlineDate") or ""
    m = re.search(r"(19|20)\d{2}", medline_date)
    return int(m.group(0)) if m else None


def parse_papers(xml_text: str) -> list[Paper]:
    """解析 EFetch XML 为 Paper 列表；单篇解析失败跳过，不影响整批。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise PubMedError(f"EFetch XML 解析失败: {e}") from e

    papers: list[Paper] = []
    for art in root.iter("PubmedArticle"):
        try:
            pmid = art.findtext(".//MedlineCitation/PMID") or ""
            if not pmid:
                continue

            # 作者（取前 6 位，超出标注 et al.）与国家解析：
            # 遍历所有作者的全部单位，取第一个能匹配到国家的 affiliation，提高覆盖率
            authors: list[str] = []
            country: str | None = None
            for author in art.findall(".//AuthorList/Author"):
                name = (
                    f"{author.findtext('LastName', '')} {author.findtext('ForeName', '')}".strip()
                    or author.findtext("CollectiveName", "")
                )
                if name:
                    authors.append(name)
                if country is None:
                    for aff_info in author.findall(".//AffiliationInfo"):
                        country = extract_country(aff_info.findtext("Affiliation"))
                        if country:
                            break

            # 摘要：多段 AbstractText 拼接（带小节标签的保留标签）
            abstract_parts = []
            for abst in art.findall(".//Abstract/AbstractText"):
                label, text = abst.get("Label"), _text(abst)
                abstract_parts.append(f"{label}: {text}" if label and text else text)
            # 关键词与 MeSH 词
            keywords = [t for kw in art.findall(".//KeywordList/Keyword") if (t := _text(kw))]
            mesh_terms = [
                t
                for mh in art.findall(".//MeshHeadingList/MeshHeading/DescriptorName")
                if (t := _text(mh))
            ]
            doi = art.findtext(".//PubmedData/ArticleIdList/ArticleId[@IdType='doi']")

            papers.append(
                Paper(
                    pmid=pmid,
                    title=_text(art.find(".//ArticleTitle")),
                    abstract=" ".join(p for p in abstract_parts if p),
                    authors=authors[:6] + (["et al."] if len(authors) > 6 else []),
                    journal=art.findtext(".//Journal/Title", ""),
                    year=_parse_year(art),
                    keywords=keywords,
                    mesh_terms=mesh_terms,
                    doi=doi or None,
                    country=country,
                )
            )
        except Exception as e:  # 单篇异常不中断整批
            logger.warning("跳过解析失败的论文: %s", e)
    return papers


async def fetch_papers(pmids: list[str]) -> list[Paper]:
    """按 PMID 并行分批 EFetch 并解析为 Paper（gather 保序，不改变 ESearch 相关度排名）。

    500 篇 = 3 批并发发出，总耗时 ≈ 单批耗时（NCBI 无 key 限流 3 req/s，3 个并发不超限）；
    单批失败由 _request_with_retry 内部 429/网络退避重试兜底。
    """
    if not pmids:
        return []
    batches = [pmids[i : i + EFETCH_BATCH_SIZE] for i in range(0, len(pmids), EFETCH_BATCH_SIZE)]
    xml_parts = await asyncio.gather(*(efetch(b) for b in batches))
    papers: list[Paper] = []
    for xml in xml_parts:
        papers.extend(parse_papers(xml))
    logger.info("EFetch 并行 %d 批完成，共解析 %d 篇", len(batches), len(papers))
    return papers
