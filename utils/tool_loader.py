
import os, sys

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from logger import GLOBAL_LOGGER as log
from exceptions.custom_exception import TavilyAPIError


class TavilySearchTool:
    def __init__(self):
        if os.getenv("ENV", "local").lower() != "production":
            load_dotenv()
            log.info("Running TavilySearchTool in LOCAL MODE: .env loaded")
        else:
            log.info("Running TavilySearchTool in PRODUCTION Mode")

        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            log.error("Missing TAVILY_API_KEY")
            raise TavilyAPIError("Missing TAVILY_API_KEY. verify your env setup.", sys)

        self._tool= None # caching

        self.indian_news_domains = [
            "economictimes.indiatimes.com",
            "business-standard.com",
            "livemint.com",
            "moneycontrol.com",
            "financialexpress.com",
            "zeebiz.com",
            "cnbctv18.com",
            "bloombergquint.com",
            "thehindubusinessline.com",
            "reuters.com",
            "nseindia.com",
            "bseindia.com",
            "yahoo.com",
            "tradingview.com",
            "cnbc.com",
            'tradingeconomics.com',
        ]

    # Load TAVILY Search tool
    def load_tavily_tool(self, max_results : int= 10, time_range : str= "week"):
        if not self._tool:
            try:
                self._tool = TavilySearch(
                    api_key=self.api_key,
                    max_results=max_results,
                    time_range=time_range,
                    topic = "news",
                    search_depth= 'advanced',
                    include_domains= self.indian_news_domains,


                )
                log.info("TavilySearch tool initialized successfully")

            except Exception as e:
                log.warning("Failed to initialize TavilySearch tool", e)
                raise TavilyAPIError("Failed to load TavilyTool", sys)

        return self._tool

# Testing tool
if __name__ == "__main__":
    tool = TavilySearchTool().load_tavily_tool()
    print(tool.invoke("Tell me latest news about Tesla along with date and get the full content as well"))