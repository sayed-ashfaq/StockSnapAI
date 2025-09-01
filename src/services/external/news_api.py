import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from app.config.settings import settings
from app.exceptions.external import NewsAPIError, RateLimitError
from app.models.schemas.news import NewsArticle
import logging

logger = logging.getLogger(__name__)


class NewsAPIClient:
    """Client for interacting with NewsAPI"""

    def __init__(self):
        self.api_key = settings.NEWS_API_KEY
        self.base_url = settings.NEWS_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT,
            'X-API-Key': self.api_key
        })
        self._last_request_time = 0

    def _rate_limit(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        # NewsAPI allows 1000 requests per day, so roughly 1 per minute to be safe
        min_interval = 60  # seconds
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def fetch_stock_news(
            self,
            ticker: str,
            days_back: Optional[int] = None,
            page_size: Optional[int] = None
    ) -> List[NewsArticle]:
        """
        Fetch latest news articles for a stock ticker

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            days_back: Number of days to look back (default: from settings)
            page_size: Number of articles to fetch (default: from settings)

        Returns:
            List of NewsArticle objects
        """
        self._rate_limit()

        days_back = days_back or settings.NEWS_DAYS_BACK
        page_size = page_size or settings.NEWS_PAGE_SIZE

        # Calculate date range
        from_date = datetime.now() - timedelta(days=days_back)
        from_date_str = from_date.strftime('%Y-%m-%d')

        # Build query
        query = f'"{ticker}" OR "{ticker} stock" OR "{ticker} earnings"'

        params = {
            'q': query,
            'from': from_date_str,
            'sortBy': settings.NEWS_SORT_BY,
            'language': settings.NEWS_LANGUAGE,
            'pageSize': page_size,
            'apiKey': self.api_key
        }

        try:
            logger.info(f"Fetching news for {ticker} from {from_date_str}")

            response = self.session.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=settings.SCRAPING_TIMEOUT
            )

            if response.status_code == 429:
                raise RateLimitError("NewsAPI", retry_after=3600)

            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'ok':
                raise NewsAPIError(f"NewsAPI error: {data.get('message', 'Unknown error')}")

            articles = []
            for article_data in data.get('articles', []):
                try:
                    article = NewsArticle(
                        title=article_data['title'],
                        description=article_data.get('description'),
                        url=article_data['url'],
                        published_at=datetime.fromisoformat(
                            article_data['publishedAt'].replace('Z', '+00:00')
                        ),
                        source_name=article_data['source']['name'],
                        author=article_data.get('author')
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue

            logger.info(f"Successfully fetched {len(articles)} articles for {ticker}")
            return articles

        except requests.exceptions.RequestException as e:
            raise NewsAPIError(f"Failed to fetch news: {str(e)}")