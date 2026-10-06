"""统一论文数据结构：后端所有接口与前端交互的标准模型。"""
from pydantic import BaseModel, Field


class Paper(BaseModel):
    pmid: str
    title: str
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    year: int | None = None
    keywords: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)
    doi: str | None = None
    # 从第一作者 affiliation 简化解析，解析不出为 None
    country: str | None = None
    # 引用次数，来源 NIH iCite API（非 JCR 影响因子）；获取失败为 None
    citation_count: int | None = None
