"""LLM 服务：调用 OpenAI 兼容接口（默认 DeepSeek），做研究方向分析与中文综述。

原则：
- 只向模型提供筛选后的代表性论文（近5年按引用数 Top N），控制上下文长度
- 结构化输出用 response_format=json_object + Pydantic 校验，解析失败走降级
- 模型返回的 evidence_pmids 必须属于输入集合，防止编造引用
"""
import json
import logging
from datetime import datetime

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.models.paper import Paper

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM 未配置/调用失败/输出校验失败。"""


_client = httpx.AsyncClient(timeout=90)

MAX_PAPERS = 25  # 提交给模型的代表性论文数量上限
ABSTRACT_CHARS = 600  # 单篇摘要截断长度，控制 token


class Direction(BaseModel):
    name: str
    description: str
    evidence_pmids: list[str] = Field(default_factory=list)


class DirectionResult(BaseModel):
    directions: list[Direction] = Field(default_factory=list)
    hotspots: list[str] = Field(default_factory=list)
    future_directions: list[str] = Field(default_factory=list)


def pick_representative(papers: list[Paper], n: int = MAX_PAPERS) -> list[Paper]:
    """代表性论文 = 近 5 年按引用数降序 Top N；不足时用全部论文补齐。"""
    recent_start = datetime.now().year - 4
    recent = [p for p in papers if p.year and p.year >= recent_start]
    ranked = sorted(recent, key=lambda p: (p.citation_count or 0), reverse=True)
    picked = ranked[:n]
    if len(picked) < n:  # 近5年不足时，用其余论文按引用数补齐
        rest = [p for p in papers if p not in picked]
        rest.sort(key=lambda p: (p.citation_count or 0), reverse=True)
        picked += rest[: n - len(picked)]
    return picked


def _format_papers(papers: list[Paper]) -> str:
    """格式化为紧凑文本块供 prompt 使用。"""
    lines = []
    for p in papers:
        lines.append(
            f"PMID: {p.pmid} | {p.year or 'N/A'} | {p.title}\n"
            f"摘要: {p.abstract[:ABSTRACT_CHARS]}\n"
            f"关键词: {', '.join((p.keywords + p.mesh_terms)[:8])}"
        )
    return "\n\n".join(lines)


async def _chat(system: str, user: str, json_mode: bool = False) -> str:
    if not settings.llm_api_key:
        raise LLMError("未配置 LLM_API_KEY，请在 backend/.env 中配置后重启服务")
    payload: dict = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        resp = await _client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise LLMError(f"LLM 服务连接失败: {e}") from e
    if resp.status_code != 200:
        raise LLMError(f"LLM 服务返回 {resp.status_code}: {resp.text[:200]}")
    try:
        return resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"LLM 响应格式异常: {e}") from e


def _parse_json(text: str) -> dict:
    """容错解析：剥掉 ```json 围栏后 json.loads。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned)


async def analyze_directions(query: str, papers: list[Paper]) -> DirectionResult:
    """研究方向分析：返回结构化 JSON，PMID 证据经输入集合过滤。"""
    picked = pick_representative(papers)
    valid_pmids = {p.pmid for p in picked}
    system = (
        "你是科研文献分析助手。只能基于用户提供的论文信息进行总结，"
        "严禁编造论文、数据或 PMID；evidence_pmids 必须从提供论文的 PMID 中选取。"
    )
    user = (
        f"检索主题:{query}\n\n以下是 {len(picked)} 篇代表性论文:\n\n{_format_papers(picked)}\n\n"
        "请输出 JSON(不要输出其他内容):\n"
        '{"directions": [{"name": "研究方向名称", "description": "50字内说明", '
        '"evidence_pmids": ["PMID"...]}], "hotspots": ["研究热点"...], '
        '"future_directions": ["未来方向"...]}\n'
        "directions 3~6 个，hotspots 与 future_directions 各 3~5 条，均用中文。"
    )
    raw = await _chat(system, user, json_mode=True)
    try:
        result = DirectionResult.model_validate(_parse_json(raw))
    except (ValidationError, json.JSONDecodeError) as e:
        raise LLMError(f"LLM 输出校验失败: {e}") from e
    # 幻觉过滤：只保留真实输入过的 PMID
    for d in result.directions:
        d.evidence_pmids = [p for p in d.evidence_pmids if p in valid_pmids]
    return result


async def generate_report(query: str, papers: list[Paper]) -> str:
    """基于代表性论文摘要生成约 500 字中文综述（Markdown 分点）。"""
    picked = pick_representative(papers)
    valid_pmids = {p.pmid for p in picked}
    system = (
        "你是科研文献综述撰写助手。只能基于用户提供的论文摘要撰写，"
        "严禁编造论文、数据、结论或 PMID。"
    )
    user = (
        f"检索主题:{query}\n\n以下是 {len(picked)} 篇代表性论文:\n\n{_format_papers(picked)}\n\n"
        "请基于以上论文撰写中文综述,Markdown 格式分点呈现,正文严格控制在 500~600 字(不含参考文献),包含以下小节:\n"
        "1. **研究背景与领域概况**\n2. **主要研究方向**\n3. **研究热点**\n"
        "4. **当前研究进展**\n5. **未来研究方向**\n6. **参考文献**(列出引用到的 PMID，"
        "只能使用上述论文中出现过的 PMID)\n"
        "直接输出 Markdown 正文，不要输出额外说明。"
    )
    report = await _chat(system, user)
    # 简单防幻觉检查:报告中出现的 PMID 若不在输入集合则剔除该行引用
    for pmid in _extract_pmids(report):
        if pmid not in valid_pmids:
            report = report.replace(pmid, "")
    return report


def _extract_pmids(text: str) -> set[str]:
    import re

    return set(re.findall(r"\b\d{7,9}\b", text))
