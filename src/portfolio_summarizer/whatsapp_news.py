import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import PydanticOutputParser

from prompts.prompt_library import NEWS_PROMPT
from utils.model_loader import ModelLoader
from utils.tool_loader import TavilySearchTool
from .schemas import WhatsAppMessageResponse
from logger import GLOBAL_LOGGER as log
from exceptions.custom_exception import WhatsAppMessengerError



class WhatsappMessenger:
    def __init__(self):
        try:
            # llm
            self.llm= ModelLoader().load_llm()
            # tavily tool
            self.search_tool = TavilySearchTool().load_tavily_tool()

            # get indian dates
            IST = ZoneInfo("Asia/Kolkata")
            self.current_date = datetime.now(IST).strftime("%d-%m-%Y")

            self.parser = PydanticOutputParser(pydantic_object=WhatsAppMessageResponse)

            self.prompt = NEWS_PROMPT

            self._setup_analysis_chain()

            log.info("WhatsAppMessenger chain has been initialized successfully")
        except Exception as e:
            log.error(f"WhatsAppMessenger has failed to initiate")
            raise WhatsAppMessengerError(f"WhatsAppMessenger has failed to initiate {e}", sys)

    def _get_news_context(self, ticker: str):
        query = f"{ticker} earning analyst ratings insider trading technical analysis sector news {self.current_date}"
        search_results = {"results": []}
        try:

            search_results = self.search_tool.invoke({"query": query})

            articles = [{
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                'url': r.get("url", ""),
                'published_date': r.get("published_date", ""),
                "source": r.get("source", ""),
                "domain": r.get("domain", ""),
            } for r in search_results.get("results", [])]

            return articles
        except Exception as e:
            log.error("Failed to get context for query")
            raise WhatsAppMessengerError(f"Unable to extract the context about the given query {e}", sys)

    def _setup_analysis_chain(self):
        try:
            self.analysis_chain = (
                self.prompt
                | self.llm
                | self.parser
            )

        except Exception as e:
            log.error(f"WhatsAppMessenger has failed to execute {e}")
            raise WhatsAppMessengerError(f"WhatsAppMessenger agent has failed to execute {e}", sys)

    def analyze_stock(self, ticker:str ):
        try:

            payload = {
                "ticker": ticker,
                "context": self._get_news_context(ticker)
            }
            log.info("Initiating analysis chain execution and starting ticker analysis...")
            response = self.analysis_chain.invoke(payload)
            log.info("Analysis chain executed successfully")
            return response
        except Exception as e:
            log.error(f"Failed to analyze the stock {ticker}")
            raise WhatsAppMessengerError(f"Failed to analyze the stock {ticker}", sys)

    def _format_response(self,response):
        try:
            pass
        except Exception as e:
            log.error(f"What's app messenger failed to format the response")
            raise WhatsAppMessengerError(f"What's app messenger failed to format the response {e}", sys)





