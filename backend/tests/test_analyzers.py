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
    assert response.json() == {"status": "healthy"}


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


if __name__ == "__main__":
    tests = [
        test_health_check,
        test_root_endpoint,
        test_image_analyzer_valid,
        test_image_analyzer_corrupted,
        test_url_analyzer_phishing,
        test_url_analyzer_safe,
        test_text_analyzer_sms_scam,
        test_text_analyzer_benign,
        test_api_text_endpoint_url_mode,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} - {e}")
    print(f"\nCompleted: {passed}/{len(tests)} tests passed.")
    if passed < len(tests):
        sys.exit(1)

