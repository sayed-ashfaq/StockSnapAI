# File: examples/test_complete_analysis.py (NEW - Test the complete system)
"""
Test the complete stock news analysis system
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_complete_analysis():
    print("=== Testing Complete Stock News Analysis ===")

    try:
        # Check environment variables
        print("1. Checking environment variables...")
        from config.settings import settings

        required_keys = {
            'TAVILY_API_KEY': settings.TAVILY_API_KEY,
            'OPENAI_API_KEY': settings.OPENAI_API_KEY
        }

        for key_name, key_value in required_keys.items():
            if not key_value:
                print(f"❌ {key_name} not found!")
                return
            print(f"✅ {key_name} loaded: {key_value[:8]}...")

        # Test the complete analysis
        print("\n2. Testing complete analysis...")
        from src.services.news_service import NewsService

        service = NewsService()
        ticker = "AAPL"  # Test with Apple

        print(f"\n3. Analyzing {ticker} stock news...")

        # THIS IS THE MAIN FUNCTION - Everything in single variables
        result = service.get_complete_stock_analysis(ticker)

        print("\n" + "="*60)
        print("📰 COMBINED HEADLINES:")
        print("="*60)
        print(result['combined_headlines'])

        print("\n" + "="*60)
        print("📄 COMBINED ARTICLES:")
        print("="*60)
        print(result['combined_articles'][:2000] + "..." if len(result['combined_articles']) > 2000 else result['combined_articles'])

        print("\n" + "="*60)
        print("🔗 ALL LINKS:")
        print("="*60)
        print(result['all_links'])

        print("\n" + "="*60)
        print("😊 OVERALL SENTIMENT:")
        print("="*60)
        print(result['overall_sentiment'])

        print("\n✅ Complete analysis finished successfully!")
        print(f"📊 Total characters in combined articles: {len(result['combined_articles'])}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_analysis()