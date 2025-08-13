import os
import requests
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.model_loader import ModelLoader
load_dotenv()


class StockNewsFAISS:
    """
    Fetches news articles for a company, scrapes paragraphs,
    and stores them in a FAISS index for retrieval.
    """

    def __init__(self, api_key=None, faiss_dir="faiss_news_index"):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.faiss_dir = faiss_dir
        if not self.api_key:
            raise ValueError("NEWS_API_KEY is required in .env or as parameter.")
        os.makedirs(self.faiss_dir, exist_ok=True)

    def fetch_news_list(self, company_name: str, limit: int = 3) -> List[dict]:
        """
        Fetch top N news articles from NewsAPI.
        """
        endpoint = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": self.api_key,
            "q": company_name,
            "sortBy": "popularity",
            "pageSize": limit,
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            return [{"title": a["title"], "url": a["url"]} for a in articles]
        except Exception as e:
            print(f"[ERROR] Fetching news failed: {e}")
            return []

    def fetch_article_paragraphs(self, url: str) -> List[str]:
        """
        Fetch an article URL and return a list of paragraph texts.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        except Exception as e:
            print(f"[ERROR] Fetching article content failed for {url}: {e}")
            return []

    def store_in_faiss(self, paragraphs: List[str]):
        """
        Store the paragraphs in a FAISS index.
        """
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = splitter.create_documents(paragraphs)

        # Create embeddings
        embeddings = ModelLoader().load_embedding_model()

        # Create FAISS index
        vectorstore = FAISS.from_documents(texts, embeddings)

        # Save FAISS index
        vectorstore.save_local(self.faiss_dir)
        print(f"[INFO] FAISS index saved to {self.faiss_dir}")

    def run(self, company_name: str, limit: int = 3):
        """
        Full pipeline: fetch news → scrape paragraphs → store in FAISS.
        """
        news_list = self.fetch_news_list(company_name, limit)
        all_paragraphs = []

        for article in news_list:
            paras = self.fetch_article_paragraphs(article["url"])
            all_paragraphs.extend(paras)

        if not all_paragraphs:
            print("[WARN] No paragraphs found. Nothing to store.")
            return

        self.store_in_faiss(all_paragraphs)
        print(f"[INFO] Stored {len(all_paragraphs)} paragraphs in FAISS index.")


if __name__ == "__main__":
    fetcher = StockNewsFAISS()
    fetcher.run(company_name="Tesla", limit=3)
