from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    xai_api_key: Optional[str] = None

    research_cache_ttl_days: int = 7
    research_max_companies: int = 20

    @property
    def data_dir(self) -> Path:
        return ROOT / "data"

    @property
    def cache_dir(self) -> Path:
        return ROOT / "data" / "cache"

    @property
    def reports_dir(self) -> Path:
        return ROOT / "reports"

    @property
    def companies_file(self) -> Path:
        return ROOT / "data" / "companies.json"

    @property
    def research_history_file(self) -> Path:
        return ROOT / "data" / "research_history.json"


settings = Settings()
