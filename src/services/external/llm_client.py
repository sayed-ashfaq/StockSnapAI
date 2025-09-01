# File: app/services/external/llm_client.py (NEW - LLM for sentiment analysis)
import openai
from typing import Dict, List
from config.settings import settings
from models.schemas.news import SentimentAnalysis
from log_utils import GLOBAL_LOGGER as logger
import json



class LLMClient:
    """Client for LLM operations using OpenAI"""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")

        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("LLMClient initialized successfully")

    def analyze_sentiment(self, text: str, ticker: str) -> SentimentAnalysis:
        """
        Analyze sentiment of news text for a specific stock

        Args:
            text: News content to analyze
            ticker: Stock ticker for context

        Returns:
            SentimentAnalysis object
        """
        try:
            prompt = f"""
            Analyze the sentiment of this financial news about {ticker} stock:

            News Content: {text[:3000]}  # Limit content to avoid token limits

            Provide your analysis in this EXACT JSON format:
            {{
                "sentiment": "Positive" or "Negative" or "Neutral",
                "score": <number between 1-10, where 1=very negative, 10=very positive>,
                "confidence": <number between 0-1 indicating confidence in analysis>,
                "key_points": ["point1", "point2", "point3"],
                "reasoning": "Brief explanation of why you assigned this sentiment"
            }}

            Focus on how this news might impact {ticker} stock price and investor sentiment.
            """

            response = self.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system",
                     "content": "You are a financial analyst specializing in sentiment analysis of stock news."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                sentiment_data = json.loads(content)
                return SentimentAnalysis(**sentiment_data)
            except json.JSONDecodeError:
                # Fallback parsing if JSON fails
                return self._parse_fallback_sentiment(content)

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return SentimentAnalysis(
                sentiment="Neutral",
                score=5.0,
                confidence=0.0,
                key_points=["Analysis failed"],
                reasoning=f"Error: {str(e)}"
            )

    def _parse_fallback_sentiment(self, content: str) -> SentimentAnalysis:
        """Parse sentiment from non-JSON LLM response"""
        # Basic parsing logic for fallback
        if "positive" in content.lower():
            sentiment = "Positive"
            score = 7.0
        elif "negative" in content.lower():
            sentiment = "Negative"
            score = 3.0
        else:
            sentiment = "Neutral"
            score = 5.0

        return SentimentAnalysis(
            sentiment=sentiment,
            score=score,
            confidence=0.5,
            key_points=["Fallback analysis"],
            reasoning="Parsed from non-JSON response"
        )