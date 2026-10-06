"""确定性统计分析：纯 Python（Counter/排序/过滤），不使用 LLM 计算任何基础统计。"""
import re
from collections import Counter
from datetime import datetime

from app.models.paper import Paper

# 英文通用停用词 + 医学论文高频无意义词
STOPWORDS = set("""
a an the and or of in on for with to from by at as is are was were be been being
we our their its this that these those it it(s) not no but if then than so such
has have had do does did will would should can could
study studies result results method methods conclusion conclusions background
objective purpose aim patient patients subject subjects group groups control
use used using based between among compared however also may can could might
show showed shown found observe observed report reported demonstrate demonstrated
associate associated association analyze analyzed analysis effect effects
include included including treatment treated therapy disease diseases cancer cancers
cell cells human humans mouse mice rat model models data research clinical trial
trials after before during high low level levels increased decreased increase decrease
expression protein proteins gene genes mutation mutations vs via et al respectively
significant significantly more most other others new all both each these those
review reviews introduction discussion
""".split())

# 短语级别的无意义关键词（MeSH/author keywords 里过于宽泛的词）
PHRASE_STOPWORDS = {
    "humans", "animals", "male", "female", "adult", "child", "middle aged", "aged",
    "young adult", "adolescent", "infant", "child, preschool", "retrospective studies",
    "prospective studies", "risk factors", "time factors", "follow-up studies",
    "prognosis", "epidemiology", "etiology", "physiopathology", "complications",
}

_WORD_RE = re.compile(r"[a-z][a-z0-9-]{2,}")


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def analyze_papers(papers: list[Paper], current_year: int | None = None) -> dict:
    """对论文列表做确定性统计，返回结构化结果（字段与前端图表一一对应）。"""
    current_year = current_year or datetime.now().year
    recent_start = current_year - 4  # 近 5 年（含今年）

    total = len(papers)

    # 按年份统计（升序，供趋势图）
    year_counter = Counter(p.year for p in papers if p.year)
    by_year = [{"year": y, "count": c} for y, c in sorted(year_counter.items())]

    # 按国家/地区统计（降序，解析不出的归入 Unknown）
    country_counter = Counter(p.country or "Unknown" for p in papers)
    by_country = [
        {"country": c, "count": n} for c, n in country_counter.most_common()
    ]

    # 高频关键词：① 作者关键词 + MeSH 短语（保留短语形态）② title/abstract 分词
    phrase_counter: Counter[str] = Counter()
    word_counter: Counter[str] = Counter()
    for p in papers:
        for phrase in p.keywords + p.mesh_terms:
            key = phrase.strip().lower().rstrip(".")
            if key and key not in PHRASE_STOPWORDS and len(key) > 2:
                phrase_counter[key] += 1
        for w in _tokenize(f"{p.title} {p.abstract}"):
            if w not in STOPWORDS:
                word_counter[w] += 1
    # 合并：短语与单词统一排序取 Top 50（词云用）
    merged = phrase_counter + word_counter
    top_keywords = [
        {"word": w, "count": c} for w, c in merged.most_common(50)
    ]

    # 近 5 年论文 & 高影响力 Top 100（按真实引用次数排序，None 视为 0）
    recent_5y = [p for p in papers if p.year and p.year >= recent_start]
    top100 = sorted(
        recent_5y, key=lambda p: (p.citation_count or 0), reverse=True
    )[:100]
    citation_available = any(p.citation_count is not None for p in papers)

    return {
        "total": total,
        "by_year": by_year,
        "by_country": by_country,
        "top_keywords": top_keywords,
        "recent_5y_count": len(recent_5y),
        "year_range": {
            "start": min(year_counter) if year_counter else None,
            "end": max(year_counter) if year_counter else None,
            "recent_start": recent_start,
        },
        "top100": top100,
        "citation_available": citation_available,
    }
