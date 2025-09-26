from __future__ import annotations
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    sqlite_path: str = os.getenv("SQLITE_PATH", ".data/memory.sqlite")
    system_prompt: str = os.getenv(
        "SYSTEM_PROMPT",
        "You are a helpful and concise assistant."
    )

settings = Settings()
