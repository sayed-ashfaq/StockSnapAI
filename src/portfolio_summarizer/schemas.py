from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

# Individual stock analysis
class StockAnalysis(BaseModel):
    symbol: str
    sentiment: str
    summary: str
    category: str
    impact: str
    published_at: Optional[datetime] = None  # article published date & time
    source_links: List[str] = None

class ThemesResponse(BaseModel):
    risks: List[str]
    opportunities: List[str]
    general: List[str]

# Portfolio summary model
class PortfolioAnalysisResponse(BaseModel):
    overall_sentiment: str
    analysis_date: datetime
    portfolio_stocks: List[StockAnalysis]
    portfolio_sentiment: str
    summary: str
    theme:ThemesResponse
    risks: List[str]
    opportunities: List[str]

class SentimentEnum(str, Enum):
    strong_bullish = "Strong Bullish"
    bullish = "Bullish"
    neutral = "Neutral"
    bearish = "Bearish"
    strong_bearish= "Strong Bearish"


class NewsAnalysisResponse(BaseModel):
    summary: str
    sentiment: SentimentEnum
    confidence_percentage:int=  Field(..., ge= 0, le= 100)
    impact: str
    actions: str
    source_links: List[str]

class WhatsAppMessageResponse(BaseModel):
    stock_symbol: str
    news_summary: Union[str, List[str]]
    sentiment: SentimentEnum # bearish, neutral, bullish
    confidence: float
    risks: str
    action_advice: str
    source_links: List[str]







