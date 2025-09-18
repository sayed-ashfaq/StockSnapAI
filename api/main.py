import os
import tempfile
from datetime import datetime
from typing import List, Any

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
from utils.document_ops import FastAPIFileAdapter
from utils.files_io import save_uploaded_files, get_file_type, generate_document_id

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

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    logger.info("Serving UI homepage.")
    resp = templates.TemplateResponse("dashboard_v2.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp
@app.get("/sentiment-analysis", response_class=HTMLResponse)
async def portfolio_analysis_page(request: Request):
    logger.info("Serving UI portfolio analysis homepage.")
    resp = templates.TemplateResponse("portfolio_analysis.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp
@app.get("/document-analysis", response_class=HTMLResponse)
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

@app.post("/sentiment-analysis", response_class=HTMLResponse)
async def sentiment_analysis_page(portfolio: List[str]):
    portfolio_analyzer = StockAnalyzer()
    logger.info("Running portfolio analysis on given stocks...")
    with portfolio_analyzer as analyzer:
        result = analyzer.analyze_portfolio_batch(portfolio)
    return JSONResponse(status_code=200, content=result)

#=============RAG Chat Engine============================#
processed_documents= {}

# get the uploaded file
@app.post("/document-analysis")
async def upload_document(file: UploadFile = File(...)) -> Any:
    logger.info("Received upload file for chat with report: {}".format(file.filename))

    document_service = DocumentService()
    vector_service = VectorService()
    chat_service = ChatService(vector_service)

    MAX_FILE_SIZE = 1024 * 1024 * 200
    # get file type
    file_type, mime_type= get_file_type(file.filename)

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    document_id = generate_document_id(file.filename, file_content)

    # create temporary file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix= Path(file.filename).suffix) as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name

    try:
        logger.info(f"Processing Document: {file.filename}")
        documents, metadata= document_service.process_single_file(tmp_file_path,file_type)

        if not documents:
            raise HTTPException(status_code=400, detail="No content could be extracted from the document")

        # store document info
        doc_info = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_type.value,
            "processed_at": datetime.now(),
            "chunk_count": len(documents),
            "has_image": metadata.get("has_images", False),
            "image_count": metadata.get("extracted_images", 0),
            # "user_session": user_session
        }

        # store in vector database with
        vector_service.add_documents(document_id=f"testing_document_{document_id}", documents=documents)

        # generate summary
        summary_content = "\n\n".join([doc.page_content for doc in documents])
        summary_response = chat_service.generate_summary(document_id=f"testing_document_{document_id}", content= summary_content)

        # extract summary
        summary_text= summary_response.get("summary", "Document processed successfully")

        # Generate key highlights based on document type and content
        highlights = generate_highlights(file.filename, metadata, doc_info)

        # Store processed document info with user session
        # processed_documents[user_doc_key] = {
        #     "summary": summary_text,
        #     "highlights": highlights,
        #     "metadata": doc_info,
        #     "processed_at": datetime.now().isoformat()
        # }

        logger.info(f"Successfully processed document: {file.filename} with ID: {document_id}")

        return JSONResponse({
            "success": True,
            "document_id": document_id,
            "summary": summary_text,
            "highlights": highlights,
            "metadata": {
                "filename": file.filename,
                "file_type": file_type.value,
                "chunk_count": len(documents),
                "has_images": metadata.get("has_images", False),
                "image_count": metadata.get("extracted_images", 0)
            }
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {e}")
    finally:
        os.unlink(tmp_file_path)

def generate_highlights(filename: str, metadata: dict, doc_info: dict) -> list:
    """
    Generate key highlights based on document type and content
    """
    highlights = []

    # Add processing info
    highlights.append(f"Document processed successfully with {doc_info['chunk_count']} text chunks")

    # File type specific highlights
    filename_lower = filename.lower()
    if 'annual' in filename_lower or '10k' in filename_lower:
        highlights.extend([
            "Annual report detected - Financial statements and performance metrics available",
            "Strategic information and business outlook included",
            "Regulatory compliance and risk factors documented"
        ])
    elif 'earnings' in filename_lower:
        highlights.extend([
            "Earnings report detected - Quarterly/Annual performance data available",
            "Revenue, profit, and key financial metrics included",
            "Management commentary and guidance available"
        ])
    elif 'audit' in filename_lower:
        highlights.extend([
            "Audit report detected - Independent verification of financial statements",
            "Auditor opinions and findings available",
            "Compliance and internal control assessments included"
        ])
    else:
        highlights.extend([
            "Financial document processed - Ready for analysis and questions",
            "Key metrics and insights available for extraction"
        ])

    # Image content highlights
    if metadata.get("has_images", False):
        image_count = metadata.get("extracted_images", 0)
        highlights.append(f"Document contains {image_count} images/charts for visual analysis")

    # Add ready status
    highlights.append("Ready for detailed Q&A and financial analysis")

    return highlights



