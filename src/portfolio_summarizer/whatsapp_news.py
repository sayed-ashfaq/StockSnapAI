import sys
from prompts.prompt_library import NEWS_PROMPT
from utils.model_loader import ModelLoader
from utils.tool_loader import TavilySearchTool
from .schemas import WhatsAppMessageResponse

from langgraph.prebuilt import create_react_agent

from logger import GLOBAL_LOGGER as log
from exceptions.custom_exception import WhatsAppMessengerError

class WhatsappMessenger:
    def __init__(self):
        try:
            self.llm= ModelLoader().load_llm()
            self.search_tool = TavilySearchTool().load_tavily_tool()

            self.prompt = NEWS_PROMPT

        except Exception as e:
            log.error(f"WhatsAppMessenger has failed to initiate")
            raise WhatsAppMessengerError(f"WhatsAppMessenger has failed to initiate {e}", sys)

    def _get_context(self, query):
        try:
            search_results= self.search_tool.search(
                query= "")
        except Exception as e:
            log.error("Failed to get context for query")
            raise WhatsAppMessengerError(f"Unable to extract the context about the given query {e}", sys)

    def execute_agent(self,query:str):
        try:

            input_message = {"role": "user", "content": query}
            log.info("WhatsAppMessenger Agent is running.")
            return self.agent_executor.invoke({"messages": [input_message]})

        except Exception as e:
            log.error(f"WhatsAppMessenger has failed to execute {e}")
            raise WhatsAppMessengerError(f"WhatsAppMessenger agent has failed to execute {e}", sys)


    def _format_response(self,response):
        try:
            pass
        except Exception as e:
            log.error(f"What's app messenger failed to format the response")
            raise WhatsAppMessengerError(f"What's app messenger failed to format the response {e}", sys)





