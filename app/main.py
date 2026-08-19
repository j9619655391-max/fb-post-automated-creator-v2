"""FastAPI application entry point."""
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.api.routes import api_router
import app.models  # noqa: F401 - ensure all models are registered

# Configure logging (minimal but correct)
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the API; schema migrations must be applied before process startup."""
    logger.info("Database startup complete; Alembic owns schema migrations.")
    yield
    # no shutdown cleanup needed for SQLite


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
_cors_origins = ["*"] if settings.cors_origins == "*" else [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    correlation_id = str(uuid.uuid4())
    logger.warning(
        f"[{correlation_id}] Validation error on {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic ValidationError."""
    correlation_id = str(uuid.uuid4())
    logger.warning(
        f"[{correlation_id}] Pydantic validation error on {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError (business rule violations)."""
    correlation_id = str(uuid.uuid4())
    logger.warning(
        f"[{correlation_id}] ValueError on {request.url.path}: {str(exc)}"
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    correlation_id = str(uuid.uuid4())
    # Sanitize error message (don't expose internal DB details)
    error_msg = "Database integrity constraint violation"
    logger.error(
        f"[{correlation_id}] IntegrityError on {request.url.path}: {str(exc)}",
        exc_info=exc
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": error_msg,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException (pass through with correlation_id)."""
    correlation_id = str(uuid.uuid4())
    logger.info(
        f"[{correlation_id}] HTTPException {exc.status_code} on {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    correlation_id = str(uuid.uuid4())
    # Log full error with correlation_id (internal logging only)
    logger.error(
        f"[{correlation_id}] Unhandled exception on {request.url.path}",
        exc_info=exc,
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    # Return generic 500 response (no stack traces in production)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id
        }
    )


# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Optional: serve frontend (when frontend/dist exists, e.g. after npm run build)
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# Media storage static mount — resolved from project root, cross-platform
_project_root = Path(__file__).resolve().parent.parent
MEDIA_DIR = str(_project_root / settings.media_dir)
if not Path(MEDIA_DIR).exists():
    Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)

# Warn on default secret key
if settings.secret_key == "supersecretkeychangeinproduction":
    logger.warning("Using default SECRET_KEY! Change this in production via .env")

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

if _frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="assets")

    @app.get("/")
    @app.get("/{path:path}")
    async def serve_spa(path: str = ""):
        """Serve SPA index.html for non-API routes."""
        if path.startswith("api") or path in ("docs", "redoc", "openapi.json", "health"):
            raise HTTPException(status_code=404, detail="Not found")
        index_file = _frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        """Root endpoint with API information (when no frontend build)."""
        return {
            "message": "Content Automation Platform API",
            "version": settings.app_version,
            "docs": "/docs"
        }
