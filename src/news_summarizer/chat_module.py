## Building the chat module
import sys
import os
# import streamlit as st
from dotenv import load_dotenv
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from utils.model_loader import ModelLoader
from exception.custom_exeption import CustomException
from log_utils.custom_logging import CustomLogger

class ConversationalRAG:
    def __init__(self, retriever):
        self.log= CustomLogger().get_logger(__name__)
        self.retriever = retriever

        try:
            self.llm = self._load_llm()
            self.news_prompt= "Under construction"
        except Exception as e:
            self.log.error("Error initializing ConversationalRAG", error=str(e))
            raise CustomException("Error initializing ConversationalRAG", sys)

    def invoke(self):
        try:
            pass
        except Exception as e:
            self.log.error("Error invoking ConversationalRAG", error=str(e))
            raise CustomException("Error invoking ConversationalRAG", sys)

    def _load_llm(self):
        try:
            pass
        except Exception as e:
            self.log.error("error loading llm", error=str(e))
            raise CustomException("Error loading llm", sys)

    def _get_session_history(self):
        print("Function left for future use-cases - stay tuned for updates")
    # Future development
