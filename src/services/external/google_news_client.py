from urllib.request import urlopen
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
from config.settings import settings
from models.schemas.news import GoogleNewsItem
from exceptions.external import NewsAPIError
from log_utils import GLOBAL_LOGGER as logger

class GoogleNewsClient:
    """Client for fetching news from Google News RSS"""

    def __init__(self):
        self.base_url = settings.GOOGLE_NEWS_BASE_URL
        logger.info("GoogleNewsClient initialized")

    def fetch_stock_news(self, ticker: str, quantity: int = None) -> List[GoogleNewsItem]:
        """
        Fetch news for a stock ticker from Google News RSS

        Args:
            ticker: Stock ticker symbol
            quantity: Number of articles to fetch

        Returns:
            List of GoogleNewsItem objects
        """
        quantity = quantity or settings.NEWS_QUANTITY

        try:
            # Create search query for stock
            search_query = f"{ticker} stock earnings news"
            site_url = self.base_url.format(search_query)

            logger.info(f"Fetching Google News for {ticker}: {site_url}")

            # Open and read the RSS feed
            op = urlopen(site_url)
            rd = op.read()
            op.close()

            # Parse XML content
            sp_page = BeautifulSoup(rd, 'xml')
            news_items = sp_page.find_all('item')

            articles = []
            for item in news_items[:quantity]:
                try:
                    article = GoogleNewsItem(
                        title=item.title.text if item.title else "No title",
                        link=item.link.text if item.link else "",
                        pub_date=item.pubDate.text if item.pubDate else "",
                        source=item.source.text if item.source else "Unknown source",
                        description=item.description.text if item.description else None
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse news item: {e}")
                    continue

            logger.info(f"Successfully fetched {len(articles)} articles for {ticker}")
            return articles

        except Exception as e:
            logger.error(f"Failed to fetch Google News for {ticker}: {e}")
            raise NewsAPIError(f"Failed to fetch news: {str(e)}")