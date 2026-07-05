"""
Video Deepfake Analyzer
Samples frames from video and runs image analysis on each.
"""
import io
import tempfile
import os
from typing import List
from schemas import EvidenceItem

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from analyzers.image_analyzer import analyze_image


def analyze_video(video_bytes: bytes, filename: str) -> dict:
    if not CV2_AVAILABLE:
        return _fallback(video_bytes, filename)

    suffix = os.path.splitext(filename)[1] or ".mp4"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name
    except Exception:
        return _fallback(video_bytes, filename)

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return _fallback(video_bytes, filename)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        if fps <= 0:
            fps = 25
        duration = total_frames / fps

        # Sample up to 8 frames evenly spaced
        sample_count = min(8, max(1, total_frames // 30))
        frame_indices = [int(i * total_frames / sample_count) for i in range(sample_count)]

        frame_scores = []
        frame_evidence = []

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            _, img_bytes = cv2.imencode(".jpg", frame)
            try:
                result = analyze_image(img_bytes.tobytes(), f"frame_{idx}.jpg")
                frame_scores.append(result["risk_score"])
                frame_evidence.append((idx, result["risk_score"], result["verdict"]))
            except Exception:
                continue

        cap.release()
    except Exception:
        return _fallback(video_bytes, filename)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if not frame_scores:
        return _fallback(video_bytes, filename)

    avg_score = sum(frame_scores) / len(frame_scores)
    max_score = max(frame_scores)
    high_risk_frames = sum(1 for s in frame_scores if s >= 70)

    evidence: List[EvidenceItem] = [
        EvidenceItem(
            label="Frame Analysis Summary",
            value=f"Analyzed {len(frame_scores)} frames from {duration:.1f}s video",
            risk_contribution=avg_score / 100,
            severity="low",
        ),
        EvidenceItem(
            label="Average Frame Risk Score",
            value=f"{avg_score:.1f}/100",
            risk_contribution=avg_score / 100,
            severity="high" if avg_score > 65 else "medium" if avg_score > 35 else "low",
        ),
        EvidenceItem(
            label="Peak Frame Risk",
            value=f"{max_score:.1f}/100 (worst frame)",
            risk_contribution=max_score / 100,
            severity="high" if max_score > 70 else "medium" if max_score > 40 else "low",
        ),
        EvidenceItem(
            label="High-Risk Frame Count",
            value=f"{high_risk_frames}/{len(frame_scores)} frames flagged as high risk",
            risk_contribution=high_risk_frames / max(len(frame_scores), 1),
            severity="high" if high_risk_frames > 2 else "medium" if high_risk_frames > 0 else "low",
        ),
    ]

    # Combined score: weighted avg + peak penalty
    risk_score = round(min(avg_score * 0.7 + max_score * 0.3, 100), 1)

    if risk_score >= 65:
        verdict = "HIGH_RISK"
        summary = f"Deepfake indicators detected across multiple frames. {high_risk_frames} frame(s) flagged as high risk."
    elif risk_score >= 35:
        verdict = "SUSPICIOUS"
        summary = "Some frames show manipulation indicators. Treat this video with caution."
    else:
        verdict = "SAFE"
        summary = "Video frames appear consistent with authentic content."

    return {
        "risk_score": risk_score,
        "verdict": verdict,
        "summary": summary,
        "evidence": evidence,
        "recommendations": _get_recommendations(verdict),
    }


def _fallback(video_bytes: bytes, filename: str) -> dict:
    size_mb = len(video_bytes) / (1024 * 1024)
    evidence = [
        EvidenceItem(
            label="File Size",
            value=f"{size_mb:.1f} MB",
            risk_contribution=0.2,
            severity="low",
        ),
        EvidenceItem(
            label="OpenCV Unavailable",
            value="Install opencv-python for full frame analysis",
            risk_contribution=0.0,
            severity="low",
        ),
    ]
    return {
        "risk_score": 45.0,
        "verdict": "SUSPICIOUS",
        "summary": "Limited video analysis available. Install opencv-python for full deepfake detection.",
        "evidence": evidence,
        "recommendations": [
            "Install opencv-python for full video analysis: pip install opencv-python",
            "Manually review video for: unnatural blinking, face boundary artifacts, audio-video sync issues.",
        ],
    }


def _get_recommendations(verdict: str) -> List[str]:
    if verdict == "SAFE":
        return [
            "Video appears authentic. Standard caution applies.",
            "Watch for subtle artifacts around face boundaries.",
        ]
    elif verdict == "SUSPICIOUS":
        return [
            "Do not share this video without verification.",
            "Look for unnatural blinking, boundary artifacts, or audio desync.",
            "Use Deepware Scanner for additional verification.",
        ]
    else:
        return [
            "HIGH RISK — likely deepfake video detected.",
            "Do not spread or act on content in this video.",
            "Report to the platform if shared online.",
            "Contact Deepware Scanner or Sensity AI for professional analysis.",
            "Preserve original file as evidence before reporting.",
        ]
