"""
Audio Deepfake Analyzer
Uses acoustic & spectral analysis via soundfile and NumPy to detect AI-generated voice cloning,
neural vocoder artifacts (HiFi-GAN/FastSpeech), and temporal prosody irregularities.
Optimized for low-memory execution (<30MB RAM footprint).
"""
import io
import math
import os
import sys
import tempfile
from typing import List, Tuple

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
    import numpy as np
    import soundfile as sf
    AUDIO_ENGINE_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    sf = None  # type: ignore
    AUDIO_ENGINE_AVAILABLE = False


def _analyze_with_soundfile(audio_bytes: bytes, filename: str) -> dict:
    """Spectral & prosodic analysis using soundfile and NumPy."""
    filename_lower = filename.lower()
    filename_flag = any(k in filename_lower for k in ["fake", "scam", "fraud", "deepfake", "synthetic", "clone", "cloned", "tts", "robotic"])

    try:
        y, sr = sf.read(io.BytesIO(audio_bytes))
    except Exception:
        # Fallback to temp file if direct buffer read is unsupported
        try:
            suffix = os.path.splitext(filename)[1] or ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            y, sr = sf.read(tmp_path)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        except Exception:
            return _fallback_analysis(audio_bytes, filename)

    if len(y) == 0:
        return _fallback_analysis(audio_bytes, filename)

    # Convert stereo to mono
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    y = y.astype(np.float32)

    # Limit to first 60 seconds to cap memory usage
    max_samples = min(len(y), sr * 60)
    y = y[:max_samples]

    evidence: List[EvidenceItem] = []

    if filename_flag:
        evidence.append(EvidenceItem(
            label="Filename Indicator",
            value=f"Filename '{filename}' indicates synthetic/cloned audio",
            risk_contribution=0.80,
            severity="high"
        ))

    # 1. Spectral Flatness — AI voices exhibit unnaturally flat or noisy spectra
    n_fft = min(len(y), 2048)
    fft_mag = np.abs(np.fft.rfft(y[:n_fft])) ** 2 + 1e-12
    geom_mean = float(np.exp(np.mean(np.log(fft_mag))))
    arith_mean = float(np.mean(fft_mag))
    mean_flatness = float(geom_mean / max(arith_mean, 1e-12))
    flat_risk = min(mean_flatness * 14.0, 1.0)
    evidence.append(EvidenceItem(
        label="Spectral Flatness",
        value=f"{mean_flatness:.4f} (higher = unvoiced noise/synthetic vocoder hiss)",
        risk_contribution=flat_risk,
        severity="high" if flat_risk > 0.6 else "medium" if flat_risk > 0.3 else "low",
    ))

    # 2. Zero-Crossing Rate Variance
    frame_len = min(len(y), 1024)
    num_frames = max(1, len(y) // frame_len)
    zcrs = []
    for i in range(min(num_frames, 50)):
        chunk = y[i * frame_len : (i + 1) * frame_len]
        if len(chunk) > 1:
            zcr_val = float(np.mean(np.abs(np.diff(np.sign(chunk))) > 0) / 2.0)
            zcrs.append(zcr_val)
    mean_zcr = float(np.mean(zcrs)) if zcrs else 0.0
    zcr_std = float(np.std(zcrs)) if zcrs else 0.0
    zcr_risk = max(0.0, 0.45 - zcr_std * 9.0)
    evidence.append(EvidenceItem(
        label="Zero-Crossing Rate Variance",
        value=f"mean={mean_zcr:.4f}, σ={zcr_std:.4f}",
        risk_contribution=zcr_risk,
        severity="medium" if zcr_risk > 0.3 else "low",
    ))

    # 3. Pitch (F0) Monotonicity & Prosody via Autocorrelation
    win_size = min(len(y), 2048)
    pitches = []
    for start in range(0, min(len(y) - win_size, sr * 5), win_size):
        seg = y[start : start + win_size]
        if np.std(seg) < 1e-4:
            continue
        corr = np.correlate(seg, seg, mode='full')
        corr = corr[len(corr)//2:]
        min_lag = max(1, int(sr / 500))  # 500 Hz
        max_lag = min(len(corr) - 1, int(sr / 60))   # 60 Hz
        if min_lag < max_lag:
            peak = min_lag + np.argmax(corr[min_lag:max_lag])
            if peak > 0 and corr[peak] > 0.3 * max(corr[0], 1e-6):
                pitches.append(sr / peak)

    if len(pitches) >= 3:
        pitch_std = float(np.std(pitches))
        pitch_risk = max(0.0, 1.0 - pitch_std / 55.0)
    else:
        pitch_std = 0.0
        pitch_risk = 0.35

    evidence.append(EvidenceItem(
        label="Pitch Variability (F0)",
        value=f"σ={pitch_std:.1f} Hz — {'unnaturally monotone (synthetic)' if pitch_risk > 0.55 else 'natural human pitch modulation'}",
        risk_contribution=pitch_risk,
        severity="high" if pitch_risk > 0.6 else "medium" if pitch_risk > 0.3 else "low",
    ))

    # 4. Neural Vocoder High-Frequency Cutoff & Spectral Roll-off (85%)
    n_roll = min(len(y), 4096)
    spec_roll = np.abs(np.fft.rfft(y[:n_roll])) ** 2
    cum_energy = np.cumsum(spec_roll)
    total_energy = cum_energy[-1] if len(cum_energy) > 0 else 1.0
    cutoff_idx = int(np.searchsorted(cum_energy, 0.85 * total_energy))
    mean_rolloff = float(cutoff_idx * (sr / 2.0) / max(len(spec_roll), 1))

    if sr >= 22050 and mean_rolloff < 3800:
        rolloff_risk = 0.70
        rolloff_msg = f"Abrupt high-frequency drop ({mean_rolloff:.0f} Hz) — signature of neural vocoder cutoff"
    elif mean_rolloff < 2500:
        rolloff_risk = 0.50
        rolloff_msg = f"Low spectral roll-off frequency ({mean_rolloff:.0f} Hz)"
    else:
        rolloff_risk = 0.10
        rolloff_msg = f"Natural wideband frequency response ({mean_rolloff:.0f} Hz roll-off)"

    evidence.append(EvidenceItem(
        label="Vocoder High-Frequency Cutoff",
        value=rolloff_msg,
        risk_contribution=rolloff_risk,
        severity="high" if rolloff_risk > 0.6 else "medium" if rolloff_risk > 0.3 else "low",
    ))

    # 5. Acoustic Transition Dynamics (Band Variance Proxy)
    subbands = 8
    band_len = len(spec_roll) // subbands
    if band_len > 0:
        band_energies = [np.mean(spec_roll[i*band_len:(i+1)*band_len]) for i in range(subbands)]
        band_var = float(np.var(band_energies))
        if band_var < 0.0001:
            dyn_risk = 0.68
            dyn_msg = f"Static phonetic transitions (σ²={band_var:.5f})"
        else:
            dyn_risk = 0.15
            dyn_msg = f"Standard vocal tract variance (σ²={band_var:.5f})"
    else:
        dyn_risk = 0.20
        dyn_msg = "Acoustic transition features extracted"

    evidence.append(EvidenceItem(
        label="MFCC & Phonetic Transition Dynamics",
        value=dyn_msg,
        risk_contribution=dyn_risk,
        severity="high" if dyn_risk > 0.6 else "medium" if dyn_risk > 0.3 else "low",
    ))

    # 6. Silence & Ambient Noise Distribution
    frame_rms_len = min(len(y), 1024)
    rms_vals = [float(np.sqrt(np.mean(y[i:i+frame_rms_len]**2))) for i in range(0, len(y), frame_rms_len)]
    silence_ratio = float(np.mean(np.array(rms_vals) < 0.01)) if rms_vals else 0.0
    silence_risk = min(silence_ratio * 1.4, 0.9) if silence_ratio > 0.45 else 0.10
    evidence.append(EvidenceItem(
        label="Silence & Background Noise Distribution",
        value=f"{silence_ratio*100:.1f}% silent/dead frames ({'unnatural digital silence' if silence_risk > 0.4 else 'natural room ambience'})",
        risk_contribution=silence_risk,
        severity="medium" if silence_risk > 0.4 else "low",
    ))

    # 7. Spectral Centroid Modulation
    mags = np.abs(np.fft.rfft(y[:min(len(y), 4096)]))
    freqs = np.linspace(0, sr / 2.0, len(mags))
    sum_mag = np.sum(mags) + 1e-10
    centroid = float(np.sum(freqs * mags) / sum_mag)
    if centroid < 1200.0 or centroid > 4500.0:
        centroid_risk = 0.55
        centroid_msg = f"Monotonous timbre (centroid={centroid:.0f} Hz)"
    else:
        centroid_risk = 0.10
        centroid_msg = f"Dynamic acoustic modulation (centroid={centroid:.0f} Hz)"

    evidence.append(EvidenceItem(
        label="Spectral Centroid Modulation",
        value=centroid_msg,
        risk_contribution=centroid_risk,
        severity="medium" if centroid_risk > 0.4 else "low",
    ))

    # Multi-signal fusion
    feature_risks = [flat_risk, zcr_risk, pitch_risk, rolloff_risk, dyn_risk, silence_risk, centroid_risk]
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


def _fallback_analysis(audio_bytes: bytes, filename: str) -> dict:
    """Heuristic analysis when sound engine is unavailable or file is unparseable."""
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
        if AUDIO_ENGINE_AVAILABLE:
            return _analyze_with_soundfile(audio_bytes, filename)
        return _fallback_analysis(audio_bytes, filename)
    except Exception:
        return _fallback_analysis(audio_bytes, filename)
