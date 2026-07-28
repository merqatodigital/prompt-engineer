from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./prompt_engineer.db")
    app_secret: str = os.getenv("APP_SECRET", "development-only-change-me")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    prompts_chat_mcp_url: str = os.getenv("PROMPTS_CHAT_MCP_URL", "https://prompts.chat/api/mcp")
    prompts_chat_api_key: str = os.getenv("PROMPTS_CHAT_API_KEY", "")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


@lru_cache
def get_settings() -> Settings:
    return Settings()
