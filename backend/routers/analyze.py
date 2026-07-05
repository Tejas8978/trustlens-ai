"""
Analysis router — handles all /api/analyze/* endpoints
"""
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, ScanLog
from schemas import AnalysisResult, EvidenceItem
from analyzers.image_analyzer import analyze_image
from analyzers.audio_analyzer import analyze_audio
from analyzers.video_analyzer import analyze_video
from analyzers.text_analyzer import analyze_text

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

AI_PROMPTS = {
    "image": (
        "You are an image forensics AI. Analyze the provided image for signs of AI generation "
        "or manipulation using Error Level Analysis, metadata inspection, GAN artifact detection, "
        "and facial consistency checks. Return a structured JSON report with: risk_score (0-100), "
        "verdict (SAFE/SUSPICIOUS/HIGH_RISK), evidence list, and recommended actions."
    ),
    "audio": (
        "You are a voice authentication AI. Analyze the audio for signs of AI voice synthesis "
        "or deepfake cloning using MFCC analysis, spectral flatness, pitch monotonicity, "
        "silence distribution, and prosody patterns. Return a structured JSON report with: "
        "risk_score (0-100), verdict (SAFE/SUSPICIOUS/HIGH_RISK), evidence list, and actions."
    ),
    "video": (
        "You are a video deepfake detection AI. Analyze the video frames for facial manipulation, "
        "GAN artifacts, temporal inconsistencies, and audio-visual sync issues. Sample key frames "
        "and run per-frame analysis. Return: risk_score (0-100), verdict, frame-level evidence."
    ),
    "sms": (
        "You are a fraud detection AI specializing in SMS scam analysis. Detect urgency tactics, "
        "reward lures, threatening language, suspicious URLs, brand impersonation, and requests "
        "for sensitive information. Return: risk_score (0-100), verdict, evidence, recommendations."
    ),
    "email": (
        "You are a phishing email detection AI. Analyze the email for spoofed sender domains, "
        "malicious links, impersonated brands, credential harvesting language, and social engineering "
        "patterns. Cross-reference with known phishing signatures. Return structured threat report."
    ),
}


def _save_scan(db: Session, result: dict, scan_type: str, filename: str | None):
    log = ScanLog(
        scan_type=scan_type,
        filename=filename,
        risk_score=result["risk_score"],
        verdict=result["verdict"],
        summary=result["summary"],
        details=json.dumps([
            (e.model_dump() if hasattr(e, "model_dump") else (e.dict() if hasattr(e, "dict") else e))
            for e in result["evidence"]
        ]),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.post("/image", response_model=AnalysisResult)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")

    result = analyze_image(content, file.filename or "upload.jpg")
    result["scan_type"] = "image"
    result["filename"] = file.filename
    result["ai_builder_prompt"] = AI_PROMPTS["image"]
    _save_scan(db, result, "image", file.filename)
    return AnalysisResult(**result)


@router.post("/audio", response_model=AnalysisResult)
async def analyze_audio_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    result = analyze_audio(content, file.filename or "upload.wav")
    result["scan_type"] = "audio"
    result["filename"] = file.filename
    result["ai_builder_prompt"] = AI_PROMPTS["audio"]
    _save_scan(db, result, "audio", file.filename)
    return AnalysisResult(**result)


@router.post("/video", response_model=AnalysisResult)
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 200MB)")

    result = analyze_video(content, file.filename or "upload.mp4")
    result["scan_type"] = "video"
    result["filename"] = file.filename
    result["ai_builder_prompt"] = AI_PROMPTS["video"]
    _save_scan(db, result, "video", file.filename)
    return AnalysisResult(**result)


@router.post("/text", response_model=AnalysisResult)
async def analyze_text_endpoint(
    text: str = Form(...),
    mode: str = Form("sms"),   # sms | email
    db: Session = Depends(get_db),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if mode not in ("sms", "email"):
        mode = "sms"

    result = analyze_text(text, mode)
    result["scan_type"] = mode
    result["filename"] = None
    result["ai_builder_prompt"] = AI_PROMPTS[mode]
    _save_scan(db, result, mode, None)
    return AnalysisResult(**result)
