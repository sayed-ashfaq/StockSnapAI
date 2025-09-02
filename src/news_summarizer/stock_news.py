import os
import sys
from datetime import datetime
from typing import List, Dict, Any

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import JsonOutputParser
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from prompts.prompt_library import STOCKANALYZER_PROMPT
from utils.model_loader import ModelLoader
from utils.tool_loader import TavilySearchTool
from config.settings import PortfolioReport

from exceptions.custom_exception import DocumentPortalException, PortfolioAnalyzerError
from logger import GLOBAL_LOGGER  as log

from dotenv import load_dotenv
load_dotenv()


class StockAnalyzer:
    def __init__(self):
        try:
            self.loader= ModelLoader()
            self.llm= self.loader.load_llm()

            # load tavily
            self.tavily_search = TavilySearchTool()
            self.search_tool= self.tavily_search.load_tavily_tool()

            # prepare parsers
            self.parser= JsonOutputParser(pydantic_object=PortfolioReport)
            self.fixing_parser= OutputFixingParser.from_llm(parser= self.parser, llm= self.llm)

            # bringing prompt
            self.prompt= STOCKANALYZER_PROMPT

            # # creating a memory checkpointer
            # self.memory= MemorySaver()

            # create agent
            self.agent_executor= create_react_agent(model= self.llm, tools=[self.search_tool])

            log.info("Portfolio Analyzer initialized Successfully")
        except Exception as e:
            log.error(f"Error initializing Portfolio Analyzer: {e}")
            raise PortfolioAnalyzerError("Error in Portfolio Analyzer", sys)

    def get_sentiment_color(self, sentiment):
        """Return color based on sentiment"""
        colors = {
            "STRONG POSITIVE": "#00C851",
            "POSITIVE": "#4CAF50",
            "NEUTRAL": "#FFA726",
            "NEGATIVE": "#F44336",
            "STRONG NEGATIVE": "#B71C1C"
        }
        return colors.get(sentiment, "#808080")

    def _validate_symbols(self, symbols: List[str]) -> List[str]:
        cleaned= [s.strip().upper() for s in symbols if isinstance(s, str) and s.strip()]
        return list(dict.fromkeys(cleaned))

    def _fallback_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Safe fallback if the LLM/chain fails."""
        return {
            "portfolio_analysis": {
                "portfolio_stocks": symbols,
                "overall_portfolio_sentiment": "NEUTRAL",
                "analysis_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "portfolio_summary": "Fallback neutral summary. LLM analysis failed or was unavailable.",
                "market_themes": [],
                "portfolio_risks": [],
                "portfolio_opportunities": []
            },
            "individual_stocks": [
                {
                    "stock_symbol": sym,
                    "sentiment": "NEUTRAL",
                    "key_news_category": "general",
                    "price_impact": "NEUTRAL",
                    "quick_summary": f"No analysis available for {sym}."
                }
                for sym in symbols
            ]
        }

    def analyze_portfolio_batch(self, stock_symbols):
        try:
            chain= self.prompt | self.agent_executor | self.fixing_parser
            log.info("Meta-data analysis chain initialized")

            invoke_payload= {
                "portfolio": stock_symbols,
                "request_time": datetime.utcnow().isoformat()
            }

            response= chain.invoke(invoke_payload)
        except Exception as e:
            pass
