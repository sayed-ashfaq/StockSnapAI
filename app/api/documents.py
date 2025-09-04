import os
import tempfile
from typing import List
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form

from src.rag_system.document_service import DocumentService
from src.rag_system.vector_service import VectorService
from src.rag_system.chat_engine import ChatService
from utils.files_io import generate_document_id, get_file_type, format_file_size
from exceptions.custom_exception import (
    create_http_exception,
    FileProcessingError,
    VectorStoreError,
)
from logger import GLOBAL_LOGGER as logger
from config.config import settings
# from src.rag_system.schemas import DocumentUploadResponse   # Uncomment when schema is ready

router = APIRouter()


# Dependency injection
def get_document_service():
    return DocumentService()


def get_vector_service():
    return VectorService()


def get_chat_service(vector_service: VectorService = Depends(get_vector_service)):
    return ChatService(vector_service)


# ---------------- Single Document Upload ---------------- #
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    vector_service: VectorService = Depends(get_vector_service),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Upload and process a single document"""
    try:
        # Validate file
        if not file.filename:
            raise create_http_exception(400, "No filename provided")

        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise create_http_exception(
                413,
                f"File too large. Max size: {format_file_size(settings.MAX_FILE_SIZE)}"
            )

        # Validate file type
        file_type, mime_type = get_file_type(file.filename)
        if Path(file.filename).suffix.lower() not in settings.ALLOWED_EXTENSIONS:
            raise create_http_exception(
                400,
                f"File type not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Generate document ID
        document_id = generate_document_id(file.filename, file_content)

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type.value}") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        try:
            # Process file
            documents, metadata = document_service.process_file(tmp_file_path, file_type)

            # Document info
            document_info = {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_type.value,
                "processed_at": datetime.now(),
                "chunk_count": len(documents),
                "has_images": metadata.get("has_images", False),
                "image_count": metadata.get("extracted_images", 0),
            }

            # Add to vector DB
            vector_service.add_single_document(document_id, documents, document_info)

            # Generate summary (using first few chunks)
            try:
                summary_content = "\n\n".join([doc.page_content for doc in documents[:3]])
                summary_data = chat_service.generate_summary(document_id, summary_content)
                document_info["summary"] = summary_data.get("summary", "")
            except Exception as e:
                logger.warning(f"Summary generation failed for {document_id}: {e}")
                document_info["summary"] = "Summary generation failed"

            logger.info(f"Successfully processed document {document_id}: {file.filename}")

            return {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_type.value,
                "status": "ready",
                "processed_at": document_info["processed_at"],
                "summary": document_info.get("summary"),
                "chunk_count": len(documents),
            }

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except FileProcessingError as e:
        logger.error(f"File processing failed for {file.filename}: {e}")
        raise create_http_exception(400, str(e), "FILE_PROCESSING_ERROR")
    except VectorStoreError as e:
        logger.error(f"Vector store error for {file.filename}: {e}")
        raise create_http_exception(500, str(e), "VECTOR_STORE_ERROR")
    except Exception as e:
        logger.error(f"Unexpected error during upload of {file.filename}: {e}")
        raise create_http_exception(500, "Internal server error", "UPLOAD_ERROR")


# ---------------- Batch Upload ---------------- #
@router.post("/upload-batch")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    collection_name: str = Form(None),
    document_service: DocumentService = Depends(get_document_service),
    vector_service: VectorService = Depends(get_vector_service),
):
    """Upload multiple documents at once"""
    successful_uploads = []
    failed_uploads = []
    files_data = []

    # Validate files
    for file in files:
        try:
            if not file.filename:
                failed_uploads.append({"filename": "unknown", "error": "No filename provided"})
                continue

            file_content = await file.read()
            if len(file_content) > settings.MAX_FILE_SIZE:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": f"File too large. Max size: {format_file_size(settings.MAX_FILE_SIZE)}"
                })
                continue

            file_type, _ = get_file_type(file.filename)
            if Path(file.filename).suffix.lower() not in settings.ALLOWED_EXTENSIONS:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": f"File type not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                })
                continue

            files_data.append((file.filename, file_content, file_type.value))

        except Exception as e:
            failed_uploads.append({"filename": file.filename, "error": str(e)})

    if not files_data:
        raise create_http_exception(400, "No valid files to process")

    try:
        all_documents, document_infos = document_service.process_multiple_files(files_data)

        if not all_documents:
            raise create_http_exception(400, "Failed to process any documents")

        collection_id = vector_service.add_documents_batch(
            all_documents, [info.dict() for info in document_infos]
        )
        successful_uploads = document_infos

        logger.info(f"Batch upload completed: {len(successful_uploads)} successful, {len(failed_uploads)} failed")

        return {
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "collection_id": collection_id,
            "message": f"Processed {len(successful_uploads)} files successfully",
        }

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise create_http_exception(500, f"Batch processing failed: {e}")


# ---------------- Database Upload ---------------- #
@router.post("/upload-database")
async def upload_from_database(
    db_connection: str = Form(...),
    query: str = Form(None),
    table_name: str = Form(None),
    document_service: DocumentService = Depends(get_document_service),
    vector_service: VectorService = Depends(get_vector_service),
):
    """Upload data directly from a database query or table"""
    try:
        if not query and not table_name:
            raise create_http_exception(400, "Either 'query' or 'table_name' must be provided")

        # Process DB content
        documents, metadata = document_service.process_database_query(db_connection, query, table_name)

        # Generate doc ID
        source_name = table_name or "database_query"
        content_hash = hash(query or table_name)
        document_id = f"db_{source_name}_{abs(content_hash)}"

        doc_info = {
            "document_id": document_id,
            "filename": f"{source_name}.db",
            "file_type": "database",
            "processed_at": datetime.now(),
            "chunk_count": len(documents),
            "has_images": False,
            "image_count": 0,
            "metadata": metadata,
        }

        # Add to vector store
        vector_service.add_single_document(document_id, documents, doc_info)

        logger.info(f"Database content uploaded: {document_id}")

        return {
            "document_id": document_id,
            "filename": doc_info["filename"],
            "file_type": "database",
            "status": "ready",
            "processed_at": doc_info["processed_at"],
            "chunk_count": len(documents),
            "rows": metadata.get("rows", 0),
            "columns": metadata.get("columns", 0),
        }

    except Exception as e:
        logger.error(f"Database upload failed: {e}")
        raise create_http_exception(500, f"Database processing failed: {e}")
