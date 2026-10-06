"""
Analysis router — handles all /api/analyze/* endpoints
"""
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from schemas import AnalysisResult, EvidenceItem
from analyzers.image_analyzer import analyze_image
from analyzers.audio_analyzer import analyze_audio
from analyzers.video_analyzer import analyze_video
from analyzers.text_analyzer import analyze_text
import database

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
    "url": (
        "You are a cybersecurity phishing & malicious link analyst AI. Inspect the provided URL "
        "for brand impersonation, typosquatting, raw IP usage, high-abuse TLDs, credential harvesting paths, "
        "and obfuscation tricks. Return: risk_score (0-100), verdict, evidence, and recommendations."
    ),
}


def _save_scan(result: dict, scan_type: str, filename: Optional[str]):
    """Persist the scan result to MongoDB."""
    payload = dict(result)
    payload["scan_type"] = scan_type
    payload["filename"] = filename
    # Serialize evidence list for storage
    payload["details"] = json.dumps([
        (e.model_dump() if hasattr(e, "model_dump") else (e.dict() if hasattr(e, "dict") else e))
        for e in result.get("evidence", [])
    ])
    database.add_history(payload)


@router.post("/image", response_model=AnalysisResult)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
):
    import gc
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 15MB)")

    try:
        result = analyze_image(content, file.filename or "upload.jpg")
        result["scan_type"] = "image"
        result["filename"] = file.filename
        result["ai_builder_prompt"] = AI_PROMPTS["image"]
        _save_scan(result, "image", file.filename)
        return AnalysisResult(**result)
    finally:
        del content
        gc.collect()


@router.post("/audio", response_model=AnalysisResult)
async def analyze_audio_endpoint(
    file: UploadFile = File(...),
):
    import gc
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 25MB)")

    try:
        result = analyze_audio(content, file.filename or "upload.wav")
        result["scan_type"] = "audio"
        result["filename"] = file.filename
        result["ai_builder_prompt"] = AI_PROMPTS["audio"]
        _save_scan(result, "audio", file.filename)
        return AnalysisResult(**result)
    finally:
        del content
        gc.collect()


@router.post("/video", response_model=AnalysisResult)
async def analyze_video_endpoint(
    file: UploadFile = File(...),
):
    import gc
    import os
    import tempfile

    suffix = os.path.splitext(file.filename or "")[1] or ".mp4"
    total_size = 0
    max_size = 100 * 1024 * 1024  # 100MB max limit to stay well within container capacity

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            while chunk := await file.read(1024 * 1024):  # 1MB stream chunks to save RAM
                total_size += len(chunk)
                if total_size > max_size:
                    raise HTTPException(status_code=413, detail="File too large (max 100MB)")
                tmp.write(chunk)

        result = analyze_video(tmp_path, file.filename or "upload.mp4")
        result["scan_type"] = "video"
        result["filename"] = file.filename
        result["ai_builder_prompt"] = AI_PROMPTS["video"]
        _save_scan(result, "video", file.filename)
        return AnalysisResult(**result)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        gc.collect()


@router.post("/text", response_model=AnalysisResult)
async def analyze_text_endpoint(
    text: str = Form(...),
    mode: str = Form("sms"),   # sms | email | url
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    if mode not in ("sms", "email", "url"):
        mode = "sms"

    result = analyze_text(text, mode)
    result["scan_type"] = mode
    result["filename"] = None
    result["ai_builder_prompt"] = AI_PROMPTS[mode]
    _save_scan(result, mode, None)
    return AnalysisResult(**result)
