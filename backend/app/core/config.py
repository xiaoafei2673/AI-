"""应用配置：优先读 backend/.env，不存在时回退 .env.example（内置演示 key，开箱即用）。"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录，保证从任何工作目录启动都能找到配置文件
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
if not ENV_FILE.exists():
    ENV_FILE = BASE_DIR / ".env.example"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )

    # LLM（兼容 OpenAI API 格式）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # PubMed（可选，提高限流额度）
    pubmed_email: str = ""
    pubmed_api_key: str = ""


settings = Settings()
