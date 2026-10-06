"""FastAPI 入口：CORS、路由注册、健康检查。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, analyze, search

app = FastAPI(title="PubMed AI 文献分析助手", version="0.1.0")

# 允许前端 Vite dev server 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(analyze.router)
app.include_router(ai.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
