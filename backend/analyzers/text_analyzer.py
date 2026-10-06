"""
Text Analyzer — Scam SMS, Phishing Email & Malicious URL Detection
Uses advanced rule-based NLP: homoglyph/leetspeak de-obfuscation, intent co-occurrence,
Shannon entropy, and multi-factor URL heuristics.
"""
import math
import re
import unicodedata
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from schemas import EvidenceItem

# Top-level domains heavily abused by phishing / bulletproof infrastructure
SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "top", "xyz", "buzz", "work", "click",
    "rest", "icu", "cam", "sbs", "monster", "bar", "download", "stream",
    "win", "bid", "loan", "men", "party", "accountant", "date", "faith",
    "racing", "cricket", "science", "space", "cfd", "hair", "beauty"
}

# Known URL shorteners used to cloak landing pages
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "cutt.ly",
    "is.gd", "rb.gy", "rebrand.ly", "buff.ly", "shorturl.at", "tiny.cc"
}

# High-value brands targeted for impersonation
TARGETED_BRANDS = [
    "paypal", "apple", "google", "microsoft", "netflix", "amazon",
    "chase", "wellsfargo", "bankofamerica", "citibank", "hsbc",
    "binance", "coinbase", "metamask", "whatsapp", "telegram",
    "facebook", "instagram", "steam", "fedex", "ups", "usps", "dhl"
]

# Common Cyrillic / Greek homoglyphs used in IDN and text spoofing
HOMOGLYPH_MAP = {
    'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o', 'р': 'p', 'х': 'x', 'у': 'y',
    'і': 'i', 'ј': 'j', 'ѕ': 's', 'ԁ': 'd', 'ԛ': 'q', 'ԝ': 'w',
    'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H', 'І': 'I', 'Ј': 'J',
    'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T', 'Х': 'X', 'Ү': 'Y'
}

# Common leetspeak substitutions
LEET_MAP = {
    '@': 'a', '0': 'o', '1': 'i', '$': 's', '5': 's', '3': 'e',
    '!': 'i', '|': 'i', '8': 'b', '7': 't', '+': 't'
}


def normalize_text(text: str) -> str:
    """
    De-obfuscates text:
    1. Unicode NFKC normalization.
    2. Strips zero-width and invisible formatting characters.
    3. Replaces common homoglyphs with standard ASCII equivalents.
    4. Normalizes leetspeak symbols within suspicious contexts.
    """
    normalized = unicodedata.normalize("NFKC", text)
    # Strip zero-width spaces, joiners, direction marks
    normalized = re.sub(r"[\u200B-\u200D\uFEFF\u202A-\u202E\u00AD]", "", normalized)

    # Replace homoglyphs
    chars = [HOMOGLYPH_MAP.get(ch, ch) for ch in normalized]
    result = "".join(chars)

    # Replace common leetspeak characters
    leet_decoded = []
    for ch in result:
        leet_decoded.append(LEET_MAP.get(ch, ch))
    return "".join(leet_decoded)


def _calculate_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string (in bits per char)."""
    if not s:
        return 0.0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in prob)


def analyze_url(raw_url: str) -> dict:
    url = raw_url.strip()
    # Normalize homoglyphs in URL string
    url = normalize_text(url)

    if not url.startswith(("http://", "https://")):
        url_to_parse = "https://" + url
    else:
        url_to_parse = url

    try:
        parsed = urlparse(url_to_parse)
        host = (parsed.hostname or "").lower()
        path = (parsed.path or "").lower()
        query = (parsed.query or "").lower()
    except Exception:
        host = ""
        path = ""
        query = ""

    evidence: List[EvidenceItem] = []
    risks = []

    # 1. Protocol Security
    is_http = raw_url.strip().lower().startswith("http://")
    proto_risk = 0.45 if is_http else 0.0
    evidence.append(EvidenceItem(
        label="Protocol Encryption",
        value="Unencrypted HTTP scheme (credentials exposed in transit)" if is_http else "Encrypted HTTPS scheme detected",
        risk_contribution=proto_risk,
        severity="medium" if is_http else "low"
    ))
    risks.append(proto_risk)

    # 2. Host IP Address / Obfuscation
    is_ip = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host))
    is_hex_octal_ip = bool(re.match(r"^0x[0-9a-f]+|0\d+$", host))
    ip_risk = 0.85 if (is_ip or is_hex_octal_ip) else 0.0
    evidence.append(EvidenceItem(
        label="Host Structure",
        value=f"Raw IP address used as hostname ({host}) — high phishing correlation" if is_ip else
              (f"Obfuscated numeric/hex IP ({host})" if is_hex_octal_ip else f"Valid standard domain format ({host})"),
        risk_contribution=ip_risk,
        severity="high" if (is_ip or is_hex_octal_ip) else "low"
    ))
    risks.append(ip_risk)

    # 3. Suspicious / Abused TLD
    tld = host.split(".")[-1] if "." in host else ""
    tld_suspicious = tld in SUSPICIOUS_TLDS
    tld_risk = 0.65 if tld_suspicious else 0.0
    evidence.append(EvidenceItem(
        label="Top-Level Domain (TLD) Reputation",
        value=f"High-abuse TLD detected (.{tld})" if tld_suspicious else f"Standard TLD (.{tld})",
        risk_contribution=tld_risk,
        severity="high" if tld_suspicious else "low"
    ))
    risks.append(tld_risk)

    # 4. URL Shortener / Redirect Cloak
    is_shortener = host in SHORTENERS
    short_risk = 0.55 if is_shortener else 0.0
    evidence.append(EvidenceItem(
        label="Link Cloaking / Shortener",
        value=f"URL Shortener detected ({host}) hiding real destination" if is_shortener else "Direct unshortened destination link",
        risk_contribution=short_risk,
        severity="medium" if is_shortener else "low"
    ))
    risks.append(short_risk)

    # 5. Shannon Entropy & Random Domain / DGA Detection
    domain_label = host.split(".")[0] if "." in host else host
    entropy = _calculate_entropy(domain_label)
    # Natural words typically have entropy between 2.2 and 3.6; DGA/random chars exceed 3.8
    entropy_risk = 0.0
    if len(domain_label) >= 8 and entropy > 3.85:
        entropy_risk = min(0.40 + (entropy - 3.85) * 0.5, 0.75)
    evidence.append(EvidenceItem(
        label="Domain Randomness & Entropy",
        value=f"Shannon entropy: {entropy:.2f} bits ({'anomalously random domain label / DGA' if entropy_risk > 0.3 else 'natural lexical distribution'})",
        risk_contribution=entropy_risk,
        severity="high" if entropy_risk > 0.5 else "medium" if entropy_risk > 0.2 else "low"
    ))
    risks.append(entropy_risk)

    # 6. Brand Impersonation, Typosquatting & Subdomain Deception
    impersonated = []
    subdomain_deception = []
    host_parts = host.split(".")
    registered_domain = ".".join(host_parts[-2:]) if len(host_parts) >= 2 else host

    for brand in TARGETED_BRANDS:
        if brand in host:
            # Check if brand is legitimately in the registered domain
            legitimate_domains = (f"{brand}.com", f"{brand}.org", f"{brand}.net", f"{brand}.co", f"{brand}.io")
            if registered_domain not in legitimate_domains:
                impersonated.append(brand)
                # Check if brand was deliberately positioned in subdomain prefix
                if len(host_parts) > 2 and any(brand in p for p in host_parts[:-2]):
                    subdomain_deception.append(brand)

    brand_risk = 0.92 if impersonated else 0.0
    brand_msg = f"Impersonation detected targeting: {', '.join(impersonated)}"
    if subdomain_deception:
        brand_msg += f" (deceptively embedded in subdomain prefix: {', '.join(subdomain_deception)})"
    if not impersonated:
        brand_msg = "No obvious brand name spoofing in domain"

    evidence.append(EvidenceItem(
        label="Brand Impersonation & Typosquatting",
        value=brand_msg,
        risk_contribution=brand_risk,
        severity="high" if brand_risk > 0.5 else "low"
    ))
    risks.append(brand_risk)

    # 7. Credential Harvesting Cues in Path & Query
    harvesting_cues = [
        "login", "signin", "verify", "auth", "account", "security",
        "update", "wallet", "seed", "kyc", "banking", "recovery", "password",
        "credential", "session", "oauth", "confirm", "passcode"
    ]
    found_cues = [c for c in harvesting_cues if c in path or c in query or c in host]
    path_risk = min(0.35 * len(found_cues), 0.90) if found_cues else 0.0
    evidence.append(EvidenceItem(
        label="Credential Harvesting Indicators",
        value=f"Sensitive account keywords in URL: {', '.join(found_cues)}" if found_cues else "No credential-harvesting triggers in path",
        risk_contribution=path_risk,
        severity="high" if path_risk > 0.5 else "medium" if path_risk > 0.2 else "low"
    ))
    risks.append(path_risk)

    # 8. Excessive Subdomain Depth & Delimiter Stacking
    subdomain_count = max(0, len(host_parts) - 2)
    hyphen_count = host.count("-")
    structure_risk = 0.0
    if subdomain_count >= 3 or hyphen_count >= 3:
        structure_risk = min(0.30 + (subdomain_count * 0.1) + (hyphen_count * 0.08), 0.70)
        evidence.append(EvidenceItem(
            label="Domain Obfuscation Structure",
            value=f"Complex nesting: {subdomain_count} subdomains, {hyphen_count} hyphens (common cloak tactic)",
            risk_contribution=structure_risk,
            severity="medium" if structure_risk < 0.5 else "high"
        ))
        risks.append(structure_risk)

    # Calibrated Risk Synthesis
    max_risk = max(risks)
    active_risks = [r for r in risks if r > 0.15]
    if max_risk >= 0.65:
        overall_risk = max_risk
        if len(active_risks) > 1:
            overall_risk = min(overall_risk + 0.15 * (len(active_risks) - 1), 1.0)
    else:
        overall_risk = sum(active_risks) / 2.0
        overall_risk = min(max(overall_risk, max_risk), 1.0)

    risk_score = round(min(overall_risk * 100, 100), 1)

    if risk_score >= 60:
        verdict = "HIGH_RISK"
        summary = "Malicious or fraudulent URL detected. High probability of phishing or credential theft."
    elif risk_score >= 30:
        verdict = "SUSPICIOUS"
        summary = "Suspicious URL characteristics detected. Do not enter passwords or personal data."
    else:
        verdict = "SAFE"
        summary = "URL appears safe. No typical phishing or obfuscation patterns detected."

    recommendations = [
        "Do NOT enter any personal details, usernames, or passwords on this site." if verdict != "SAFE" else "Always verify SSL padlock and exact domain spelling.",
        "Check domain registration and certificate details before interacting." if verdict != "SAFE" else "Exercise standard browsing precautions.",
        "Report phishing links to Google Safe Browsing and PhishTank." if verdict == "HIGH_RISK" else "Ensure your browser's anti-phishing protection is active."
    ]

    return {
        "risk_score": risk_score,
        "verdict": verdict,
        "summary": summary,
        "evidence": evidence,
        "recommendations": recommendations,
        "risk_level": verdict,
        "confidence": risk_score / 100.0,
    }


# ── Keyword Banks with Word Boundary Matching ─────────────────────────────────

URGENCY_PHRASES = [
    "act now", "urgent", "immediately", "limited time", "expires today",
    "last chance", "don't delay", "respond asap", "action required",
    "your account will be suspended", "verify now", "confirm immediately",
    "account compromised", "security alert", "unauthorized access",
    "lock", "locked", "suspended", "frozen", "deactivated", "disabled",
    "due today", "final notice", "pay now", "asap", "immediate action",
    "within 24 hours", "24 hours", "close your account"
]

LURE_PHRASES = [
    "you have won", "congratulations", "you've been selected",
    "free gift", "claim your prize", "lottery", "jackpot", "reward",
    "you are a winner", "gift card", "cash prize", "lucky winner",
    "giveaway", "free voucher", "cash reward", "bonus payout",
    "refund pending", "unclaimed funds"
]

THREAT_PHRASES = [
    "legal action", "arrest warrant", "irs", "police", "lawsuit",
    "court order", "debt collector", "criminal charges", "fbi",
    "seized", "penalty", "fine", "overdue", "debt", "block", "blocked",
    "jail", "sued", "unpaid fee", "tax evasion", "prosecution"
]

REQUEST_PHRASES = [
    "click here", "click the link", "click below", "tap here",
    "provide your", "enter your", "confirm your", "update your",
    "verify your account", "login to", "sign in to",
    "send money", "wire transfer", "bitcoin", "crypto", "gift card",
    "social security", "ssn", "password", "credit card", "cvv", "pin",
    "bank account", "routing number", "otp", "one-time password",
    "verification code", "card details", "login credentials", "verify info"
]

BRAND_IMPERSONATION = [
    "paypal", "amazon", "netflix", "apple", "microsoft", "google",
    "facebook", "instagram", "whatsapp", "irs", "social security",
    "bank of america", "chase", "wells fargo", "citibank", "hsbc",
    "fedex", "ups", "usps", "dhl", "post office", "security department"
]

SUSPICIOUS_URL_PATTERNS = [
    r"bit\.ly", r"tinyurl\.com", r"t\.co", r"goo\.gl", r"ow\.ly",
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # IP address URLs
    r"[a-z0-9-]{20,}\.",                    # Very long subdomains
    r"secure.*login", r"verify.*account", r"update.*info",
    r"\.(tk|ml|ga|cf|gq|xyz|top|sbs|buzz)($|/|\?)",
]

URL_REGEX = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"
)


def _count_matches_boundary(text: str, phrases: List[str]) -> Tuple[int, List[str]]:
    """
    Match phrases using word boundaries (\b) to eliminate substring false positives
    like 'lock' in 'clockwise' or 'irs' in 'first'.
    """
    text_lower = text.lower()
    found = []
    for p in phrases:
        # For multi-word phrases or single words, enforce word boundaries
        pattern = rf"(?<!\w){re.escape(p)}(?!\w)"
        if re.search(pattern, text_lower):
            found.append(p)
    return len(found), found


def _analyze_urls(text: str) -> Tuple[float, str, List[str]]:
    urls = URL_REGEX.findall(text)
    if not urls:
        return 0.0, "No URLs found", []

    suspicious = []
    for url in urls:
        # Check through quick patterns
        flagged = False
        for pattern in SUSPICIOUS_URL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                suspicious.append(url)
                flagged = True
                break
        if not flagged:
            # Also run quick host heuristics
            try:
                parsed = urlparse(url if url.startswith("http") else "http://" + url)
                host = parsed.hostname or ""
                tld = host.split(".")[-1] if "." in host else ""
                if tld in SUSPICIOUS_TLDS or host in SHORTENERS or _calculate_entropy(host.split(".")[0]) > 3.85:
                    suspicious.append(url)
            except Exception:
                pass

    if len(suspicious) == 0:
        return 0.1, f"{len(urls)} URL(s) found, none obviously suspicious", urls
    ratio = len(suspicious) / len(urls)
    return min(0.35 + ratio * 0.65, 1.0), f"{len(suspicious)}/{len(urls)} URLs are suspicious", suspicious


def _grammar_score(text: str) -> Tuple[float, str]:
    """Writing quality and spoofing artifact heuristic."""
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
    question_marks = text.count("?")
    if exclamations > 3 or (exclamations + question_marks) > 4:
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
    mode: 'sms', 'email', or 'url'
    """
    if mode == "url":
        return analyze_url(text)

    try:
        # Normalize text to defang homoglyph and zero-width cloaking
        cleaned_text = normalize_text(text)

        evidence: List[EvidenceItem] = []

        # 1. Urgency
        urgency_count, urgency_found = _count_matches_boundary(cleaned_text, URGENCY_PHRASES)
        urgency_risk = min(urgency_count * 0.35, 1.0)
        evidence.append(EvidenceItem(
            label="Urgency & Pressure Tactics",
            value=f"{urgency_count} phrase(s): {', '.join(urgency_found[:3]) or 'none'}",
            risk_contribution=urgency_risk,
            severity="high" if urgency_risk > 0.5 else "medium" if urgency_risk > 0.2 else "low",
        ))

        # 2. Lure phrases
        lure_count, lure_found = _count_matches_boundary(cleaned_text, LURE_PHRASES)
        lure_risk = min(lure_count * 0.40, 1.0)
        evidence.append(EvidenceItem(
            label="Reward / Lure Language",
            value=f"{lure_count} phrase(s): {', '.join(lure_found[:3]) or 'none'}",
            risk_contribution=lure_risk,
            severity="high" if lure_risk > 0.5 else "medium" if lure_risk > 0.2 else "low",
        ))

        # 3. Threats
        threat_count, threat_found = _count_matches_boundary(cleaned_text, THREAT_PHRASES)
        threat_risk = min(threat_count * 0.40, 1.0)
        evidence.append(EvidenceItem(
            label="Threat / Fear Language",
            value=f"{threat_count} phrase(s): {', '.join(threat_found[:3]) or 'none'}",
            risk_contribution=threat_risk,
            severity="high" if threat_risk > 0.5 else "medium" if threat_risk > 0.2 else "low",
        ))

        # 4. Information requests
        req_count, req_found = _count_matches_boundary(cleaned_text, REQUEST_PHRASES)
        req_risk = min(req_count * 0.40, 1.0)
        evidence.append(EvidenceItem(
            label="Sensitive Information Requests",
            value=f"{req_count} phrase(s): {', '.join(req_found[:3]) or 'none'}",
            risk_contribution=req_risk,
            severity="high" if req_risk > 0.5 else "medium" if req_risk > 0.2 else "low",
        ))

        # 5. Brand impersonation
        brand_count, brand_found = _count_matches_boundary(cleaned_text, BRAND_IMPERSONATION)
        brand_risk = min(brand_count * 0.30, 0.8)
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

        # 8. Intent Synergy / Co-occurrence Bonus:
        # Phishing relies on synergy: [Pressure (Urgency/Threat/Lure)] + [Target/Action (Request/URL/Brand)]
        has_pressure = (urgency_risk > 0.2 or threat_risk > 0.2 or lure_risk > 0.2)
        has_action = (req_risk > 0.2 or url_risk > 0.3)
        has_target = (brand_risk > 0.2)
        synergy_boost = 0.0
        if has_pressure and has_action:
            synergy_boost += 0.20
            if has_target:
                synergy_boost += 0.15
            evidence.append(EvidenceItem(
                label="Multi-Vector Intent Co-occurrence",
                value="High-confidence phishing pattern: combines social engineering pressure with call-to-action",
                risk_contribution=min(synergy_boost, 0.35),
                severity="high"
            ))

        # Non-linear combination
        risks = [urgency_risk, lure_risk, threat_risk, req_risk, brand_risk, url_risk, grammar_risk]
        if synergy_boost > 0:
            risks.append(synergy_boost)

        max_risk = max(risks)
        active_risks = [r for r in risks if r > 0.15]

        if max_risk >= 0.65 or synergy_boost >= 0.30:
            overall_risk = max(max_risk, 0.70)
            if len(active_risks) > 1:
                overall_risk = min(overall_risk + 0.15 * (len(active_risks) - 1), 1.0)
        else:
            overall_risk = sum(active_risks) / 2.0
            overall_risk = min(max(overall_risk, max_risk), 1.0)

        risk_score = round(min(overall_risk * 100, 100), 1)

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
            "risk_level": verdict,
            "confidence": risk_score / 100.0,
        }
    except Exception as e:
        return {
            "risk_score": 0.0,
            "verdict": "SAFE",
            "summary": f"Could not analyze text due to internal error: {str(e)}",
            "evidence": [],
            "recommendations": [],
            "risk_level": "SAFE",
            "confidence": 0.0,
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

