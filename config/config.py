from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Document Chat API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "multimodalembedding"
    EMBEDDING_PROVIDER: str = "google-gemini"
    LLM_MODEL: str = "gpt-4o"
    LLM_PROVIDER: str = "openai"

    # Vector Store Configuration
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_K: int = 4
    ANONYMIZED_TELEMETRY:bool = False

    # File Configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".txt", ".docx", ".xlsx", ".csv", '.jpeg', '.png', '.jpg']

    # Database Configuration
    DATABASE_URL: Optional[str] = None

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
os.makedirs("logs", exist_ok=True)