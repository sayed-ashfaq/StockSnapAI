import os
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.portfolio_summarizer.portfolio_sentiment import StockAnalyzer
from src.rag_system.document_service import DocumentService
from src.rag_system.vector_service import VectorService
from src.rag_system.chat_engine import ChatService
from logger import GLOBAL_LOGGER as logger

UPLOAD_BASE = os.getenv("UPLOAD_BASE", "data")

app= FastAPI(title= "Stock Snap AI",version= "1.0",)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR/'static')), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR/"templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_ui(request: Request):
    logger.info("Serving UI homepage.")
    resp = templates.TemplateResponse("dashboard_v2.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp
@app.get("/dashboard/sentiment-analysis", response_class=HTMLResponse)
async def portfolio_analysis_page(request: Request):
    logger.info("Serving UI portfolio analysis homepage.")
    resp = templates.TemplateResponse("portfolio_analysis.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp
@app.get("/dashboard/document-analysis", response_class=HTMLResponse)
async def document_analysis_page(request: Request):
    logger.info("Serving UI document analysis homepage.")
    resp = templates.TemplateResponse("chat_with_reports.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/health")
def health():
    logger.info("Health check.")
    return {"status": "ok", "service": "Stock Snap AI"}

#=============Portfolio Analyzer========================#

@app.post("/dashboard/sentiment-analysis", response_class=HTMLResponse)
async def sentiment_analysis_page(portfolio: List[str]):
    portfolio_analyzer = StockAnalyzer()
    logger.info("Running portfolio analysis on given stocks...")
    with portfolio_analyzer as analyzer:
        result = analyzer.analyze_portfolio_batch(portfolio)
    return JSONResponse(status_code=200, content=result)

#=============RAG Chat Engine============================#

