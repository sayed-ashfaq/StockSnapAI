"""
Test the news service with Tavily integration
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_tavily_news_service():
    print("=== Testing News Service with Tavily ===")

    try:
        # Test environment loading
        print("1. Testing environment variables...")
        from config.settings import settings

        # Check required API keys
        required_keys = {
            'NEWS_API_KEY': settings.NEWS_API_KEY,
            'TAVILY_API_KEY': settings.TAVILY_API_KEY
        }

        for key_name, key_value in required_keys.items():
            if not key_value:
                print(f"❌ {key_name} not found!")
                print(f"Please add {key_name} to your .env file.")
                return
            print(f"✅ {key_name} loaded: {key_value[:8]}...")

        # Test Tavily client
        print("\n2. Testing TavilyClient...")
        from src.services.external.tavily_client import TavilyClient

        tavily_client = TavilyClient()
        print("✅ TavilyClient initialized successfully")

        # Test news service
        print("\n3. Testing full NewsService with Tavily...")
        from src.services.news_service import NewsService

        service = NewsService()

        # Test with a specific ticker
        ticker = "nvidia"
        print(f"\n4. Processing news for {ticker}...")

        # Test headlines
        print("\n=== HEADLINES ===")
        headlines = service.fetch_headlines_string(ticker)
        print(headlines)

        print("\n" + "=" * 50)

        # # Test full articles with Tavily
        # print("\n=== FULL ARTICLES (with Tavily) ===")
        # articles = service.fetch_full_articles_string(ticker)
        #
        # # Show preview of articles
        # if len(articles) > 1000:
        #     print(articles[:1000] + "\n...[truncated for display]...")
        #     print(f"\nTotal article content length: {len(articles)} characters")
        # else:
        #     print(articles)
        #
        # print("\n" + "=" * 50)
        #
        # # Test complete processing
        # print("\n=== COMPLETE PROCESSING ===")
        # result = service.process_ticker_news(ticker)
        #
        # print(f"Ticker: {result.ticker}")
        # print(f"Articles Count: {result.articles_count}")
        # print(f"Fetch Timestamp: {result.fetch_timestamp}")
        # print(f"Processing Errors: {result.processing_errors}")

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_tavily_news_service()