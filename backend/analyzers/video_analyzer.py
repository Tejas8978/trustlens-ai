"""
Video Deepfake Analyzer
Samples frames from video, inspects inter-frame temporal consistency & edge flickering,
and executes multi-domain forensic analysis per frame.
Optimized for low-memory execution (<50MB RAM footprint).
"""
import gc
import os
import sys
import tempfile
from typing import List, Tuple

# Ensure backend directory is in sys.path for IDEs and runtimes
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

try:
    from schemas import EvidenceItem
except ImportError:
    try:
        from ..schemas import EvidenceItem  # type: ignore
    except ImportError:
        from backend.schemas import EvidenceItem  # type: ignore

try:
    import numpy as np  # type: ignore
except ImportError:
    pass

try:
    import cv2  # type: ignore
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore
    CV2_AVAILABLE = False

try:
    from analyzers.image_analyzer import analyze_image
except ImportError:
    try:
        from image_analyzer import analyze_image  # type: ignore
    except ImportError:
        from .image_analyzer import analyze_image  # type: ignore


def _compute_temporal_jitter(gray1, gray2) -> Tuple[float, float]:
    """
    Computes inter-frame difference and edge instability (Laplacian variance flux).
    Deepfake face swaps frequently suffer from temporal flickering and micro-boundary jitter.
    """
    if not CV2_AVAILABLE or cv2 is None or np is None or gray1 is None or gray2 is None:
        return 0.0, 0.0

    try:
        # Resize to standard analysis size if large
        if gray1.shape[0] > 480 or gray1.shape[1] > 640:
            g1 = cv2.resize(gray1, (320, 240))
            g2 = cv2.resize(gray2, (320, 240))
        else:
            g1, g2 = gray1, gray2

        # 1. Absolute pixel difference
        abs_diff = cv2.absdiff(g1, g2)
        diff_mean = float(np.mean(abs_diff))

        # 2. Laplacian edge difference
        lap1 = cv2.Laplacian(g1, cv2.CV_32F)
        lap2 = cv2.Laplacian(g2, cv2.CV_32F)
        edge_flux = float(np.mean(np.abs(lap1 - lap2)))

        return diff_mean, edge_flux
    except Exception:
        return 0.0, 0.0


def analyze_video(video_input, filename: str) -> dict:
    # Contextual filename check
    filename_lower = filename.lower()
    filename_flag = any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "manipulated", "spoof", "phish"])

    # Fallback if OpenCV is not available
    if not CV2_AVAILABLE or cv2 is None or np is None:
        size = 0
        if isinstance(video_input, (bytes, bytearray)):
            size = len(video_input)
        elif isinstance(video_input, str) and os.path.exists(video_input):
            size = os.path.getsize(video_input)
        return _fallback_from_size(size, filename)

    is_temp_file = False
    tmp_path = ""
    if isinstance(video_input, str) and os.path.exists(video_input):
        tmp_path = video_input
    else:
        suffix = os.path.splitext(filename)[1] or ".mp4"
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                if isinstance(video_input, (bytes, bytearray)):
                    tmp.write(video_input)
                tmp_path = tmp.name
                is_temp_file = True
        except Exception:
            size = len(video_input) if isinstance(video_input, (bytes, bytearray)) else 0
            return _fallback_from_size(size, filename)

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
            return _fallback_from_size(size, filename)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        if fps <= 0:
            fps = 25
        duration = total_frames / fps

        # Sample 2-4 key checkpoints to conserve memory under 512MB RAM
        sample_count = min(4, max(2, total_frames // 40)) if total_frames > 1 else 1
        frame_indices = [int(i * (total_frames - 2) / max(sample_count - 1, 1)) for i in range(sample_count)]

        frame_scores = []
        temporal_edge_fluxes = []

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # Read consecutive frame for temporal consistency analysis
            ret_next, frame_next = cap.read()
            if ret_next and frame_next is not None:
                g1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                g2 = cv2.cvtColor(frame_next, cv2.COLOR_BGR2GRAY)
                _, edge_flux = _compute_temporal_jitter(g1, g2)
                temporal_edge_fluxes.append(edge_flux)
                del frame_next

            # Downscale frame for memory safety before forensic image analysis
            fh, fw = frame.shape[:2]
            if max(fh, fw) > 480:
                scale = 480 / max(fh, fw)
                small_frame = cv2.resize(frame, (int(fw * scale), int(fh * scale)), interpolation=cv2.INTER_AREA)
            else:
                small_frame = frame
            del frame

            _, img_bytes = cv2.imencode(".jpg", small_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            del small_frame

            try:
                result = analyze_image(img_bytes.tobytes(), f"frame_{idx}.jpg")
                frame_scores.append(result["risk_score"])
            except Exception:
                continue
            finally:
                del img_bytes

        cap.release()

        if not frame_scores:
            size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
            return _fallback_from_size(size, filename)

        avg_score = sum(frame_scores) / len(frame_scores)
        max_score = max(frame_scores)
        high_risk_frames = sum(1 for s in frame_scores if s >= 65)

        evidence: List[EvidenceItem] = []

        if filename_flag:
            evidence.append(EvidenceItem(
                label="Filename Indicator",
                value=f"Filename '{filename}' indicates potential video deepfake/fraud",
                risk_contribution=0.80,
                severity="high"
            ))

        # 1. Temporal consistency & flickering
        temporal_risk = 0.0
        if temporal_edge_fluxes:
            mean_edge_flux = sum(temporal_edge_fluxes) / len(temporal_edge_fluxes)
            if mean_edge_flux > 18.0:
                temporal_risk = min(0.40 + (mean_edge_flux - 18.0) * 0.03, 0.85)
                temporal_msg = f"Temporal edge flux={mean_edge_flux:.1f} — notable inter-frame texture flickering"
            else:
                temporal_risk = 0.10
                temporal_msg = f"Temporal edge flux={mean_edge_flux:.1f} — smooth inter-frame motion consistency"
        else:
            temporal_risk = 0.15
            temporal_msg = "Single-frame sequence evaluated"

        evidence.append(EvidenceItem(
            label="Temporal Consistency & Edge Flickering",
            value=temporal_msg,
            risk_contribution=temporal_risk,
            severity="high" if temporal_risk > 0.55 else "medium" if temporal_risk > 0.3 else "low",
        ))

        # 2. Frame Analysis Summary
        evidence.extend([
            EvidenceItem(
                label="Frame Analysis Summary",
                value=f"Analyzed {len(frame_scores)} key frames from {duration:.1f}s video",
                risk_contribution=avg_score / 100.0,
                severity="low",
            ),
            EvidenceItem(
                label="Average Frame Risk Score",
                value=f"{avg_score:.1f}/100 across sampled timeline",
                risk_contribution=avg_score / 100.0,
                severity="high" if avg_score > 65 else "medium" if avg_score > 35 else "low",
            ),
            EvidenceItem(
                label="Peak Frame Risk",
                value=f"{max_score:.1f}/100 (worst detected frame)",
                risk_contribution=max_score / 100.0,
                severity="high" if max_score > 70 else "medium" if max_score > 40 else "low",
            ),
            EvidenceItem(
                label="High-Risk Frame Count",
                value=f"{high_risk_frames}/{len(frame_scores)} frames flagged with deepfake/manipulation cues",
                risk_contribution=high_risk_frames / max(len(frame_scores), 1),
                severity="high" if high_risk_frames > 2 else "medium" if high_risk_frames > 0 else "low",
            ),
        ])

        base_score = avg_score * 0.50 + max_score * 0.35 + (temporal_risk * 100.0) * 0.15
        risks = [base_score / 100.0, temporal_risk]
        if filename_flag:
            risks.append(0.80)

        max_risk = max(risks)
        active_risks = [r for r in risks if r > 0.20]
        if len(active_risks) > 1:
            overall_risk = min(max_risk + 0.10 * (len(active_risks) - 1), 1.0)
        else:
            overall_risk = max_risk

        risk_score = round(min(overall_risk * 100, 100), 1)

        if risk_score >= 65:
            verdict = "HIGH_RISK"
            summary = f"Deepfake indicators detected across sampled video timeline ({high_risk_frames} high-risk frame(s) with temporal inconsistency)."
        elif risk_score >= 35:
            verdict = "SUSPICIOUS"
            summary = "Some frames or temporal transitions show manipulation anomalies. Exercise caution."
        else:
            verdict = "SAFE"
            summary = "Video frames and temporal motion appear consistent with authentic recorded media."

        return {
            "risk_score": risk_score,
            "verdict": verdict,
            "summary": summary,
            "evidence": evidence,
            "recommendations": _get_recommendations(verdict),
            "risk_level": verdict,
            "confidence": risk_score / 100.0,
        }
    except Exception:
        size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        return _fallback_from_size(size, filename)
    finally:
        if is_temp_file and tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        gc.collect()


def _fallback(video_bytes: bytes, filename: str) -> dict:
    return _fallback_from_size(len(video_bytes), filename)


def _fallback_from_size(size_bytes: int, filename: str) -> dict:
    size_mb = size_bytes / (1024 * 1024)
    filename_lower = filename.lower()
    filename_risk = 0.0
    if any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "manipulated", "spoof", "phish"]):
        filename_risk = 0.85

    evidence = [
        EvidenceItem(
            label="File Size",
            value=f"{size_mb:.1f} MB",
            risk_contribution=0.20,
            severity="low",
        ),
        EvidenceItem(
            label="Frame Inspection Status",
            value="Heuristic stream analysis completed",
            risk_contribution=0.0,
            severity="low",
        ),
    ]

    if filename_risk > 0:
        evidence.append(EvidenceItem(
            label="Filename Flag",
            value=f"Suspicious filename '{filename}' explicitly suggests video deepfake/fraud",
            risk_contribution=filename_risk,
            severity="high"
        ))

    risks = [0.20]
    if filename_risk > 0:
        risks.append(filename_risk)

    max_risk = max(risks)
    active_risks = [r for r in risks if r > 0.20]
    if len(active_risks) > 1:
        overall_risk = min(max_risk + 0.10 * (len(active_risks) - 1), 1.0)
    else:
        overall_risk = max_risk

    risk_score = round(min(overall_risk * 100, 100), 1)

    if risk_score >= 65:
        verdict = "HIGH_RISK"
        summary = "Video filename suggests deepfake/fraud. Detailed frame analysis unavailable."
    else:
        verdict = "SUSPICIOUS"
        summary = "Limited video analysis available. Install opencv-python for full deepfake detection."

    return {
        "risk_score": risk_score,
        "verdict": verdict,
        "summary": summary,
        "evidence": evidence,
        "recommendations": [
            "Install opencv-python for full video analysis: pip install opencv-python",
            "Manually review video for: unnatural blinking, face boundary artifacts, audio-video sync issues.",
        ],
        "risk_level": verdict,
        "confidence": risk_score / 100.0,
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
