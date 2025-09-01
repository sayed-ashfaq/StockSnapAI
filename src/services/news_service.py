from typing import List, Dict
from datetime import datetime
import logging
from app.services.external.news_api import NewsAPIClient
from app.services.external.web_scraper import WebScraper
from app.utils.text_processing import TextProcessor
from app.models.schemas.news import NewsResponse, NewsArticle, ScrapedArticle
from app.exceptions.external import NewsAPIError, WebScrapingError

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching and processing news articles"""

    def __init__(self):
        self.news_client = NewsAPIClient()
        self.web_scraper = WebScraper()
        self.text_processor = TextProcessor()

    def fetch_headlines_string(self, ticker: str) -> str:
        """
        Fetch top 3 headlines for a ticker and return as single string

        Args:
            ticker: Stock ticker symbol

        Returns:
            String containing formatted headlines
        """
        try:
            articles = self.news_client.fetch_stock_news(ticker)

            if not articles:
                return f"No recent news found for {ticker}"

            # Convert to dict format for text processor
            articles_dict = [
                {
                    'title': article.title,
                    'description': article.description,
                    'url': str(article.url),
                    'published_at': article.published_at,
                    'source': article.source_name
                }
                for article in articles
            ]

            return self.text_processor.combine_headlines(articles_dict)

        except Exception as e:
            logger.error(f"Failed to fetch headlines for {ticker}: {e}")
            return f"Error fetching headlines for {ticker}: {str(e)}"

    def fetch_full_articles_string(self, ticker: str) -> str:
        """
        Fetch top 3 articles, scrape full content, and return as single string

        Args:
            ticker: Stock ticker symbol

        Returns:
            String containing full articles content
        """
        try:
            # Fetch articles from NewsAPI
            articles = self.news_client.fetch_stock_news(ticker)

            if not articles:
                return f"No recent articles found for {ticker}"

            scraped_articles = []

            # Scrape full content for each article
            for article in articles:
                scraped = self.web_scraper.scrape_article(str(article.url), article.title)

                if scraped.success:
                    scraped_articles.append({
                        'title': article.title,
                        'content': scraped.content,
                        'url': str(article.url),
                        'source': article.source_name
                    })
                else:
                    # Fallback to description if scraping fails
                    scraped_articles.append({
                        'title': article.title,
                        'content': article.description or "Content not available",
                        'url': str(article.url),
                        'source': article.source_name
                    })

            return self.text_processor.combine_articles(scraped_articles)

        except Exception as e:
            logger.error(f"Failed to fetch full articles for {ticker}: {e}")
            return f"Error fetching full articles for {ticker}: {str(e)}"

    def process_ticker_news(self, ticker: str) -> NewsResponse:
        """
        Complete news processing for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            NewsResponse with headlines and full articles as strings
        """
        logger.info(f"Processing news for ticker: {ticker}")

        processing_errors = []

        try:
            # Fetch headlines
            headlines_string = self.fetch_headlines_string(ticker)

            # Fetch full articles
            full_articles_string = self.fetch_full_articles_string(ticker)

            # Count articles processed
            articles = self.news_client.fetch_stock_news(ticker)
            articles_count = len(articles)

            return NewsResponse(
                ticker=ticker.upper(),
                headlines_string=headlines_string,
                full_articles_string=full_articles_string,
                articles_count=articles_count,
                fetch_timestamp=datetime.now(),
                processing_errors=processing_errors
            )

        except Exception as e:
            error_msg = f"Failed to process news for {ticker}: {str(e)}"
            logger.error(error_msg)
            processing_errors.append(error_msg)

            return NewsResponse(
                ticker=ticker.upper(),
                headlines_string=f"Error processing headlines for {ticker}",
                full_articles_string=f"Error processing articles for {ticker}",
                articles_count=0,
                fetch_timestamp=datetime.now(),
                processing_errors=processing_errors
            )