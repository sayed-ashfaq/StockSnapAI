from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum


#==========Portfolio pydantic validators===========


class SentimentEnum(str, Enum):
    STRONG_POSITIVE = "STRONG POSITIVE"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    STRONG_NEGATIVE = "STRONG NEGATIVE"


class ImpactEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriceImpactEnum(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class CategoryEnum(str, Enum):
    EARNINGS = "earnings"
    REGULATORY = "regulatory"
    PRODUCT = "product"
    GENERAL = "general"


class PortfolioRequest(BaseModel):
    stocks: List[str] = Field(..., min_items=1, max_items=20)
    user_id: Optional[str] = None

    @field_validator('stocks')
    def validate_stocks(cls, v):
        if not v:
            raise ValueError('Portfolio cannot be empty')
        # Clean and validate stock symbols
        cleaned_stocks = []
        for stock in v:
            cleaned = stock.strip().upper()
            if not cleaned:
                continue
            if len(cleaned) > 10:  # Reasonable stock symbol length
                raise ValueError(f'Stock symbol too long: {cleaned}')
            cleaned_stocks.append(cleaned)

        if not cleaned_stocks:
            raise ValueError('No valid stock symbols provided')

        return cleaned_stocks


class IndividualStockAnalysis(BaseModel):
    stock_symbol: str
    sentiment: SentimentEnum
    quick_summary: List[str] = Field(..., min_length=10, max_length=500)
    key_news_category: CategoryEnum
    price_impact: PriceImpactEnum
    source_links: List[str]
    confidence_score: float = Field(None, ge=0.0, le=1.0)


class PortfolioAnalysis(BaseModel):
    analysis_date: datetime
    portfolio_stocks: List[str]
    overall_portfolio_sentiment: SentimentEnum
    portfolio_summary: List[str] = Field(..., min_length=20, max_length=1000)
    market_themes: List[str] = Field(..., max_items=5)
    portfolio_risks: List[str] = Field(..., max_items=5)
    portfolio_opportunities: List[str] = Field(..., max_items=5)


class NewsAnalysisResponse(BaseModel):
    portfolio_analysis: PortfolioAnalysis
    individual_stocks: List[IndividualStockAnalysis]
    cache_hit: bool = False
    processing_time_ms: int
    source: str = "tavily_openai"


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

class WhatsAppMessageResponse(BaseModel):
    stock_symbol: str
    news_summary: Union[str, List[str]]
    sentiment: SentimentEnum # bearish, neutral, bullish
    confidence: float
    risks: str
    action_advice: str
    source_links: List[str]







