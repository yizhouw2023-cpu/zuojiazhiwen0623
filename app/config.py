"""Application configuration via environment variables."""
from __future__ import annotations
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    secret_key: str = "change-me-to-random-string"
    database_url: str = "sqlite+aiosqlite:///app/data/fingerprint.db"
    max_history_entries: int = 50

    # Font path for word cloud
    font_path: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
