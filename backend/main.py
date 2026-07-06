"""
TrustLens AI — FastAPI Backend Entry Point
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from database import init_db
from routers import analyze, history

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TrustLens AI",
    description="AI-powered deepfake & scam detection API",
    version="1.0.0",
    lifespan=lifespan,
)

logger = logging.getLogger("uvicorn.error")

# Read allowed origins from env var (comma-separated) or fall back to allow all
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# Support wildcard — if "*" is present, use it alone (CORSMiddleware requires it)
if "*" in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

# credentials can't be combined with wildcard origins (CORS spec)
_allow_credentials: bool = ALLOWED_ORIGINS != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": " ".join(error_messages)})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception during request: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


app.include_router(analyze.router)
app.include_router(history.router)


@app.get("/")
def root():
    return {
        "name": "TrustLens AI",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": ["/api/analyze/image", "/api/analyze/audio", "/api/analyze/video", "/api/analyze/text", "/api/history/"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
