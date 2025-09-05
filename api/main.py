from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # your app URL

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Session management (in production, use proper session store)
active_sessions = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Protected dashboard"""
    session_token = request.cookies.get("session_token")

    if not session_token or session_token not in active_sessions:
        return RedirectResponse(url="/", status_code=302)

    user_data = active_sessions[session_token]
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user_data})


@app.post("/auth/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    """Sign up with email/password"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            return {"message": "Check your email for confirmation link"}
        raise HTTPException(status_code=400, detail="Signup failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/signin")
async def signin(request: Request, email: str = Form(...), password: str = Form(...)):
    """Sign in with email/password"""
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
                secure=False,  # set True if using HTTPS
                samesite="lax"
            )
            return redirect_response
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid login"})


@app.get("/auth/google")
async def google_auth():
    """Redirect to Google OAuth via Supabase"""
    redirect_to = f"{BASE_URL}/auth/callback"
    oauth_url = (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider=google&redirect_to={redirect_to}"
    )
    return RedirectResponse(url=oauth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle Supabase OAuth callback"""
    access_token = request.query_params.get("access_token")
    refresh_token = request.query_params.get("refresh_token")

    if access_token:
        try:
            response = supabase.auth.get_user(access_token)
            if response.user:
                active_sessions[access_token] = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "provider": "google"
                }
                redirect_response = RedirectResponse(url="/dashboard", status_code=302)
                redirect_response.set_cookie(
                    key="session_token",
                    value=access_token,
                    httponly=True,
                    secure=False,  # set True if using HTTPS
                    samesite="lax"
                )
                return redirect_response
        except Exception:
            pass

    return RedirectResponse(url="/?error=auth_failed")


@app.post("/auth/signout")
async def signout(request: Request):
    """Sign out"""
    session_token = request.cookies.get("session_token")
    if session_token:
        active_sessions.pop(session_token, None)
        try:
            supabase.auth.sign_out()
        except:
            pass
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_token")
    return response


@app.get("/auth/user")
async def get_user(request: Request):
    """Return current user info"""
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in active_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return active_sessions[session_token]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
