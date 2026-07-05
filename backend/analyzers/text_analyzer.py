"""
Text Analyzer — Scam SMS & Email Phishing Detection
Uses rule-based NLP: keyword scoring, URL analysis, urgency patterns.
"""
import re
from typing import List, Tuple
from schemas import EvidenceItem


# ── Keyword banks ──────────────────────────────────────────────────────────────

URGENCY_PHRASES = [
    "act now", "urgent", "immediately", "limited time", "expires today",
    "last chance", "don't delay", "respond asap", "action required",
    "your account will be suspended", "verify now", "confirm immediately",
    "account compromised", "security alert", "unauthorized access",
]

LURE_PHRASES = [
    "you have won", "congratulations", "you've been selected",
    "free gift", "claim your prize", "lottery", "jackpot", "reward",
    "you are a winner", "gift card", "cash prize", "lucky winner",
]

THREAT_PHRASES = [
    "legal action", "arrest warrant", "irs", "police", "lawsuit",
    "court order", "debt collector", "criminal charges", "fbi",
    "seized", "penalty", "fine", "overdue", "debt",
]

REQUEST_PHRASES = [
    "click here", "click the link", "click below", "tap here",
    "provide your", "enter your", "confirm your", "update your",
    "verify your account", "login to", "sign in to",
    "send money", "wire transfer", "bitcoin", "crypto", "gift card",
    "social security", "ssn", "password", "credit card", "cvv", "pin",
    "bank account", "routing number",
]

BRAND_IMPERSONATION = [
    "paypal", "amazon", "netflix", "apple", "microsoft", "google",
    "facebook", "instagram", "whatsapp", "irs", "social security",
    "bank of america", "chase", "wells fargo", "citibank", "hsbc",
    "fedex", "ups", "usps", "dhl",
]

SUSPICIOUS_URL_PATTERNS = [
    r"bit\.ly", r"tinyurl\.com", r"t\.co", r"goo\.gl", r"ow\.ly",
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # IP address URLs
    r"[a-z0-9-]{20,}\.",                       # Very long subdomains
    r"secure.*login", r"verify.*account", r"update.*info",
    r"\.tk$", r"\.ml$", r"\.ga$", r"\.cf$",   # Cheap TLDs
]

URL_REGEX = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"
)


# ── Helper functions ────────────────────────────────────────────────────────────

def _count_matches(text: str, phrases: List[str]) -> Tuple[int, List[str]]:
    text_lower = text.lower()
    found = [p for p in phrases if p in text_lower]
    return len(found), found


def _analyze_urls(text: str) -> Tuple[float, str, List[str]]:
    urls = URL_REGEX.findall(text)
    if not urls:
        return 0.0, "No URLs found", []

    suspicious = []
    for url in urls:
        for pattern in SUSPICIOUS_URL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                suspicious.append(url)
                break

    if len(suspicious) == 0:
        return 0.1, f"{len(urls)} URL(s) found, none obviously suspicious", urls
    ratio = len(suspicious) / len(urls)
    return min(0.3 + ratio * 0.6, 1.0), f"{len(suspicious)}/{len(urls)} URLs are suspicious", suspicious


def _grammar_score(text: str) -> Tuple[float, str]:
    """Simple grammar/formality heuristic."""
    issues = 0
    words = text.split()
    if not words:
        return 0.0, "Empty message"

    # ALL CAPS ratio
    caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1)
    if caps_ratio > 0.3:
        issues += 2

    # Excessive punctuation
    exclamations = text.count("!")
    if exclamations > 3:
        issues += 1

    # Numbers where letters expected (l33t speak / randomization)
    l33t_count = len(re.findall(r"\b\w*[0-9]+\w*[a-zA-Z]+\w*\b", text))
    if l33t_count > 2:
        issues += 1

    risk = min(issues * 0.15, 0.7)
    msg = f"Writing quality indicators: CAPS={caps_ratio:.0%}, exclamations={exclamations}"
    return risk, msg


def analyze_text(text: str, mode: str = "sms") -> dict:
    """
    mode: 'sms' or 'email'
    """
    try:
        evidence: List[EvidenceItem] = []

        # 1. Urgency
        urgency_count, urgency_found = _count_matches(text, URGENCY_PHRASES)
        urgency_risk = min(urgency_count * 0.18, 1.0)
        evidence.append(EvidenceItem(
            label="Urgency & Pressure Tactics",
            value=f"{urgency_count} phrase(s): {', '.join(urgency_found[:3]) or 'none'}",
            risk_contribution=urgency_risk,
            severity="high" if urgency_risk > 0.5 else "medium" if urgency_risk > 0.2 else "low",
        ))

        # 2. Lure phrases
        lure_count, lure_found = _count_matches(text, LURE_PHRASES)
        lure_risk = min(lure_count * 0.25, 1.0)
        evidence.append(EvidenceItem(
            label="Reward / Lure Language",
            value=f"{lure_count} phrase(s): {', '.join(lure_found[:3]) or 'none'}",
            risk_contribution=lure_risk,
            severity="high" if lure_risk > 0.5 else "medium" if lure_risk > 0.2 else "low",
        ))

        # 3. Threats
        threat_count, threat_found = _count_matches(text, THREAT_PHRASES)
        threat_risk = min(threat_count * 0.25, 1.0)
        evidence.append(EvidenceItem(
            label="Threat / Fear Language",
            value=f"{threat_count} phrase(s): {', '.join(threat_found[:3]) or 'none'}",
            risk_contribution=threat_risk,
            severity="high" if threat_risk > 0.5 else "medium" if threat_risk > 0.2 else "low",
        ))

        # 4. Information requests
        req_count, req_found = _count_matches(text, REQUEST_PHRASES)
        req_risk = min(req_count * 0.20, 1.0)
        evidence.append(EvidenceItem(
            label="Sensitive Information Requests",
            value=f"{req_count} phrase(s): {', '.join(req_found[:3]) or 'none'}",
            risk_contribution=req_risk,
            severity="high" if req_risk > 0.5 else "medium" if req_risk > 0.2 else "low",
        ))

        # 5. Brand impersonation
        brand_count, brand_found = _count_matches(text, BRAND_IMPERSONATION)
        brand_risk = min(brand_count * 0.15, 0.6)
        evidence.append(EvidenceItem(
            label="Brand Impersonation",
            value=f"Mentions: {', '.join(brand_found[:4]) or 'none'}",
            risk_contribution=brand_risk,
            severity="high" if brand_risk > 0.4 else "medium" if brand_risk > 0.15 else "low",
        ))

        # 6. URL analysis
        url_risk, url_msg, urls = _analyze_urls(text)
        evidence.append(EvidenceItem(
            label="URL / Link Analysis",
            value=url_msg,
            risk_contribution=url_risk,
            severity="high" if url_risk > 0.6 else "medium" if url_risk > 0.3 else "low",
        ))

        # 7. Grammar / writing style
        grammar_risk, grammar_msg = _grammar_score(text)
        evidence.append(EvidenceItem(
            label="Writing Style Analysis",
            value=grammar_msg,
            risk_contribution=grammar_risk,
            severity="medium" if grammar_risk > 0.3 else "low",
        ))

        weights = [0.20, 0.18, 0.18, 0.20, 0.10, 0.09, 0.05]
        risks = [urgency_risk, lure_risk, threat_risk, req_risk, brand_risk, url_risk, grammar_risk]
        raw_score = sum(w * r for w, r in zip(weights, risks))
        risk_score = round(min(raw_score * 100, 100), 1)

        if risk_score >= 60:
            verdict = "HIGH_RISK"
            summary = (
                "This message exhibits multiple high-confidence scam indicators. "
                "It is very likely a phishing attempt or fraud."
            )
        elif risk_score >= 30:
            verdict = "SUSPICIOUS"
            summary = "Several red flags detected. Treat this message with significant caution."
        else:
            verdict = "SAFE"
            summary = "No major scam indicators found. Message appears legitimate."

        recommendations = _get_recommendations(verdict, mode)

        return {
            "risk_score": risk_score,
            "verdict": verdict,
            "summary": summary,
            "evidence": evidence,
            "recommendations": recommendations,
        }
    except Exception as e:
        return {
            "risk_score": 0.0,
            "verdict": "SAFE",
            "summary": f"Could not analyze text due to internal error: {str(e)}",
            "evidence": [],
            "recommendations": [],
        }


def _get_recommendations(verdict: str, mode: str) -> List[str]:
    base = {
        "SAFE": [
            "Message appears safe — stay vigilant regardless.",
            "Never share passwords or financial info via message.",
        ],
        "SUSPICIOUS": [
            "Do NOT click any links in this message.",
            "Verify the sender's identity through official channels.",
            "Do not reply or provide any information.",
            "Block the sender if unsolicited.",
        ],
        "HIGH_RISK": [
            "SCAM DETECTED — Do not respond, click links, or share information.",
            "Block and report the sender immediately.",
            "Forward to 7726 (SPAM) for SMS reporting in the US/UK.",
            "Report phishing emails to reportphishing@apwg.org or your email provider.",
            "Warn others if this is circulating in your network.",
            "If you already responded, contact your bank or change passwords immediately.",
        ],
    }
    return base.get(verdict, [])
