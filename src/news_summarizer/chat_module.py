## Building the chat module
import sys
import streamlit as st
from operator import itemgetter
from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from utils.model_loader import ModelLoader
from prompts.prompt_library import document_summarize_prompt,qa_history_prompt,qa_context_history_prompt
from exception.custom_exeption import CustomException
from log_utils.custom_logging import CustomLogger

class ConversationalRAG:
    def __init__(self, session_id: str, retriever):
        self.log = CustomLogger().get_logger(__name__)
        self.session_id = session_id
        self.retriever = retriever
        self.llm = self._load_llm()
        try:
            self.contextualize_prompt = qa_history_prompt
            self.qa_prompt= qa_context_history_prompt

            self._build_lcel_chain()
            self.log.info("Conversational RAG initialized", session_id= self.session_id)

        except Exception as e:
            self.log.error("Failed to initialize conversational RAG", error=str(e))
            raise CustomException("Failed to initialize conversational RAG", sys)


    def _load_llm(self):
        try:
            llm= ModelLoader().load_llm("google")
            self.log.info("Loaded LLM successfully", class_name= llm.__class__.__name__)
            return llm
        except Exception as e:
            self.log.error("error loading llm", error=str(e))
            raise CustomException("Error loading llm", sys)

    def invoke(self, user_input: str, chat_history: Optional[List[BaseMessage]]= None)->str:
        """
               package of chain
               :param user_input:
               :param chat_history:
               :return:
               """
        try:
            chat_history = chat_history or []
            payload = {"input": user_input, "chat_history": chat_history or []}
            answer = self.chain.invoke(payload)
            if not answer:
                self.log.warning("No answer has been generated", session_id=self.session_id)
                return "No answer generated"

            self.log.info("Chain invoke successfully",
                          session_id=self.session_id,
                          user_input=user_input,
                          answer_preview=answer[:100])
            return answer
    #     try:
    #         response= self.chain.invoke(
    #             {"input": user_input},
    #             config= {"configurable": {"session_id": self.session_id}}
    #         )
    #         answer= response.get("answer", "No answer")
    #
    #
    #         if not answer:
    #             self.log.warning("Empty answer received")
    #
    #         self.log.info("Chain invoked successfully", user_input= user_input, answer= answer[:10])
    #         return answer
        except Exception as e:
            self.log.error("Failed to invoke conversational RAG", error=str(e))
            raise CustomException("Failed to invoke conversational RAG", sys)
    #
    #
    # def _get_session_history(self, session_id) -> BaseChatMessageHistory:
    #     try:
    #         if "chat_history" not in st.session_state:
    #             st.session_state.chat_history= {}
    #
    #
    #         if session_id not in st.session_state.chat_history:
    #             st.session_state.chat_history[session_id]= ChatMessageHistory()
    #             self.log.info("New Chat session history created", session_id= session_id)
    #
    #         return st.session_state.chat_history[session_id]
    #
    #     except Exception as e:
    #         self.log.error("Failed to access session history", error=str(e))
    #         raise CustomException("Failed to access session history", sys)

    def _format_docs(self, docs):
        return "\n\n".join(d.page_content for d in docs)

    def _build_lcel_chain(self):
        try:
            question_rewriter= (
                {'input': itemgetter("input"), "chat_history": itemgetter("chat_history")}
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )

            retrieved_docs= question_rewriter | self.retriever | self._format_docs

            self.chain= (
                {
                    "documents": retrieved_docs,
                    "input": itemgetter("input"),
                    "chat_history": itemgetter("chat_history"),
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )

            self.log.info("Chain has been built successfully", session_id= self.session_id)
        except Exception as e:
            self.log.error("Failed to build LCEL chain", error=str(e))
            raise CustomException("Failed to build LCEL chain", sys)








 ### ------------------- Old code ----------------------##
        # def __init__(self, session_id, retriever):
        #     self.log = CustomLogger().get_logger(__name__)
        #     self.retriever = retriever
        #     self.session_id = session_id
        #
        #     try:
        #         self.llm = self._load_llm()
        #         self.summarizer_prompt = document_summarize_prompt
        #         self.contextualize_prompt = contextualize_prompt
        #         self.conversation_prompt = qa_context_prompt
        #
        #         self.history_aware_retriever = create_history_aware_retriever(
        #             self.llm, self.retriever, self.contextualize_prompt
        #         )
        #
        #         self.log.info("Created history-aware retriever")
        #
        #         self.qa_chain = create_stuff_documents_chain(self.llm, self.conversation_prompt,
        #                                                      document_variable_name="documents")
        #         self.log.info("Created stuff-documents chain")
        #         self.ragchain = create_retrieval_chain(self.history_aware_retriever, self.qa_chain)
        #         self.log.info("Created RAG Chain")
        #
        #         self.chain = RunnableWithMessageHistory(
        #             self.ragchain,
        #             self._get_session_history,
        #             input_messages_key="input",
        #             history_messages_key="chat_history",
        #             output_messages_key="answer",
        #
        #         )
        #         self.log.info("Wrapped chain with message history", session_id=self.session_id)
        #
        #     except Exception as e:
        #         self.log.error("Error initializing ConversationalRAG", error=str(e))
        #         raise CustomException("Error initializing ConversationalRAG", sys)