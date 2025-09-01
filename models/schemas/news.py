from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, validator


class NewsArticle(BaseModel):
    """Schema for a news article from NewsAPI"""
    title: str
    description: Optional[str] = None
    url: HttpUrl
    published_at: datetime
    source_name: str
    author: Optional[str] = None

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Title cannot be empty')
        return v.strip()


class ScrapedArticle(BaseModel):
    """Schema for scraped article content"""
    url: str
    title: str
    content: str
    scraped_at: datetime
    success: bool
    error_message: Optional[str] = None


class NewsResponse(BaseModel):
    """Schema for processed news response"""
    ticker: str
    headlines_string: str
    full_articles_string: str
    articles_count: int
    fetch_timestamp: datetime
    processing_errors: List[str] = []


# File: app/exceptions/external.py
class NewsAPIError(Exception):
    """Exception raised for NewsAPI errors"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class WebScrapingError(Exception):
    """Exception raised for web scraping errors"""

    def __init__(self, message: str, url: Optional[str] = None):
        self.message = message
        self.url = url
        super().__init__(self.message)


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, service: str, retry_after: Optional[int] = None):
        self.service = service
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {service}")