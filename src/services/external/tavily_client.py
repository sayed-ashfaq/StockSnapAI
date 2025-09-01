# File: app/services/external/tavily_client.py (UPDATED for URL-based extraction)
import requests
from typing import Optional, Dict, List
from datetime import datetime
import time
import logging
from config.settings import settings
from exceptions.external import WebScrapingError
from models.schemas.news import ExtractedArticle

from log_utils import GLOBAL_LOGGER as logger

class TavilyClient:
    """Client for extracting article content using Tavily API"""

    def __init__(self):
        if not settings.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is required")

        self.api_key = settings.TAVILY_API_KEY
        self.base_url = settings.TAVILY_BASE_URL
        self.session = requests.Session()
        self._last_request_time = 0

        logger.info("TavilyClient initialized successfully")

    def _rate_limit(self):
        """Rate limiting for Tavily API"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        # Conservative: 1 request per 2 seconds
        min_interval = 2
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def extract_article_content(self, url: str, title: str, source: str, pub_date: str) -> ExtractedArticle:
        """
        Extract full article content using Tavily

        Args:
            url: Article URL
            title: Article title
            source: News source
            pub_date: Publication date

        Returns:
            ExtractedArticle with full content
        """
        self._rate_limit()

        try:
            logger.info(f"Extracting content from: {url}")

            # Tavily payload for URL-based extraction
            payload = {
                "api_key": self.api_key,
                "query": url,  # Direct URL query
                "search_depth": "advanced",
                "include_answer": False,
                "include_images": False,
                "include_raw_content": True,
                "max_results": 1
            }

            response = self.session.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=settings.TAVILY_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])

            if results:
                result = results[0]
                content = result.get('content', '') or result.get('raw_content', '')

                if len(content.strip()) < 50:
                    # Fallback: search by title
                    payload['query'] = f'"{title}" {source}'
                    fallback_response = self.session.post(
                        f"{self.base_url}/search",
                        json=payload,
                        timeout=settings.TAVILY_TIMEOUT
                    )
                    fallback_data = fallback_response.json()
                    fallback_results = fallback_data.get('results', [])

                    if fallback_results:
                        content = fallback_results[0].get('content', '') or fallback_results[0].get('raw_content', '')

                if len(content.strip()) >= 50:
                    logger.info(f"Successfully extracted {len(content)} characters")

                    return ExtractedArticle(
                        title=title,
                        link=url,
                        source=source,
                        pub_date=pub_date,
                        content=content,
                        extraction_success=True
                    )

            # If we reach here, extraction failed
            raise WebScrapingError("Insufficient content extracted")

        except Exception as e:
            error_msg = f"Tavily extraction failed: {str(e)}"
            logger.error(f"Error extracting {url}: {error_msg}")

            return ExtractedArticle(
                title=title,
                link=url,
                source=source,
                pub_date=pub_date,
                content=f"Content extraction failed: {error_msg}",
                extraction_success=False,
                error_message=error_msg
            )
