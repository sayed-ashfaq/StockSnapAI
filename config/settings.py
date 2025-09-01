import os
from datetime import timedelta
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    # News API Settings
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"
    NEWS_DAYS_BACK: int = 3
    NEWS_PAGE_SIZE: int = 3
    NEWS_LANGUAGE: str = "en"
    NEWS_SORT_BY: str = "publishedAt"

    # Web Scraping Settings
    SCRAPING_TIMEOUT: int = 30
    SCRAPING_MAX_RETRIES: int = 3
    SCRAPING_DELAY: float = 1.0
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Rate Limiting
    NEWS_API_RATE_LIMIT: int = 1000  # requests per day
    SCRAPING_RATE_LIMIT: int = 10  # requests per minute

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()