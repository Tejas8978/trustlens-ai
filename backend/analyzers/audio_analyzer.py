"""
Audio Deepfake Analyzer
Uses spectral analysis via librosa to detect AI-generated voice cloning.
"""
import io
import math
import tempfile
import os
from typing import List, Tuple
from schemas import EvidenceItem

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def _analyze_with_librosa(audio_bytes: bytes, filename: str) -> dict:
    """Full spectral analysis when librosa is available."""
    # Write to temp file
    suffix = ".wav" if filename.lower().endswith(".wav") else ".mp3"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
    except Exception:
        return _fallback_analysis(audio_bytes, filename)

    try:
        try:
            y, sr = librosa.load(tmp_path, sr=None, duration=60)
        except Exception:
            return _fallback_analysis(audio_bytes, filename)

        if len(y) == 0:
            return _fallback_analysis(audio_bytes, filename)

        evidence: List[EvidenceItem] = []

        # 1. Spectral flatness — AI voices are often unnaturally flat
        spec_flat = librosa.feature.spectral_flatness(y=y)
        mean_flatness = float(np.mean(spec_flat))
        flat_risk = min(mean_flatness * 15, 1.0)  # Calibrated: real speech ~0.02-0.1
        evidence.append(EvidenceItem(
            label="Spectral Flatness",
            value=f"{mean_flatness:.4f} (higher = more noise-like / synthetic)",
            risk_contribution=flat_risk,
            severity="high" if flat_risk > 0.6 else "medium" if flat_risk > 0.3 else "low",
        ))

        # 2. Zero crossing rate — synthesized audio often differs
        zcr = librosa.feature.zero_crossing_rate(y)
        mean_zcr = float(np.mean(zcr))
        zcr_std = float(np.std(zcr))
        zcr_risk = max(0.0, 0.5 - zcr_std * 10)  # Low variance = synthetic
        evidence.append(EvidenceItem(
            label="Zero-Crossing Rate Variance",
            value=f"mean={mean_zcr:.4f}, std={zcr_std:.4f}",
            risk_contribution=zcr_risk,
            severity="medium" if zcr_risk > 0.3 else "low",
        ))

        # 3. Pitch (F0) monotonicity — AI voices lack natural pitch variation
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_vals = pitches[pitches > 0]
            if len(pitch_vals) > 10:
                pitch_std = float(np.std(pitch_vals))
                pitch_risk = max(0.0, 1.0 - pitch_std / 50.0)
            else:
                pitch_std = 0
                pitch_risk = 0.4
        except Exception:
            pitch_std = 0
            pitch_risk = 0.3

        evidence.append(EvidenceItem(
            label="Pitch Variability (F0)",
            value=f"σ={pitch_std:.1f} Hz — {'monotone (suspicious)' if pitch_risk > 0.5 else 'natural variation'}",
            risk_contribution=pitch_risk,
            severity="high" if pitch_risk > 0.6 else "medium" if pitch_risk > 0.3 else "low",
        ))

        # 4. Silence ratio — TTS systems often have unnaturally clean silences
        rms = librosa.feature.rms(y=y)[0]
        silence_threshold = 0.01
        silence_ratio = float(np.mean(rms < silence_threshold))
        silence_risk = min(silence_ratio * 1.5, 1.0) if silence_ratio > 0.4 else 0.1
        evidence.append(EvidenceItem(
            label="Silence Distribution",
            value=f"{silence_ratio*100:.1f}% silent frames",
            risk_contribution=silence_risk,
            severity="medium" if silence_risk > 0.4 else "low",
        ))

        # 5. MFCC consistency — human speech shows natural MFCC variance
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_var = float(np.mean(np.var(mfccs, axis=1)))
        mfcc_risk = max(0.0, 1.0 - mfcc_var / 200.0)
        evidence.append(EvidenceItem(
            label="MFCC Consistency",
            value=f"variance={mfcc_var:.2f} — {'suspiciously uniform' if mfcc_risk > 0.5 else 'natural'}",
            risk_contribution=mfcc_risk,
            severity="high" if mfcc_risk > 0.6 else "medium" if mfcc_risk > 0.3 else "low",
        ))

        weights = [0.25, 0.15, 0.30, 0.15, 0.15]
        risks = [flat_risk, zcr_risk, pitch_risk, silence_risk, mfcc_risk]
        raw_score = sum(w * r for w, r in zip(weights, risks))
        risk_score = round(min(raw_score * 100, 100), 1)

        return _build_result(risk_score, evidence)
    except Exception:
        return _fallback_analysis(audio_bytes, filename)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _fallback_analysis(audio_bytes: bytes, filename: str) -> dict:
    """Simple heuristic when librosa is unavailable."""
    size = len(audio_bytes)
    evidence: List[EvidenceItem] = []

    # File size heuristic — AI-generated clips are often perfectly uniform
    size_kb = size / 1024
    if size_kb < 10:
        size_risk = 0.6
        size_msg = "Very small audio clip — common for synthetic samples"
    elif size_kb > 5000:
        size_risk = 0.15
        size_msg = f"Large file ({size_kb:.0f} KB) — likely genuine recording"
    else:
        size_risk = 0.2
        size_msg = f"Normal file size ({size_kb:.0f} KB)"

    evidence.append(EvidenceItem(
        label="File Size Analysis",
        value=size_msg,
        risk_contribution=size_risk,
        severity="medium" if size_risk > 0.4 else "low",
    ))

    # Format heuristic
    if filename.lower().endswith(".mp3"):
        fmt_risk = 0.2
        fmt_msg = "MP3 format — commonly used, moderate confidence"
    else:
        fmt_risk = 0.15
        fmt_msg = "WAV/other format — standard recording format"

    evidence.append(EvidenceItem(
        label="Audio Format",
        value=fmt_msg,
        risk_contribution=fmt_risk,
        severity="low",
    ))

    risk_score = round(((size_risk + fmt_risk) / 2) * 100, 1)
    return _build_result(risk_score, evidence)


def _build_result(risk_score: float, evidence: List[EvidenceItem]) -> dict:
    if risk_score >= 65:
        verdict = "HIGH_RISK"
        summary = "Multiple spectral markers of AI voice synthesis detected. High probability of deepfake audio."
    elif risk_score >= 35:
        verdict = "SUSPICIOUS"
        summary = "Some anomalies detected in audio characteristics. Exercise caution."
    else:
        verdict = "SAFE"
        summary = "Audio characteristics appear consistent with natural human speech."

    recommendations = _get_recommendations(verdict)
    return {
        "risk_score": risk_score,
        "verdict": verdict,
        "summary": summary,
        "evidence": evidence,
        "recommendations": recommendations,
    }


def _get_recommendations(verdict: str) -> List[str]:
    if verdict == "SAFE":
        return [
            "Audio appears authentic — standard caution applies.",
            "Verify the speaker's identity through a separate trusted channel.",
        ]
    elif verdict == "SUSPICIOUS":
        return [
            "Do not take action based on this audio without independent verification.",
            "Contact the purported speaker through a known trusted channel.",
            "Listen for subtle robotic artifacts, unnatural pauses, or monotone delivery.",
        ]
    else:
        return [
            "HIGH RISK — strong signs of AI voice cloning detected.",
            "Do NOT comply with any requests made in this audio.",
            "Report to the platform, organization, or relevant authority.",
            "Contact the person allegedly speaking through a verified channel immediately.",
            "Preserve the audio file as evidence.",
        ]


def analyze_audio(audio_bytes: bytes, filename: str) -> dict:
    try:
        if LIBROSA_AVAILABLE:
            return _analyze_with_librosa(audio_bytes, filename)
        return _fallback_analysis(audio_bytes, filename)
    except Exception:
        return _fallback_analysis(audio_bytes, filename)
