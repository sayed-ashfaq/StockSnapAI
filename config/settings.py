from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Individual stock analysis
class StockAnalysis(BaseModel):
    symbol: str
    sentiment: str
    category: str
    impact: str
    summary: str
    published_at: Optional[datetime] = None  # article published date & time

# Portfolio summary model
class PortfolioSummary(BaseModel):
    overall_sentiment: str
    analysis_date: datetime
    summary: str
    market_themes: List[str]
    risks: List[str]
    opportunities: List[str]

# Statistics
class PortfolioStats(BaseModel):
    sentiment_distribution: dict
    price_impact_distribution: dict

# Final full report model
class PortfolioReport(BaseModel):
    stocks_analyzed: List[str]
    summary: PortfolioSummary
    individual_stocks: List[StockAnalysis]
    stats: PortfolioStats

