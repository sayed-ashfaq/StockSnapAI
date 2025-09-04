import time
from typing import List, Dict, Any, Optional
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from config.config import settings
from logger import GLOBAL_LOGGER as logger
from exceptions.custom_exception import ChatError
from src.rag_system.vector_service import ChromaManager
from src.rag_system.schemas import ChatMessage, ChatResponse

logger = setup_logger(__name__)


class ChatService:
    def __init__(self, vector_service: VectorService):
        try:
            self.llm = init_chat_model(
                model=settings.LLM_MODEL,
                model_provider=settings.LLM_PROVIDER,
                openai_api_key=settings.OPENAI_API_KEY
            )
            self.vector_service = vector_service
            self.output_parser = StrOutputParser()
            self._setup_prompts()
            logger.info("Chat service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}")
            raise ChatError(f"Chat service initialization failed: {e}")

    def _setup_prompts(self):
        """Setup prompt templates"""
        # RAG prompt for document Q&A
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant specialized in analyzing financial and business documents. 
            Use the provided context to answer questions accurately and provide insights.

            Guidelines:
            - Answer based primarily on the provided context
            - If information is not in the context, clearly state this
            - Provide specific citations when possible
            - Highlight important financial metrics, trends, and red flags
            - Be concise but comprehensive
            - Focus on factual information from the documents

            Context: {context}"""),
            ("human", "{question}")
        ])

        # Summary prompt
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst. Create a comprehensive summary of the provided document.

            Structure your summary with these sections:
            1. **Document Type & Overview**: Identify the document type and main purpose
            2. **Key Financial Highlights**: Important metrics, performance indicators
            3. **Key Points**: Main findings, decisions, or statements
            4. **Red Flags & Concerns**: Potential risks, warnings, or concerning trends
            5. **Future Outlook**: Forward-looking statements or guidance

            Be specific and include actual numbers/percentages when available.
            Focus on actionable insights and important details."""),
            ("human", "Summarize this document:\n\n{content}")
        ])

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
                document_id, question, k=settings.RETRIEVAL_K
            )

            if not retrieved_docs:
                raise ChatError("No relevant context found in document")

            # Prepare context
            context = self._format_context(retrieved_docs)

            # Build chain
            chain = (
                    {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                    | self.rag_prompt
                    | self.llm
                    | self.output_parser
            )

            # Generate response
            response = chain.invoke({"context": context, "question": question})

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