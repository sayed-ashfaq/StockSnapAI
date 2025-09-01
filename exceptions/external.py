from typing import Optional


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