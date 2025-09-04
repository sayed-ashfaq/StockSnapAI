import time
from typing import List, Dict, Any, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from config.config import settings
from utils.model_loader import ModelLoader
from logger import GLOBAL_LOGGER as logger
from exceptions.custom_exception import ChatError
from prompts.prompt_library import RAG_PROMPT, SUMMARY_PROMPT
from src.rag_system.vector_service import VectorService
from src.rag_system.schemas import ChatMessage, ChatResponse


class ChatService:
    def __init__(self, vector_service: VectorService):
        try:
            self.llm = ModelLoader().load_llm()
            self.vector_service = vector_service
            self.output_parser = StrOutputParser()
            self.rag_prompt = RAG_PROMPT
            self.summary_prompt = SUMMARY_PROMPT
            logger.info("Chat service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}")
            raise ChatError(f"Chat service initialization failed: {e}")

    def chat_with_document(
        self,
        document_id: str,
        question: str,
        chat_history: Optional[List[ChatMessage]] = None
    ) -> ChatResponse:
        """Chat with a specific document"""
        start_time = time.time()

        try:
            # Retrieve relevant context
            retrieved_docs = self.vector_service.similarity_search(
                document_id= document_id,
                query=question,
                k=settings.RETRIEVAL_K)

            if not retrieved_docs:
                raise ChatError("No relevant context found in document")

            # Prepare context
            context = self._format_context(retrieved_docs)

            # Prepare chat history string
            history_str = ""
            if chat_history:
                for msg in chat_history:
                    history_str += f"{msg.role.upper()}: {msg.content}\n"

            # Build chain
            chain = (
                {
                    "context": RunnablePassthrough(),
                    "question": RunnablePassthrough(),
                    "chat_history": RunnablePassthrough(),
                }
                | self.rag_prompt
                | self.llm
                | self.output_parser
            )

            # Generate response
            response = chain.invoke(
                {"context": context, "question": question, "chat_history": history_str}
            )

            # Prepare sources
            sources = self._format_sources(retrieved_docs)

            response_time = int((time.time() - start_time) * 1000)
            logger.info(f"Generated response for document {document_id} in {response_time}ms")

            return ChatResponse(
                answer=response,
                sources=sources,
                response_time_ms=response_time
            )

        except Exception as e:
            logger.error(f"Chat failed for document {document_id}: {e}")
            raise ChatError(f"Chat processing failed: {e}")

    def generate_summary(self, document_id: str, content: str) -> Dict[str, Any]:
        """Generate document summary"""
        try:
            # Limit content length for summary
            max_content_length = 8000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            # Build chain
            chain = self.summary_prompt | self.llm | self.output_parser

            # Generate summary
            summary = chain.invoke({"content": content})

            # Extract key points and red flags (basic extraction)
            key_points = self._extract_key_points(summary)
            red_flags = self._extract_red_flags(summary)

            logger.info(f"Generated summary for document {document_id}")

            return {
                "summary": summary,
                "key_points": key_points,
                "red_flags": red_flags
            }

        except Exception as e:
            logger.error(f"Summary generation failed for document {document_id}: {e}")
            raise ChatError(f"Summary generation failed: {e}")

    def _format_context(self, documents: List) -> str:
        """Format retrieved documents as context"""
        context_parts = []
        for i, doc in enumerate(documents):
            context_parts.append(f"[Source {i + 1}]: {doc.page_content}")
        return "\n\n".join(context_parts)

    def _format_sources(self, documents: List) -> List[Dict[str, Any]]:
        """Format sources for response"""
        sources = []
        for i, doc in enumerate(documents):
            source = {
                "id": i + 1,
                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            }
            sources.append(source)
        return sources

    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract key points from summary (basic implementation)"""
        key_points = []
        lines = summary.split('\n')

        for line in lines:
            line = line.strip()
            if (line.startswith('- ') or line.startswith('• ') or
                    'key' in line.lower() or 'important' in line.lower()):
                key_points.append(line.lstrip('- •').strip())

        return key_points[:10]  # Limit to top 10

    def _extract_red_flags(self, summary: str) -> List[str]:
        """Extract red flags from summary (basic implementation)"""
        red_flags = []
        lines = summary.split('\n')

        red_flag_keywords = [
            'risk', 'concern', 'warning', 'decline', 'loss', 'debt',
            'litigation', 'uncertainty', 'challenge', 'problem'
        ]

        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in red_flag_keywords):
                red_flags.append(line.lstrip('- •').strip())

        return red_flags[:10]  # Limit to top 10
