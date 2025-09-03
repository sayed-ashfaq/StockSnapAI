from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Filetype(str, Enum):
    PDF= "pdf"
    TXT = "txt"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    MARKDOWN = "md"
    IMAGE = ('png', 'jpg', 'jpeg')

class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    SUCCESS = "success"

class DocumentUploadResponse(BaseModel):
    documentId: str
    filename: str
    fileType: Filetype
    status: DocumentStatus
    processed_at: Optional[datetime]= None
    summary: Optional[str]= None
    chunk_count: Optional[int]= None

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender(user/assia")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime= Field(..., description=datetime.now().isoformat())

class ChatRequest(BaseModel):
    document_id: str = Field(..., description="Document ID of the message")
    question: str = Field(..., min_length=1, max_length=1000)
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: Optional[float]= None
    response_time_ms: int
