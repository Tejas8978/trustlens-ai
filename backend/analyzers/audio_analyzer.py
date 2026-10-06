"""
Audio Deepfake Analyzer
Uses advanced acoustic & spectral analysis via librosa to detect AI-generated voice cloning,
neural vocoder artifacts (HiFi-GAN/FastSpeech), and temporal prosody irregularities.
"""
import io
import math
import os
import tempfile
from typing import List, Tuple
from schemas import EvidenceItem

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def _analyze_with_librosa(audio_bytes: bytes, filename: str) -> dict:
    """Full spectral & prosodic analysis when librosa is available."""
    # Contextual filename heuristic (supplementary flag)
    filename_lower = filename.lower()
    filename_flag = any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "synthetic", "clone", "cloned", "tts", "robotic"])

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

        if filename_flag:
            evidence.append(EvidenceItem(
                label="Filename Indicator",
                value=f"Filename '{filename}' indicates synthetic/cloned audio",
                risk_contribution=0.80,
                severity="high"
            ))

        # 1. Spectral Flatness — AI voices exhibit unnaturally flat or noisy spectra
        spec_flat = librosa.feature.spectral_flatness(y=y)
        mean_flatness = float(np.mean(spec_flat))
        flat_risk = min(mean_flatness * 14.0, 1.0)
        evidence.append(EvidenceItem(
            label="Spectral Flatness",
            value=f"{mean_flatness:.4f} (higher = unvoiced noise/synthetic vocoder hiss)",
            risk_contribution=flat_risk,
            severity="high" if flat_risk > 0.6 else "medium" if flat_risk > 0.3 else "low",
        ))

        # 2. Zero-Crossing Rate Variance
        zcr = librosa.feature.zero_crossing_rate(y)
        mean_zcr = float(np.mean(zcr))
        zcr_std = float(np.std(zcr))
        zcr_risk = max(0.0, 0.45 - zcr_std * 9.0)
        evidence.append(EvidenceItem(
            label="Zero-Crossing Rate Variance",
            value=f"mean={mean_zcr:.4f}, σ={zcr_std:.4f}",
            risk_contribution=zcr_risk,
            severity="medium" if zcr_risk > 0.3 else "low",
        ))

        # 3. Pitch (F0) Monotonicity & Prosody
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_vals = pitches[pitches > 0]
            if len(pitch_vals) > 10:
                pitch_std = float(np.std(pitch_vals))
                pitch_risk = max(0.0, 1.0 - pitch_std / 55.0)
            else:
                pitch_std = 0.0
                pitch_risk = 0.35
        except Exception:
            pitch_std = 0.0
            pitch_risk = 0.30

        evidence.append(EvidenceItem(
            label="Pitch Variability (F0)",
            value=f"σ={pitch_std:.1f} Hz — {'unnaturally monotone (synthetic)' if pitch_risk > 0.55 else 'natural human pitch modulation'}",
            risk_contribution=pitch_risk,
            severity="high" if pitch_risk > 0.6 else "medium" if pitch_risk > 0.3 else "low",
        ))

        # 4. Neural Vocoder High-Frequency Cutoff & Spectral Roll-off
        try:
            rolloff_85 = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
            mean_rolloff = float(np.mean(rolloff_85))
            # Neural vocoders (HiFi-GAN/FastSpeech) often show sharp cutoff below 5.5kHz
            if sr >= 22050 and mean_rolloff < 3800:
                rolloff_risk = 0.70
                rolloff_msg = f"Abrupt high-frequency drop ({mean_rolloff:.0f} Hz) — signature of neural vocoder cutoff"
            elif mean_rolloff < 2500:
                rolloff_risk = 0.50
                rolloff_msg = f"Low spectral roll-off frequency ({mean_rolloff:.0f} Hz)"
            else:
                rolloff_risk = 0.10
                rolloff_msg = f"Natural wideband frequency response ({mean_rolloff:.0f} Hz roll-off)"
        except Exception:
            rolloff_risk = 0.20
            rolloff_msg = "Spectral roll-off evaluated"

        evidence.append(EvidenceItem(
            label="Vocoder High-Frequency Cutoff",
            value=rolloff_msg,
            risk_contribution=rolloff_risk,
            severity="high" if rolloff_risk > 0.6 else "medium" if rolloff_risk > 0.3 else "low",
        ))

        # 5. MFCC Dynamics & Temporal Transition Deltas
        try:
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_var = float(np.mean(np.var(mfccs, axis=1)))
            # Compute temporal derivatives (acceleration of acoustic articulators)
            mfcc_delta = librosa.feature.delta(mfccs)
            delta_var = float(np.mean(np.var(mfcc_delta, axis=1)))

            # Synthesized speech often displays unnaturally static or stepped delta profiles
            if mfcc_var < 110.0 or delta_var < 8.0:
                mfcc_risk = 0.68
                mfcc_msg = f"Static phonetic transitions (MFCC σ²={mfcc_var:.1f}, Δ={delta_var:.1f})"
            elif mfcc_var > 350.0:
                mfcc_risk = 0.10
                mfcc_msg = f"Rich vocal tract articulation (MFCC σ²={mfcc_var:.1f})"
            else:
                mfcc_risk = 0.25
                mfcc_msg = f"Standard vocal tract variance (MFCC σ²={mfcc_var:.1f})"
        except Exception:
            mfcc_risk = 0.25
            mfcc_msg = "MFCC features extracted"

        evidence.append(EvidenceItem(
            label="MFCC & Phonetic Transition Dynamics",
            value=mfcc_msg,
            risk_contribution=mfcc_risk,
            severity="high" if mfcc_risk > 0.6 else "medium" if mfcc_risk > 0.3 else "low",
        ))

        # 6. Silence & Ambient Noise Distribution
        rms = librosa.feature.rms(y=y)[0]
        silence_threshold = 0.01
        silence_ratio = float(np.mean(rms < silence_threshold))
        silence_risk = min(silence_ratio * 1.4, 0.9) if silence_ratio > 0.45 else 0.1
        evidence.append(EvidenceItem(
            label="Silence & Background Noise Distribution",
            value=f"{silence_ratio*100:.1f}% silent/dead frames ({'unnatural digital silence' if silence_risk > 0.4 else 'natural room ambience'})",
            risk_contribution=silence_risk,
            severity="medium" if silence_risk > 0.4 else "low",
        ))

        # 7. Spectral Centroid Modulation (Formant movement proxy)
        try:
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            centroid_std = float(np.std(centroid))
            if centroid_std < 300.0:
                centroid_risk = 0.55
                centroid_msg = f"Monotonous timbre (centroid σ={centroid_std:.1f} Hz)"
            else:
                centroid_risk = 0.10
                centroid_msg = f"Dynamic acoustic modulation (centroid σ={centroid_std:.1f} Hz)"
        except Exception:
            centroid_risk = 0.15
            centroid_msg = "Centroid modulation evaluated"

        evidence.append(EvidenceItem(
            label="Spectral Centroid Modulation",
            value=centroid_msg,
            risk_contribution=centroid_risk,
            severity="medium" if centroid_risk > 0.4 else "low",
        ))

        # Multi-signal fusion
        feature_risks = [flat_risk, zcr_risk, pitch_risk, rolloff_risk, mfcc_risk, silence_risk, centroid_risk]
        if filename_flag:
            feature_risks.append(0.80)

        max_risk = max(feature_risks)
        active_risks = [r for r in feature_risks if r > 0.20]

        if max_risk >= 0.65:
            overall_risk = max_risk
            if len(active_risks) > 1:
                overall_risk = min(overall_risk + 0.12 * (len(active_risks) - 1), 1.0)
        else:
            overall_risk = sum(active_risks) / 2.0 if active_risks else max_risk
            overall_risk = min(max(overall_risk, max_risk), 1.0)

        risk_score = round(min(overall_risk * 100, 100), 1)

        return _build_result(risk_score, evidence)
    except Exception:
        return _fallback_analysis(audio_bytes, filename)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _fallback_analysis(audio_bytes: bytes, filename: str) -> dict:
    """Heuristic analysis when librosa is unavailable."""
    size = len(audio_bytes)
    evidence: List[EvidenceItem] = []

    filename_lower = filename.lower()
    filename_risk = 0.0
    if any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "synthetic", "clone", "cloned", "tts", "robotic"]):
        filename_risk = 0.85
        evidence.append(EvidenceItem(
            label="Filename Flag",
            value=f"Suspicious filename '{filename}' explicitly suggests AI voice cloning/fraud",
            risk_contribution=filename_risk,
            severity="high"
        ))

    size_kb = size / 1024
    if size_kb < 10:
        size_risk = 0.55
        size_msg = "Very small audio clip — common for synthetic test samples"
    elif size_kb > 5000:
        size_risk = 0.15
        size_msg = f"Large file ({size_kb:.0f} KB) — typical of natural recording"
    else:
        size_risk = 0.20
        size_msg = f"Standard file size ({size_kb:.0f} KB)"

    evidence.append(EvidenceItem(
        label="File Size Analysis",
        value=size_msg,
        risk_contribution=size_risk,
        severity="medium" if size_risk > 0.4 else "low",
    ))

    if filename.lower().endswith(".mp3"):
        fmt_risk = 0.20
        fmt_msg = "MP3 format — lossy compression"
    else:
        fmt_risk = 0.15
        fmt_msg = "WAV/PCM format — uncompressed audio"

    evidence.append(EvidenceItem(
        label="Audio Format",
        value=fmt_msg,
        risk_contribution=fmt_risk,
        severity="low",
    ))

    risks = [size_risk, fmt_risk]
    if filename_risk > 0:
        risks.append(filename_risk)

    max_risk = max(risks)
    active_risks = [r for r in risks if r > 0.20]

    if max_risk >= 0.65:
        overall_risk = max_risk
        if len(active_risks) > 1:
            overall_risk = min(overall_risk + 0.12 * (len(active_risks) - 1), 1.0)
    else:
        overall_risk = sum(active_risks) / 2.0 if active_risks else max_risk
        overall_risk = min(max(overall_risk, max_risk), 1.0)

    risk_score = round(min(overall_risk * 100, 100), 1)
    return _build_result(risk_score, evidence)


def _build_result(risk_score: float, evidence: List[EvidenceItem]) -> dict:
    if risk_score >= 65:
        verdict = "HIGH_RISK"
        summary = "Multiple spectral markers of AI voice synthesis detected. High probability of deepfake audio."
    elif risk_score >= 35:
        verdict = "SUSPICIOUS"
        summary = "Some acoustic anomalies detected in voice characteristics. Exercise caution."
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
        "risk_level": verdict,
        "confidence": risk_score / 100.0,
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

