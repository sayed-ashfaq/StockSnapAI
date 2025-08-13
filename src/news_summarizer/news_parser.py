from dotenv import load_dotenv
load_dotenv()

import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


class StockNewsFetcher:
    """
    Handles fetching and scraping of news articles for a given company or stock ticker.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.news_endpoint = "https://newsapi.org/v2/top-headlines"
        if not self.api_key:
            raise ValueError("NEWS_API_KEY is required. Set as an environment variable or pass to the constructor.")

    def fetch_news_list(self, company_name: str, limit: int = 3) -> List[Dict[str, str]]:
        """
        Fetch top N news articles for the given company from NewsAPI.

        :param company_name: The company name or keyword to search.
        :param limit: Maximum number of articles to fetch.
        :return: List of article dicts with 'title' and 'url'.
        """
        params = {
            "apiKey": self.api_key,
            "q": company_name,
            "sortBy": "popularity",
            "pageSize": limit,
        }
        try:
            response = requests.get(self.news_endpoint, params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            return [{"title": a["title"], "url": a["url"]} for a in articles]
        except Exception as e:
            print(f"[ERROR] Fetching news list failed: {e}")
            return []

    def fetch_article_html(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch raw HTML for a given article URL.

        :param url: Article URL.
        :return: BeautifulSoup object or None if failed.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"[ERROR] Fetching HTML failed for {url}: {e}")
            return None

    def parse_article(self, soup: BeautifulSoup) -> Dict[str, object]:
        """
        Extract headline, key points, and paragraphs from an article HTML.

        :param soup: BeautifulSoup object of the article.
        :return: Dictionary with 'headline', 'key_points', and 'paragraphs'.
        """
        if not soup:
            return {}

        try:
            headline = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
            bullets = [
                li.get_text(strip=True)
                for li in soup.find_all("li")
                if "key points" in li.text.lower() or li.text.startswith("*")
            ]
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
            return {
                "headline": headline,
                "key_points": bullets,
                "paragraphs": paragraphs,
            }
        except Exception as e:
            print(f"[ERROR] Parsing article failed: {e}")
            return {}

    def get_news_with_content(self, company_name: str, limit: int = 3) -> List[Dict[str, object]]:
        """
        Full pipeline: fetch top N articles, scrape and parse them.

        :param company_name: Company name or keyword to search.
        :param limit: Number of articles to fetch.
        :return: List of parsed article data.
        """
        news_list = self.fetch_news_list(company_name, limit)
        results = []

        for item in news_list:
            soup = self.fetch_article_html(item["url"])
            parsed_data = self.parse_article(soup)
            parsed_data["url"] = item["url"]
            results.append(parsed_data)

        return results


if __name__ == "__main__":
    fetcher = StockNewsFetcher()

    # Step 1: Fetch list of articles
    articles = fetcher.fetch_news_list(company_name="Tesla", limit=3)
    print("Fetched news list:", articles)

    # Step 2: Full scrape & parse
    results = fetcher.get_news_with_content(company_name="Tesla", limit=3)
    for r in results:
        print("\nURL:", r.get("url"))
        print("Headline:", r.get("headline"))
        print("Key Points:", r.get("key_points"))
        print("Paragraph Count:", len(r.get("paragraphs", [])))
