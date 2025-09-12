from __future__ import annotations
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Iterable, List, Tuple

from fastapi import UploadFile

from logger import GLOBAL_LOGGER as log
from src.rag_system.schemas import FileType
from exceptions.custom_exception import DocumentPortalException
import hashlib
import mimetypes
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}
IST= ZoneInfo("Asia/Kolkata")


# ----------------------------- #
# Helpers (file I/O + loading)  #
# ----------------------------- #
def generate_document_id(filename: str, file_content: bytes) -> str:
    """Generate unique document ID based on filename and content hash"""
    content_hash = hashlib.md5(file_content).hexdigest()[:8]
    return f"{Path(filename).stem}_{content_hash}_{uuid.uuid4().hex[:8]}"


def get_file_type(filename: str) -> Tuple[FileType, str]:
    """Get file type and MIME type from filename"""
    ext = Path(filename).suffix.lower()
    mime_type, _ = mimetypes.guess_type(filename)

    type_mapping = {
        '.pdf': FileType.PDF,
        '.txt': FileType.TXT,
        '.docx': FileType.DOCX,
        '.xlsx': FileType.EXCEL,
        '.csv': FileType.CSV,
    }

    return type_mapping.get(ext, FileType.TXT), mime_type or 'application/octet-stream'


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
def generate_session_id(prefix: str = "session") -> str:
    return f"{prefix}_{datetime.now(IST).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

def save_uploaded_files(uploaded_files: Iterable, target_dir: Path) -> List[Path]:
    """Save uploaded files (Streamlit-like) and return local paths."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        saved: List[Path] = []
        for uf in uploaded_files:
            name = getattr(uf, "name", "file")
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                log.warning("Unsupported file skipped", filename=name)
                continue
            # Clean file name (only alphanum, dash, underscore)
            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(name).stem).lower()
            fname = f"{safe_name}_{uuid.uuid4().hex[:6]}{ext}"
            fname = f"{uuid.uuid4().hex[:8]}{ext}"
            out = target_dir / fname
            with open(out, "wb") as f:
                if hasattr(uf, "read"):
                    f.write(uf.read())
                else:
                    f.write(uf.getbuffer())  # fallback
            saved.append(out)
            log.info("File saved for ingestion", uploaded=name, saved_as=str(out))
        return saved
    except Exception as e:
        log.error("Failed to save uploaded files", error=str(e), dir=str(target_dir))
        raise DocumentPortalException("Failed to save uploaded files", e) from e


# ---------- Helpers ----------
class FastAPIFileAdapter:
    """Adapt FastAPI UploadFile -> .name + .getbuffer() API"""
    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename
    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()

def read_pdf_via_handler(handler, path: str) -> str:
    if hasattr(handler, "read_pdf"):
        return handler.read_pdf(path)  # type: ignore
    if hasattr(handler, "read_"):
        return handler.read_(path)  # type: ignore
    raise RuntimeError("DocHandler has neither read_pdf nor read_ method.")