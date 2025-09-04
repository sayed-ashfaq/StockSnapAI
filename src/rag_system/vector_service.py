from typing import List
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config.config import settings
from logger import GLOBAL_LOGGER as logger
from exceptions.custom_exception import VectorStoreError, EmbeddingError
from utils.model_loader import ModelLoader


class VectorService:
    def __init__(self):
        try:
            self.embeddings = ModelLoader().load_llm()
            self.vector_store = None
            logger.info("Vector service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise EmbeddingError(f"Embedding initialization failed: {e}")

    def create_collection(self, document_id: str) -> None:
        """Create a new collection for a document"""
        try:
            self.vector_store = Chroma(
                collection_name=document_id,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY
            )
            logger.info(f"Created collection for document: {document_id}")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise VectorStoreError(f"Collection creation failed: {e}")

    def add_documents(self, document_id: str, documents: List[Document]) -> None:
        """Add documents to vector store"""
        try:
            if not self.vector_store or self.vector_store._collection.name != document_id:
                self.create_collection(document_id)

            self.vector_store.add_documents(documents)
            self.vector_store.persist()
            logger.info(f"Added {len(documents)} documents to collection: {document_id}")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise VectorStoreError(f"Document addition failed: {e}")

    def similarity_search(
            self,
            document_id: str,
            query: str,
            k: int = None
    ) -> List[Document]:
        """Search for similar documents"""
        try:
            k = k or settings.RETRIEVAL_K

            # Load existing collection
            vector_store = Chroma(
                collection_name=document_id,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY
            )

            results = vector_store.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(results)} documents for query in collection: {document_id}")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise VectorStoreError(f"Search failed: {e}")

    def delete_collection(self, document_id: str) -> None:
        """Delete a collection"""
        try:
            vector_store = Chroma(
                collection_name=document_id,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY
            )
            vector_store.delete_collection()
            logger.info(f"Deleted collection: {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise VectorStoreError(f"Collection deletion failed: {e}")
