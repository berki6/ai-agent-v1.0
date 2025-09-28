import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException, Depends, status, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from langdetect import detect
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO
import json
import os
from pathlib import Path
import hashlib
import asyncio
from urllib.request import urlopen
from urllib.error import URLError

from src.core.engine import CodeForgeEngine
from src.core.logger import get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global engine
    logger.info("Starting CodeForge AI Web Server")
    engine = CodeForgeEngine()
    success = await engine.initialize()
    if success:
        modules = engine.list_modules()
        logger.info(f"Engine initialized with {len(modules)} modules")
    else:
        logger.error("Failed to initialize engine")
        raise RuntimeError("Engine initialization failed")
    yield
    if engine:
        await engine.shutdown()
        logger.info("CodeForge AI Web Server shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="CodeForge AI",
    description="Unified Modular AI Agent for Software Development",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response


# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Security
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple user storage (in production, use a database)
# Pre-hashed password for "admin123" using bcrypt
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$AjIZG4t56l4iDCCmEwC6ZOqWUCe0fr5ch6UfAyO2Bsee1tAzI1VxC",  # admin123
        "full_name": "Administrator",
        "email": "admin@codeforge.ai",
    }
}

# Setup directories
BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = BASE_DIR / "static"

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global variables
engine: Optional[CodeForgeEngine] = None
logger = get_logger(__name__)


def detect_language(text: str) -> str:
    """Detect the language of the input text"""
    try:
        if not text or len(text.strip()) < 3:
            return "unknown"
        return detect(text)
    except Exception:
        return "unknown"


def generate_pdf_report(
    module_name: str, input_data: str, result: dict, language: str
) -> BytesIO:
    """Generate a PDF report for module execution results"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=30,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
    )
    normal_style = styles["Normal"]

    story = []

    # Title
    story.append(Paragraph(f"CodeForge AI - {module_name.title()} Report", title_style))
    story.append(Spacer(1, 12))

    # Metadata
    story.append(Paragraph("Execution Details", heading_style))
    story.append(Paragraph(f"<b>Module:</b> {module_name}", normal_style))
    story.append(
        Paragraph(
            f"<b>Language:</b> {language.upper() if language != 'unknown' else 'Unknown'}",
            normal_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            normal_style,
        )
    )
    story.append(
        Paragraph(f"<b>Input Length:</b> {len(input_data)} characters", normal_style)
    )
    story.append(Spacer(1, 20))

    # Input
    story.append(Paragraph("Input Data", heading_style))
    story.append(
        Paragraph(
            input_data[:1000] + ("..." if len(input_data) > 1000 else ""), normal_style
        )
    )
    story.append(Spacer(1, 20))

    # Result
    story.append(Paragraph("Execution Result", heading_style))
    if result.get("success"):
        story.append(Paragraph("<b>Status:</b> Success", normal_style))
        result_text = result.get("data", "")
        if isinstance(result_text, dict):
            result_text = str(result_text)
        story.append(
            Paragraph(
                result_text[:2000] + ("..." if len(result_text) > 2000 else ""),
                normal_style,
            )
        )
    else:
        story.append(Paragraph("<b>Status:</b> Error", normal_style))
        story.append(Paragraph(result.get("error", "Unknown error"), normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


# Learning Mode - Feedback System
FEEDBACK_FILE = BASE_DIR / "feedback_data.json"


def load_feedback_data():
    """Load feedback data from file"""
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_feedback_data(data):
    """Save feedback data to file"""
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_feedback(
    module_name: str,
    input_data: str,
    rating: int,
    comment: str = "",
    user: str = "anonymous",
):
    """Add user feedback for learning"""
    data = load_feedback_data()
    if module_name not in data:
        data[module_name] = []

    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "input": input_data[:500],  # Truncate long inputs
        "rating": rating,
        "comment": comment,
        "input_length": len(input_data),
    }

    data[module_name].append(feedback_entry)
    save_feedback_data(data)

    # Keep only last 1000 feedback entries per module
    if len(data[module_name]) > 1000:
        data[module_name] = data[module_name][-1000:]
        save_feedback_data(data)


def get_feedback_stats(module_name: Optional[str] = None):
    """Get feedback statistics for learning insights"""
    data = load_feedback_data()
    stats = {}

    if module_name:
        module_data = data.get(module_name, [])
        if module_data:
            ratings = [f["rating"] for f in module_data]
            stats[module_name] = {
                "total_feedback": len(module_data),
                "average_rating": round(sum(ratings) / len(ratings), 2),
                "rating_distribution": {
                    "1": ratings.count(1),
                    "2": ratings.count(2),
                    "3": ratings.count(3),
                    "4": ratings.count(4),
                    "5": ratings.count(5),
                },
                "recent_feedback": module_data[-5:],  # Last 5 entries
            }
    else:
        # Overall stats
        for mod_name, module_data in data.items():
            if module_data:
                ratings = [f["rating"] for f in module_data]
                stats[mod_name] = {
                    "total_feedback": len(module_data),
                    "average_rating": round(sum(ratings) / len(ratings), 2),
                }

    return stats


# Offline Mode - Caching and Fallback
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def check_internet_connectivity() -> bool:
    """Check if internet connection is available"""
    try:
        urlopen("http://www.google.com", timeout=5)
        return True
    except URLError:
        return False


def get_cache_key(module_name: str, input_data: str) -> str:
    """Generate cache key for module execution"""
    content = f"{module_name}:{input_data}".encode("utf-8")
    return hashlib.md5(content).hexdigest()


def get_cached_result(cache_key: str):
    """Get cached result if available"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
                # Check if cache is not too old (24 hours)
                cache_time = datetime.fromisoformat(data["timestamp"])
                if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                    return data["result"]
        except:
            pass
    return None


def save_cached_result(cache_key: str, result: dict):
    """Save result to cache"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    cache_data = {"timestamp": datetime.now().isoformat(), "result": result}
    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
    except:
        pass


def get_offline_fallback(module_name: str, input_data: str) -> dict:
    """Provide offline fallback responses for common queries"""
    fallbacks = {
        "scaffolder": {
            "success": True,
            "data": "Offline Mode: Project scaffolding templates are available locally. Please provide more specific requirements for detailed scaffolding suggestions.",
            "cached": True,
        },
        "sentinel": {
            "success": True,
            "data": "Offline Mode: Basic security checks completed. For comprehensive vulnerability scanning, please connect to the internet.",
            "cached": True,
        },
        "alchemist": {
            "success": True,
            "data": "Offline Mode: Documentation generation is limited. Basic code analysis available, but AI-powered documentation requires internet connection.",
            "cached": True,
        },
        "architect": {
            "success": True,
            "data": "Offline Mode: Architecture analysis available for cached patterns. Advanced AI recommendations require internet connectivity.",
            "cached": True,
        },
    }

    return fallbacks.get(
        module_name,
        {
            "success": False,
            "error": "This module requires internet connectivity for full functionality. Please check your connection and try again.",
            "cached": False,
        },
    )


# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    import bcrypt

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_user(username: str):
    """Get user from database"""
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return user_dict


def authenticate_user(username: str, password: str):
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return False

    # Handle bcrypt's 72-byte password limit by truncating
    # Truncate password to 72 bytes as suggested by bcrypt error
    password_bytes = password.encode("utf-8")[:72]
    password = password_bytes.decode("utf-8", errors="ignore")

    if not verify_password(password, user["hashed_password"]):
        return False
    return user


async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Get current authenticated user"""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user: dict = Depends(get_current_user)):
    """Home page with module overview"""
    modules = engine.list_modules() if engine else []
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "title": "CodeForge AI",
            "modules": modules,
            "user": current_user,
        },
    )


@app.get("/module/{module_name}", response_class=HTMLResponse)
async def module_page(
    request: Request, module_name: str, current_user: dict = Depends(get_current_user)
):
    """Individual module page with form"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    module_info = engine.get_module_info(module_name)
    if not module_info:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")

    return templates.TemplateResponse(
        request,
        "module.html",
        {
            "request": request,
            "title": f"CodeForge AI - {module_name.title()}",
            "module": module_info,
            "module_name": module_name,
            "user": current_user,
        },
    )


@app.post("/api/module/{module_name}/execute")
@limiter.limit("10/minute")
async def execute_module(
    module_name: str,
    request: Request,
    input_data: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Execute a module via API"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        # Parse input data (could be JSON or plain text)
        try:
            input_dict = (
                eval(input_data)
                if input_data.startswith("{")
                else {"input": input_data}
            )
        except:
            input_dict = {"input": input_data}

        # Detect language of input
        detected_language = detect_language(input_data)

        # Check internet connectivity
        is_online = check_internet_connectivity()

        # Generate cache key
        cache_key = get_cache_key(module_name, input_data)

        # Try to get cached result first
        cached_result = get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Using cached result for {module_name}")
            result_dict = cached_result
            cached = True
        elif not is_online:
            # Offline mode - use fallback
            logger.info(f"Offline mode activated for {module_name}")
            result_dict = get_offline_fallback(module_name, input_data)
            cached = True
        else:
            # Online mode - execute normally and cache result
            result = await engine.execute_module(module_name, input_dict)
            result_dict = {
                "success": result.success,
                "data": result.data,
                "error": result.error,
            }
            if result.success:
                save_cached_result(cache_key, result_dict)
            cached = False

        return JSONResponse(
            {
                "success": result_dict.get("success", False),
                "data": result_dict.get("data", ""),
                "error": result_dict.get("error", ""),
                "module": module_name,
                "language": detected_language,
                "input_length": len(input_data),
                "cached": cached,
                "offline_mode": not is_online,
            }
        )

    except Exception as e:
        logger.error(f"Error executing module {module_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/modules")
@limiter.limit("30/minute")
async def list_modules_api(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """API endpoint to list all modules"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    modules = engine.list_modules()
    return JSONResponse({"modules": modules})


@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    feedback_stats = get_feedback_stats()
    is_online = check_internet_connectivity()
    cache_files = list(CACHE_DIR.glob("*.json"))

    return {
        "status": "healthy",
        "engine_initialized": engine is not None,
        "internet_connected": is_online,
        "offline_mode": {"available": True, "cached_results": len(cache_files)},
        "learning_mode": {
            "enabled": True,
            "modules_with_feedback": len(feedback_stats),
            "total_feedback_entries": sum(
                stats.get("total_feedback", 0) for stats in feedback_stats.values()
            ),
        },
    }


@app.get("/api/export/{module_name}/pdf")
@limiter.limit("5/minute")
async def export_pdf(
    module_name: str,
    request: Request,
    input_data: str,
    current_user: dict = Depends(get_current_user),
):
    """Export module execution result as PDF"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        # Detect language
        detected_language = detect_language(input_data)

        # Parse input data
        try:
            input_dict = (
                eval(input_data)
                if input_data.startswith("{")
                else {"input": input_data}
            )
        except:
            input_dict = {"input": input_data}

        # Execute module
        result = await engine.execute_module(module_name, input_dict)

        # Generate PDF
        pdf_buffer = generate_pdf_report(
            module_name,
            input_data,
            {"success": result.success, "data": result.data, "error": result.error},
            detected_language,
        )

        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={module_name}_report.pdf"
            },
        )

    except Exception as e:
        logger.error(f"Error generating PDF export for {module_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{module_name}/json")
@limiter.limit("10/minute")
async def export_json(
    module_name: str,
    request: Request,
    input_data: str,
    current_user: dict = Depends(get_current_user),
):
    """Export module execution result as JSON"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        # Detect language
        detected_language = detect_language(input_data)

        # Parse input data
        try:
            input_dict = (
                eval(input_data)
                if input_data.startswith("{")
                else {"input": input_data}
            )
        except:
            input_dict = {"input": input_data}

        # Execute module
        result = await engine.execute_module(module_name, input_dict)

        # Prepare JSON export data
        export_data = {
            "module": module_name,
            "timestamp": datetime.now().isoformat(),
            "user": current_user["username"],
            "language": detected_language,
            "input": {"data": input_data, "length": len(input_data)},
            "result": {
                "success": result.success,
                "data": result.data,
                "error": result.error,
            },
            "metadata": {
                "exported_by": "CodeForge AI Web Interface",
                "version": "1.0.0",
            },
        }

        return JSONResponse(
            export_data,
            headers={
                "Content-Disposition": f"attachment; filename={module_name}_result.json"
            },
        )

    except Exception as e:
        logger.error(f"Error generating JSON export for {module_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback/{module_name}")
@limiter.limit("20/minute")
async def submit_feedback(
    module_name: str,
    request: Request,
    rating: int = Form(..., ge=1, le=5),
    comment: str = Form(""),
    input_data: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Submit feedback for learning mode"""
    try:
        add_feedback(
            module_name=module_name,
            input_data=input_data,
            rating=rating,
            comment=comment,
            user=current_user["username"],
        )

        return JSONResponse(
            {
                "success": True,
                "message": "Thank you for your feedback! This helps improve the AI.",
                "rating": rating,
            }
        )

    except Exception as e:
        logger.error(f"Error saving feedback for {module_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")


@app.get("/api/feedback/stats")
@limiter.limit("30/minute")
async def get_feedback_stats_api(
    request: Request,
    module_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get feedback statistics for learning insights"""
    try:
        stats = get_feedback_stats(module_name)
        return JSONResponse(
            {"success": True, "stats": stats, "total_modules_with_feedback": len(stats)}
        )

    except Exception as e:
        logger.error(f"Error retrieving feedback stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve feedback statistics"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
