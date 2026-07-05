"""
TrustLens AI — FastAPI Backend Entry Point
"""
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
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
