import requests
from bs4 import BeautifulSoup
import time
from typing import Optional
from urllib.parse import urljoin, urlparse
from config.settings import settings
from exceptions.external import WebScrapingError
from utils.text_processing import TextProcessor
from models.schemas.news import ScrapedArticle
from datetime import datetime
from log_utils import GLOBAL_LOGGER as logger


class WebScraper:
    """Web scraper for extracting full article content"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self._last_request_time = 0

    def _rate_limit(self):
        """Implement rate limiting for web scraping"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < settings.SCRAPING_DELAY:
            sleep_time = settings.SCRAPING_DELAY - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def scrape_article(self, url: str, title: str = "") -> ScrapedArticle:
        """
        Scrape full content from a single article URL

        Args:
            url: Article URL to scrape
            title: Article title (for reference)

        Returns:
            ScrapedArticle object with content and metadata
        """
        if not self._is_valid_url(url):
            return ScrapedArticle(
                url=url,
                title=title,
                content="",
                scraped_at=datetime.now(),
                success=False,
                error_message="Invalid URL format"
            )

        self._rate_limit()

        for attempt in range(settings.SCRAPING_MAX_RETRIES):
            try:
                logger.info(f"Scraping article: {url} (attempt {attempt + 1})")

                response = self.session.get(
                    url,
                    timeout=settings.SCRAPING_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()

                # Extract article content
                content = TextProcessor.extract_article_content(response.text)

                if len(content.strip()) < 100:  # Minimum content threshold
                    raise WebScrapingError("Insufficient content extracted")

                logger.info(f"Successfully scraped {len(content)} characters from {url}")

                return ScrapedArticle(
                    url=url,
                    title=title,
                    content=content,
                    scraped_at=datetime.now(),
                    success=True
                )

            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                logger.warning(f"Scraping attempt {attempt + 1} failed for {url}: {error_msg}")

                if attempt == settings.SCRAPING_MAX_RETRIES - 1:
                    return ScrapedArticle(
                        url=url,
                        title=title,
                        content="",
                        scraped_at=datetime.now(),
                        success=False,
                        error_message=error_msg
                    )

                time.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                error_msg = f"Scraping error: {str(e)}"
                logger.error(f"Unexpected error scraping {url}: {error_msg}")

                return ScrapedArticle(
                    url=url,
                    title=title,
                    content="",
                    scraped_at=datetime.now(),
                    success=False,
                    error_message=error_msg
                )
