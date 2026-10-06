"""AI 分析接口：POST /api/ai/analyze（研究方向）与 POST /api/ai/report（中文综述）"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.paper import Paper
from app.services.llm_service import LLMError, analyze_directions, generate_report

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AIRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    papers: list[Paper] = Field(max_length=500)


@router.post("/analyze")
async def ai_analyze(req: AIRequest) -> dict:
    try:
        result = await analyze_directions(req.query, req.papers)
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return result.model_dump()


@router.post("/report")
async def ai_report(req: AIRequest) -> dict:
    try:
        report = await generate_report(req.query, req.papers)
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"report": report}
