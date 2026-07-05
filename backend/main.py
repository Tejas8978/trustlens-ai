"""
TrustLens AI — FastAPI Backend Entry Point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Read allowed origins from env var (comma-separated) or fall back to allow all
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# Support wildcard — if "*" is present, use it alone (CORSMiddleware requires it)
if "*" in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOWED_ORIGINS != ["*"],  # credentials can't be used with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
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
