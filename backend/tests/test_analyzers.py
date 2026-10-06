"""
Unit & Integration Tests for TrustLens AI Analyzers and Endpoints
"""
import io
import sys
import os
from PIL import Image

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzers.image_analyzer import analyze_image
from analyzers.text_analyzer import analyze_text, analyze_url
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "database" in response.json()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"


def test_image_analyzer_valid():
    # Generate a dummy RGB image
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    result = analyze_image(img_bytes, "test.jpg")
    assert "risk_score" in result
    assert "verdict" in result
    assert "evidence" in result
    assert "visual_artifact" in result
    assert result["visual_artifact"] is not None
    assert result["visual_artifact"].startswith("data:image/png;base64,")


def test_image_analyzer_corrupted():
    result = analyze_image(b"not-an-image-data", "broken.jpg")
    assert "risk_score" in result
    assert result["verdict"] in ("SAFE", "SUSPICIOUS", "HIGH_RISK")


def test_url_analyzer_phishing():
    phishing_url = "http://paypal-security-account-update.xyz/login"
    result = analyze_url(phishing_url)
    assert result["risk_score"] >= 60
    assert result["verdict"] == "HIGH_RISK"
    evidence_labels = [e.label for e in result["evidence"]]
    assert "Brand Impersonation & Typosquatting" in evidence_labels
    assert "Credential Harvesting Indicators" in evidence_labels


def test_url_analyzer_safe():
    safe_url = "https://www.google.com"
    result = analyze_url(safe_url)
    assert result["risk_score"] < 40
    assert result["verdict"] == "SAFE"


def test_text_analyzer_sms_scam():
    scam_sms = "URGENT: Your bank account is locked! Click http://bit.ly/bank-auth immediately to claim your cash prize and verify SSN."
    result = analyze_text(scam_sms, mode="sms")
    assert result["risk_score"] >= 60
    assert result["verdict"] == "HIGH_RISK"


def test_text_analyzer_benign():
    benign_text = "Hey! Let's meet at the coffee shop at 4pm today."
    result = analyze_text(benign_text, mode="sms")
    assert result["risk_score"] < 30
    assert result["verdict"] == "SAFE"


def test_api_text_endpoint_url_mode():
    response = client.post(
        "/api/analyze/text",
        data={"text": "http://chase-security-verify.top/signin", "mode": "url"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scan_type"] == "url"
    assert data["verdict"] == "HIGH_RISK"
    assert len(data["evidence"]) > 0


def test_text_analyzer_homoglyph_deobfuscation():
    # 'р' and 'а' are Cyrillic homoglyphs, and '1' is leetspeak for 'i'
    obfuscated_scam = "URGENT: Your pаypal account will be suspended! Verify your b1tcoin wallet password immediately."
    result = analyze_text(obfuscated_scam, mode="sms")
    assert result["risk_score"] >= 60
    assert result["verdict"] == "HIGH_RISK"
    evidence_labels = [e.label for e in result["evidence"]]
    assert "Brand Impersonation" in evidence_labels or "Sensitive Information Requests" in evidence_labels


def test_text_analyzer_word_boundaries():
    # "clockwise" contains "lock", "first" contains "irs"
    benign_text = "Please turn clockwise on the first intersection to reach the park."
    result = analyze_text(benign_text, mode="sms")
    assert result["verdict"] == "SAFE"
    assert result["risk_score"] < 30


def test_url_analyzer_subdomain_deception_and_entropy():
    # Brand is in subdomain prefix rather than registered domain, plus high-abuse TLD
    deceptive_url = "http://paypal.com.account-verify-login.xyz/session"
    result = analyze_url(deceptive_url)
    assert result["verdict"] == "HIGH_RISK"
    evidence_labels = [e.label for e in result["evidence"]]
    assert "Brand Impersonation & Typosquatting" in evidence_labels
    assert "Domain Randomness & Entropy" in evidence_labels or "Top-Level Domain (TLD) Reputation" in evidence_labels


def test_image_analyzer_ai_evidence():
    # Verify presence of multi-domain forensics on generated image
    img = Image.new("RGB", (512, 512), color=(120, 140, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = analyze_image(buf.getvalue(), "sample.png")

    evidence_labels = [e.label for e in result["evidence"]]
    assert "Frequency Spectrum Analysis (2D FFT)" in evidence_labels
    assert "Sensor Noise & Texture Consistency" in evidence_labels
    assert "Deep Feature Latent Analysis" in evidence_labels
    assert "Error Level Analysis (ELA)" in evidence_labels


def test_history_invalid_id():
    response = client.get("/api/history/invalid-nonexistent-id")
    assert response.status_code == 404


def test_auth_quick_demo_login():
    response = client.post(
        "/api/auth/login",
        json={"email": "demo_operative@trustlens.ai", "auth_type": "quick_demo"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "demo_operative@trustlens.ai"


def test_password_hashing_and_verification():
    import database
    pwd = "super-secret-password-123"
    hashed = database.hash_password(pwd)
    assert database.verify_password(pwd, hashed) is True
    assert database.verify_password("wrong-password", hashed) is False


if __name__ == "__main__":
    tests = [
        test_health_check,
        test_root_endpoint,
        test_image_analyzer_valid,
        test_image_analyzer_corrupted,
        test_image_analyzer_ai_evidence,
        test_url_analyzer_phishing,
        test_url_analyzer_safe,
        test_text_analyzer_sms_scam,
        test_text_analyzer_benign,
        test_api_text_endpoint_url_mode,
        test_text_analyzer_homoglyph_deobfuscation,
        test_text_analyzer_word_boundaries,
        test_url_analyzer_subdomain_deception_and_entropy,
        test_history_invalid_id,
        test_auth_quick_demo_login,
        test_password_hashing_and_verification,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} - {e}")
            raise e
    print(f"\nCompleted: {passed}/{len(tests)} tests passed.")



