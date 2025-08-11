
# todo
# 1. Get the news data from the newsapi
# 2. Scrap the content using the url
# 3. Get the content and store it in the list
from dotenv import load_dotenv
load_dotenv()

import os
import requests
from bs4 import BeautifulSoup

class StockNewsFetcher:
    """
    Handles fetching and scraping of news articles for a given company or stock ticker.
    """
    def __init__(self, api_key= None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.news_endpoint= "https://newsapi.org/v2/top-headlines"
        if not self.api_key:
            raise ValueError("NEWS_API_KEY is required. Set as env var or pass to constructor.")
    def fetch_news_list(self, company_name, limit= 3):
        """
        Fetch top N news articles for the given company from NewsAPI.
        """
        params= {
            'apiKey': self.api_key,
            'q': company_name,
            'sortBy': 'popularity',
            'pageSize': limit,
        }
        try:
            response= requests.get(self.news_endpoint, params=params)
            response.raise_for_status()
            articles= response.json().get('articles',[])
            # Extract only relevant info
            return [{"title": a["title"], "url": a["url"]} for a in articles]
        except Exception as e:
            print(f"[ERROR] Fetching news failed: {e}")
            return []
    def fetch_article_html(self, url):
        """
        Download raw HTML from a news article
        :param url:
        :return:
        """
        try:
            response= requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"[ERROR] Fetching news article failed: {e}")
            return None
    def parse_article(self, soup):
        """
        Extract headline, bullet points, and paragraphs from article HTML
        :param soup:
        :return:
        """
        if not soup:
            return {}
        try:
            headline= soup.find("h1", class_="entry-title").get_text(strip=True) if soup.find('h1') else ""
            bullets= [
                li.get_text(strip=True)
                for li in soup.select("li")
                if "key Points" in li.text or li.text.startswith("*")
            ]
            paragraphs= [p.get_text(strip=True) for p in soup.find_all("p")]
            return {
                "headline": headline,
                "key_points": bullets,
                "paragraphs": paragraphs
            }
        except Exception as e:
            print(f"[ERROR] Parsing article failed: {e}")
            return {}

    def get_news_with_content(self, company_name, limit= 3):
        """
        Full pipeline: fetch top N articles, scrape and parse them
        :param company_name:
        :param limit:
        :return:
        """
        news_list= self.fetch_news_list(company_name)
        results = []
        for item in news_list:
            soup = self.fetch_article_html(item['url'])
            parsed_data= self.parse_article(soup)
            parsed_data["url"]= item['url']
            results.append(parsed_data)
        return results

if __name__ == "__main__":
    fetcher = StockNewsFetcher(api_key= os.getenv("NEWS_API_KEY"))

    articles= fetcher.fetch_news_list(company_name= "Tesla",)
    print("fetching news articles\n", articles)
    results= []
    for item in articles:
        soup= fetcher.fetch_article_html(item['url'])
        print("fetching articles html\n",len(soup))

        parsed_data= fetcher.parse_article(soup)
        print("parsing content\n", parsed_data)




    # for item in articles:
        # print(item['url'])
        # soup = fetcher.fetch_article_html(item["url"])
        # print(soup)