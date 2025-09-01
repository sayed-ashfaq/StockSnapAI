
# modules/__init__.py
"""
AI Finance Copilot Modules

This package contains the core modules for the AI Finance Copilot application:
- stock_analyzer: Real-time stock news analysis with AI sentiment scoring
- document_chat: Upload and chat with financial documents using RAG
"""

__version__ = "1.0.0"
__author__ = "AI Finance Copilot Team"

from .stock_analyzer import StockAnalyzer
from .document_chat import DocumentChat

__all__ = ["StockAnalyzer", "DocumentChat"]