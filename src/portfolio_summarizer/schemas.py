from enum import Enum
from typing import List, Optional
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
    strong_bullish = "strong_bullish"
    bullish = "bullish"
    neutral = "neutral"
    bearish = "bearish"
    strong_bearish= "strong_bearish"


class NewsAnalysisResponse(BaseModel):
    summary: str
    sentiment: SentimentEnum
    confidence_percentage:int=  Field(..., ge= 0, le= 100)
    impact: str
    actions: str
    source_links: List[str]

class WhatsAppMessageResponse(BaseModel):
    stock_symbol: str = Field(description="StockSymbol")
    news_summary: str = Field(description="2-3 line summary of the extracted news")
    sentiment: SentimentEnum # bearish, neutral, bullish
    confidence: float =  Field(..., ge= 0, le= 100) # 0-1
    action_advice: str
    source_links: List[str]







