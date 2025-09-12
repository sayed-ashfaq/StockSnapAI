from fastapi import FastAPI,File ,Request, Form, HTTPException, Depends, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware
from src.portfolio_summarizer.schemas import PortfolioAnalysisResponse
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel
import logging
import json
import tempfile
from datetime import datetime

# Portfolio Analyzer
from src.portfolio_summarizer.portfolio_sentiment import StockAnalyzer
from src.rag_system.chat_engine import ChatService
from src.rag_system.document_service import DocumentService
from src.rag_system.vector_service import VectorService
from utils.files_io import generate_document_id, get_file_type

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mount static and templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Session management (demo only)
active_sessions = {}

# Add CORS middleware - CRITICAL for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------ ROUTES ------------------ #

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main landing/login page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard page"""
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in active_sessions:
        return RedirectResponse(url="/", status_code=302)
    user_data = active_sessions[session_token]
    return templates.TemplateResponse("dashboard_v2.html", {"request": request, "user": user_data})


@app.get("/dashboard/sentiment-analysis", response_class=HTMLResponse)
async def portfolio_analysis_page(request: Request):
    """Serve the portfolio analysis HTML page"""
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in active_sessions:
        return RedirectResponse(url="/", status_code=302)
    user_data = active_sessions[session_token]
    return templates.TemplateResponse("portfolio_analysis.html", {"request": request, "user": user_data})


@app.get("/dashboard/document-analysis", response_class=HTMLResponse)
async def document_analysis_page(request: Request):
    """Serve the document analysis HTML page"""
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in active_sessions:
        return RedirectResponse(url="/", status_code=302)
    user_data = active_sessions[session_token]
    return templates.TemplateResponse("chat_with_reports.html", {"request": request, "user": user_data})


# ========== AUTH ========== #
@app.post("/auth/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    """Handle user signup"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            return {"message": "Check your email for confirmation link"}
        raise HTTPException(status_code=400, detail="Signup failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/signin")
async def signin(request: Request, email: str = Form(...), password: str = Form(...)):
    """Handle user signin"""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            session_token = response.session.access_token
            active_sessions[session_token] = {
                "id": response.user.id,
                "email": response.user.email,
                "provider": "email"
            }
            redirect_response = RedirectResponse(url="/dashboard", status_code=302)
            redirect_response.set_cookie(
                key="session_token",
                value=session_token,
                httponly=True,
                secure=False,
                samesite="lax"
            )
            return redirect_response
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid login"})


@app.post("/auth/logout")
async def logout(request: Request):
    """Handle user logout"""
    session_token = request.cookies.get("session_token")
    if session_token and session_token in active_sessions:
        del active_sessions[session_token]

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_token")
    return response


# ================= PORTFOLIO ANALYSIS API ================= #

def create_stock_analyzer(session_id: Optional[str] = None) -> StockAnalyzer:
    """Factory function to create PortfolioAnalyzer instance"""
    return StockAnalyzer(session_id=session_id)


def get_current_user_session(request: Request) -> Optional[str]:
    """Extract user session from request cookies"""
    session_token = request.cookies.get("session_token")
    if session_token and session_token in active_sessions:
        return active_sessions[session_token]["id"]
    return None


@app.post("/dashboard/sentiment-analysis", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(
        request: Request,
        stocks: List[str]  # This will directly accept the JSON array from frontend
):
    """
    Analyze a batch of stocks and return sentiment + summary
    Frontend will call this with a JSON body: ["AAPL", "TSLA", "NVDA"]
    """
    try:
        # Get user session for tracking
        user_session = get_current_user_session(request)

        # Validate input
        if not stocks or len(stocks) == 0:
            raise HTTPException(status_code=400, detail="No stocks provided for analysis")

        if len(stocks) > 20:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Too many stocks. Maximum 20 stocks allowed per analysis")

        # Sanitize stock symbols
        cleaned_stocks = [stock.strip().upper() for stock in stocks if stock.strip()]

        if not cleaned_stocks:
            raise HTTPException(status_code=400, detail="No valid stock symbols provided")

        logger.info(f"Analyzing portfolio for user {user_session}: {cleaned_stocks}")

        # Create analyzer and get results
        with create_stock_analyzer(session_id=user_session) as analyzer:
            result = analyzer.analyze_portfolio_batch(cleaned_stocks)

            # Transform the result to match our response model structure
            transformed_result = transform_analysis_result(result, cleaned_stocks)

            logger.info(f"Portfolio analysis completed for {len(cleaned_stocks)} stocks")
            print("============result================")
            print(result)
            return JSONResponse(content=transformed_result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

def transform_analysis_result(result: dict, requested_stocks: List[str]) -> dict:
    """
    Transform analyzer result into format expected by the frontend
    (summary + themes + stocks)
    """
    try:
        return result
    except Exception as e:
        logger.error(f"Error transforming analysis result: {str(e)}")
        # fallback
        return result

# def transform_analysis_result(result: dict, requested_stocks: List[str]) -> dict:
#     """
#     Transform the analyzer result into the format expected by the frontend
#     """
#     try:
#         # Extract data from the results
#         portfolio_content= result.get("portfolio_analysis")
#         stocks_data = result.get("portfolio_analysis").get('stocks', [])
#         summary_data = result.get("portfolio_analysis").get("overall_insights",{})
#         themes_data = result.get('themes', {})
#
#         # Process individual stocks
#         transformed_stocks = []
#         for stock_data in stocks_data:
#             transformed_stock = {
#                 "symbol": stock_data.get('ticker', 'Invalid StockName'),
#                 "sentiment": stock_data.get('market_sentiment', 'NEUTRAL'),
#                 "impact": stock_data.get('impact', 'NEUTRAL'),
#                 "category": stock_data.get('category', 'General'),
#                 "summary": stock_data.get("portfolio_insights")
#             }
#             transformed_stocks.append(transformed_stock)
#
#         # Process summary
#         transformed_summary = {
#             "totalStocks": len(result.get("portfolio_analysis").get("stocks",[])),
#             "avgSentiment": summary_data.get('avgSentiment', 'N/A'),
#             "riskLevel": summary_data.get('riskLevel', 'Moderate'),
#             "description": summary_data.get('description', 'Portfolio analysis completed')
#         }
#
#         # Process themes
#         transformed_themes = {
#             "risks": themes_data.get('risks', ["Market volatility may affect portfolio performance"]),
#             "opportunities": themes_data.get('opportunities',
#                                              ["Diversification across sectors provides growth potential"]),
#             "general": themes_data.get('general', ["Mixed sentiment across selected stocks"])
#         }
#
#         return {
#             "summary": transformed_summary,
#             "themes": transformed_themes,
#             "stocks": transformed_stocks
#         }
#
#     except Exception as e:
#         logger.error(f"Error transforming analysis result: {str(e)}")
#         # Return fallback structure
#         return {
#             "summary": {
#                 "totalStocks": len(requested_stocks),
#                 "avgSentiment": "N/A",
#                 "riskLevel": "Unknown",
#                 "description": "Analysis completed with limited data"
#             },
#             "themes": {
#                 "risks": ["Unable to determine specific risks"],
#                 "opportunities": ["Analysis incomplete"],
#                 "general": ["Portfolio analysis encountered issues"]
#             },
#             "stocks": [
#                 {
#                     "symbol": symbol,
#                     "sentiment": "UNKNOWN",
#                     "impact": "UNKNOWN",
#                     "category": "General",
#                     "summary": f"Analysis incomplete for {symbol}"
#                 }
#                 for symbol in requested_stocks
#             ]
#         }

# ================= RAG Chat Engine API ================= #

# Initialize RAG services
document_service = DocumentService()
vector_service = VectorService()
chat_service = ChatService(vector_service)

# Store for processed documents (in production, use a proper database)
processed_documents = {}


# Replace your incomplete upload_document function with this complete implementation:

@app.post('/dashboard/document-analysis/upload')
async def upload_document(request: Request, file: UploadFile = File(...)):
    """
    Upload and process a document for RAG analysis
    """
    try:
        # Check if user is authenticated
        user_session = get_current_user_session(request)
        if not user_session:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Validate file size (200MB limit as per frontend)
        MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
        file_content = await file.read()

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 200MB.")

        # Reset file pointer
        await file.seek(0)

        # Get file type
        file_type, mime_type = get_file_type(file.filename)

        # Generate document ID
        document_id = generate_document_id(file.filename, file_content)

        # Check if document already processed for this user
        user_doc_key = f"{user_session}_{document_id}"
        if user_doc_key in processed_documents:
            return JSONResponse({
                "success": True,
                "document_id": document_id,
                "message": "Document already processed",
                "summary": processed_documents[user_doc_key]["summary"],
                "highlights": processed_documents[user_doc_key]["highlights"],
                "metadata": processed_documents[user_doc_key]["metadata"]
            })

        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            # Process the document using your existing service
            logger.info(f"Processing document: {file.filename} for user: {user_session}")
            documents, metadata = document_service.process_single_file(temp_file_path, file_type)

            if not documents:
                raise HTTPException(status_code=400, detail="No content could be extracted from the document")

            # Create document info
            doc_info = {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_type.value,
                "processed_at": datetime.now(),
                "chunk_count": len(documents),
                "has_images": metadata.get("has_images", False),
                "image_count": metadata.get("extracted_images", 0),
                "user_session": user_session
            }

            # Store in vector database with user-specific document ID
            vector_service.add_documents(f"{user_session}_{document_id}", documents)

            # Generate summary using first few chunks (similar to your notebook)
            summary_content = "\n\n".join([doc.page_content for doc in documents[:3]])
            summary_response = chat_service.generate_summary(f"{user_session}_{document_id}", summary_content)

            # Extract summary
            summary_text = summary_response.get("summary", "Document processed successfully")

            # Generate key highlights based on document type and content
            highlights = generate_highlights(file.filename, metadata, doc_info)

            # Store processed document info with user session
            processed_documents[user_doc_key] = {
                "summary": summary_text,
                "highlights": highlights,
                "metadata": doc_info,
                "processed_at": datetime.now().isoformat()
            }

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

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post('/dashboard/document-analysis/chat')
async def chat_with_document(
        request: Request,
        document_id: str = Form(...),
        message: str = Form(...),
        chat_history: Optional[str] = Form(default="[]")
):
    """
    Chat with a processed document
    """
    try:
        # Check if user is authenticated
        user_session = get_current_user_session(request)
        if not user_session:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Create user-specific document key
        user_doc_key = f"{user_session}_{document_id}"

        # Validate document exists for this user
        if user_doc_key not in processed_documents:
            raise HTTPException(status_code=404, detail="Document not found. Please upload the document first.")

        # Parse chat history
        try:
            history = json.loads(chat_history) if chat_history else []
        except json.JSONDecodeError:
            history = []

        logger.info(f"Chat request for document {document_id} from user {user_session}: {message}")

        # Get response from chat service using user-specific document ID
        response = chat_service.chat_with_document(user_doc_key, message)

        # Update chat history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})

        return JSONResponse({
            "success": True,
            "response": response,
            "chat_history": history,
            "document_id": document_id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get('/dashboard/document-analysis/{document_id}/info')
async def get_document_info(request: Request, document_id: str):
    """
    Get information about a processed document
    """
    try:
        user_session = get_current_user_session(request)
        if not user_session:
            raise HTTPException(status_code=401, detail="Authentication required")

        user_doc_key = f"{user_session}_{document_id}"

        if user_doc_key not in processed_documents:
            raise HTTPException(status_code=404, detail="Document not found")

        return JSONResponse({
            "success": True,
            "document_info": processed_documents[user_doc_key]
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving document info: {str(e)}")


@app.delete('/dashboard/document-analysis/{document_id}')
async def delete_document(request: Request, document_id: str):
    """
    Delete a processed document and its vectors
    """
    try:
        user_session = get_current_user_session(request)
        if not user_session:
            raise HTTPException(status_code=401, detail="Authentication required")

        user_doc_key = f"{user_session}_{document_id}"

        if user_doc_key not in processed_documents:
            raise HTTPException(status_code=404, detail="Document not found")

        # Remove from vector database
        vector_service.delete_document(user_doc_key)

        # Remove from local storage
        del processed_documents[user_doc_key]

        logger.info(f"Deleted document: {document_id} for user: {user_session}")

        return JSONResponse({
            "success": True,
            "message": "Document deleted successfully"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


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




# ================= ADDITIONAL HELPER ROUTES ================= #

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors by showing a custom page"""
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


# ------------------ SERVER ------------------ #
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)