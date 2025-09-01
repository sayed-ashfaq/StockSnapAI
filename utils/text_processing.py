import re
from typing import List
from bs4 import BeautifulSoup


class TextProcessor:
    """Utility class for text processing operations"""

    @staticmethod
    def clean_html(html_content: str) -> str:
        """Remove HTML tags and clean text"""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    @staticmethod
    def extract_article_content(html: str) -> str:
        """Extract main article content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Common article selectors (ordered by priority)
        content_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            'main',
            '.story-body',
            '.article-body'
        ]

        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return TextProcessor.clean_html(str(content))

        # Fallback: find largest text block
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text().strip() for p in paragraphs])
            return content

        # Last resort: clean all text
        return TextProcessor.clean_html(str(soup))

    @staticmethod
    def combine_headlines(articles: List[dict], separator: str = "\n\n") -> str:
        """Combine headlines into a single string"""
        headlines = []
        for i, article in enumerate(articles, 1):
            headline = f"{i}. {article.get('title', 'No title')}"
            if article.get('description'):
                headline += f"\n   {article['description']}"
            headlines.append(headline)

        return separator.join(headlines)

    @staticmethod
    def combine_articles(articles: List[dict], separator: str = "\n\n---\n\n") -> str:
        """Combine full articles into a single string"""
        full_articles = []
        for i, article in enumerate(articles, 1):
            article_text = f"ARTICLE {i}: {article.get('title', 'No title')}\n\n"
            article_text += article.get('content', 'No content available')
            full_articles.append(article_text)

        return separator.join(full_articles)