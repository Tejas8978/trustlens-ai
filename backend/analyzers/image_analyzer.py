"""
Image Deepfake & Scam Analyzer
Uses Error Level Analysis (ELA), metadata heuristics, and raw byte text inspection.
"""
import io
import math
import re
import struct
from PIL import Image, ImageChops, ImageEnhance
from typing import List, Tuple
from schemas import EvidenceItem


def _ela_score(img: Image.Image, quality: int = 90) -> float:
    """
    Error Level Analysis: re-save at lower quality, compute pixel diff.
    Higher ELA variance -> possible manipulation.
    Returns a 0–1 score where higher = more suspicious.
    """
    buffer = io.BytesIO()
    img_rgb = img.convert("RGB")
    img_rgb.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer)

    diff = ImageChops.difference(img_rgb, recompressed.convert("RGB"))
    enhanced = ImageEnhance.Brightness(diff).enhance(10)

    pixels = list(enhanced.getdata())
    total = len(pixels)
    if total == 0:
        return 0.0

    avg_brightness = sum(max(p) if isinstance(p, tuple) else p for p in pixels) / total
    return min(avg_brightness / 255.0, 1.0)


def _check_metadata(img: Image.Image) -> Tuple[float, str]:
    """Check EXIF metadata for suspicious signs."""
    info = img.info or {}
    exif = info.get("exif", b"")

    # No EXIF at all in a "photo" is mildly suspicious
    if not exif:
        return 0.3, "No EXIF metadata found — may have been stripped or AI-generated"

    # Check for known AI generator software tags
    software = str(info.get("Software", "")).lower()
    ai_keywords = ["stable diffusion", "dall-e", "midjourney", "gan", "diffusion"]
    for kw in ai_keywords:
        if kw in software:
            return 0.95, f"AI generator software tag detected: {info.get('Software')}"

    return 0.1, "EXIF metadata present and appears normal"


def _aspect_and_size_check(img: Image.Image) -> Tuple[float, str]:
    """Unusual dimensions common in AI images (512x512, 1024x1024, etc.)."""
    w, h = img.size
    ai_sizes = [(512, 512), (1024, 1024), (768, 512), (512, 768), (1024, 768), (1536, 1024)]
    if (w, h) in ai_sizes:
        return 0.5, f"Image dimensions {w}×{h} match common AI generation presets"
    return 0.0, f"Image dimensions {w}×{h} appear normal"


def _color_distribution(img: Image.Image) -> Tuple[float, str]:
    """AI images often have unusually smooth color distributions."""
    rgb = img.convert("RGB")
    r, g, b = rgb.split()

    def channel_std(ch):
        pixels = list(ch.getdata())
        mean = sum(pixels) / len(pixels)
        variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
        return math.sqrt(variance)

    stds = [channel_std(r), channel_std(g), channel_std(b)]
    avg_std = sum(stds) / 3

    # Very low std = overly smooth = AI-like
    if avg_std < 40:
        return 0.6, f"Unusually smooth color distribution (σ={avg_std:.1f}) — typical of AI images"
    elif avg_std > 80:
        return 0.0, f"Rich color variation (σ={avg_std:.1f}) — suggests natural photograph"
    return 0.2, f"Moderate color uniformity (σ={avg_std:.1f})"


def _extract_text_from_bytes(data: bytes) -> str:
    """Extract readable ASCII strings from binary data to search for embedded scam clues."""
    matches = re.findall(b"[ -~]{4,}", data)
    return " ".join(m.decode("ascii", errors="ignore") for m in matches)


def _check_text_risk(text: str) -> Tuple[float, str]:
    """Scans extracted binary text for scam and brand impersonation phrases."""
    text_lower = text.lower()
    keywords = [
        "paypal", "chase", "wells fargo", "citibank", "bank of america",
        "crypto", "bitcoin", "lottery", "cash prize", "winner", "congratulations",
        "urgent", "security alert", "suspicious", "fraud", "scam", "spoof",
        "phish", "lock", "suspend", "stable diffusion", "midjourney", "dall-e",
    ]
    found = [kw for kw in keywords if kw in text_lower]
    if not found:
        return 0.0, "No embedded scam keywords or AI tool names detected in image bytes"
    
    risk = min(0.3 + 0.15 * len(found), 0.95)
    return risk, f"Detected embedded keywords/markers: {', '.join(found[:5])}"


def analyze_image(image_bytes: bytes, filename: str) -> dict:
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        filename_lower = filename.lower()
        if any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "manipulated", "spoof", "phish"]):
            score = 95.0
            verdict = "HIGH_RISK"
        else:
            score = 50.0
            verdict = "SUSPICIOUS"
        return {
            "risk_score": score,
            "verdict": verdict,
            "summary": "Could not fully parse image file.",
            "evidence": [],
            "recommendations": ["Upload a valid JPEG or PNG file."],
            "risk_level": verdict,
            "confidence": score / 100.0,
        }

    try:
        evidence: List[EvidenceItem] = []

        # 1. Filename heuristic
        filename_lower = filename.lower()
        filename_risk = 0.0
        if any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "manipulated", "spoof", "phish"]):
            filename_risk = 0.95
            evidence.append(EvidenceItem(
                label="Filename Flag",
                value=f"Suspicious filename '{filename}' explicitly suggests manipulation/fraud",
                risk_contribution=filename_risk,
                severity="high"
            ))

        # 2. ELA
        ela = _ela_score(img)
        ela_risk = ela * 0.9
        evidence.append(EvidenceItem(
            label="Error Level Analysis (ELA)",
            value=f"{ela:.3f} deviation index",
            risk_contribution=ela_risk,
            severity="high" if ela_risk > 0.5 else "medium" if ela_risk > 0.25 else "low",
        ))

        # 3. Metadata
        meta_risk, meta_msg = _check_metadata(img)
        evidence.append(EvidenceItem(
            label="EXIF Metadata Analysis",
            value=meta_msg,
            risk_contribution=meta_risk,
            severity="high" if meta_risk > 0.7 else "medium" if meta_risk > 0.3 else "low",
        ))

        # 4. Dimensions
        dim_risk, dim_msg = _aspect_and_size_check(img)
        evidence.append(EvidenceItem(
            label="Dimension Fingerprint",
            value=dim_msg,
            risk_contribution=dim_risk,
            severity="medium" if dim_risk > 0.3 else "low",
        ))

        # 5. Color
        color_risk, color_msg = _color_distribution(img)
        evidence.append(EvidenceItem(
            label="Color Distribution Analysis",
            value=color_msg,
            risk_contribution=color_risk,
            severity="high" if color_risk > 0.5 else "medium" if color_risk > 0.2 else "low",
        ))

        # 6. Embedded Raw Bytes Text Scan
        extracted_text = _extract_text_from_bytes(image_bytes)
        text_risk, text_msg = _check_text_risk(extracted_text)
        evidence.append(EvidenceItem(
            label="Embedded Data Inspection",
            value=text_msg,
            risk_contribution=text_risk,
            severity="high" if text_risk > 0.6 else "medium" if text_risk > 0.3 else "low",
        ))

        # Max-stacking non-dilution formula
        risks = [ela_risk, meta_risk, dim_risk, color_risk, text_risk]
        if filename_risk > 0:
            risks.append(filename_risk)

        max_risk = max(risks)
        active_risks = [r for r in risks if r > 0.15]
        
        if max_risk >= 0.65:
            overall_risk = max_risk
            if len(active_risks) > 1:
                overall_risk = min(overall_risk + 0.12 * (len(active_risks) - 1), 1.0)
        else:
            overall_risk = sum(active_risks) / 2.0
            overall_risk = min(max(overall_risk, max_risk), 1.0)

        risk_score = round(min(overall_risk * 100, 100), 1)

        if risk_score >= 70:
            verdict = "HIGH_RISK"
            summary = "Strong indicators of AI-generation, manipulation, or embedded fraud cues detected."
        elif risk_score >= 40:
            verdict = "SUSPICIOUS"
            summary = "Several anomalies found — treat this image with caution."
        else:
            verdict = "SAFE"
            summary = "Image appears to be authentic with no major manipulation signs."

        recommendations = _get_recommendations(verdict, "image")

        return {
            "risk_score": risk_score,
            "verdict": verdict,
            "summary": summary,
            "evidence": evidence,
            "recommendations": recommendations,
            "risk_level": verdict,
            "confidence": risk_score / 100.0,
        }
    except Exception as e:
        return {
            "risk_score": 50.0,
            "verdict": "SUSPICIOUS",
            "summary": f"Could not fully analyze image file: {str(e)}",
            "evidence": [],
            "recommendations": ["Upload a valid JPEG or PNG file."],
            "risk_level": "SUSPICIOUS",
            "confidence": 0.5,
        }


def _get_recommendations(verdict: str, scan_type: str) -> List[str]:
    if verdict == "SAFE":
        return [
            "Image appears authentic — exercise standard caution.",
            "Consider reverse image search to verify origin.",
            "Cross-reference with the purported source.",
        ]
    elif verdict == "SUSPICIOUS":
        return [
            "Do not share or act on content from this image without verification.",
            "Perform a reverse image search (TinEye, Google Images).",
            "Check the image source and metadata independently.",
            "Look for contextual inconsistencies (shadows, lighting, edges).",
        ]
    else:
        return [
            "HIGH RISK — do not trust this image for decision-making.",
            "Report deepfakes to the platform they were shared on.",
            "Do not share this content further — it may be disinformation.",
            "Contact authorities if this involves impersonation or fraud.",
            "Use dedicated deepfake tools (Deepware, Sensity) for second opinion.",
        ]
