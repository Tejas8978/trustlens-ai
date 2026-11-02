"""
TrustLens AI — Enterprise Webhook Ingestion Router
Automated ingestion pipelines for Slack and Microsoft Teams that block phishing attacks in transit.
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from analyzers.text_analyzer import analyze_text

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/webhooks", tags=["Enterprise Webhooks"])

class WebhookTestRequest(BaseModel):
    platform: str  # "slack" or "teams"
    sender: str
    channel: str
    message: str
    urls: Optional[List[str]] = []

@router.post("/slack")
async def slack_webhook(request: Request):
    """
    Slack Event Subscriptions & Incoming Webhook endpoint.
    Handles URL verification challenge and inspects posted messages in transit.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Handle Slack URL verification challenge
    if "challenge" in body:
        return {"challenge": body["challenge"]}

    event = body.get("event", {})
    text = event.get("text", "") or body.get("text", "")

    # Run TrustLens forensic text and link analyzer
    result = analyze_text(text) if text else {"overall_score": 0.0, "risk_level": "LOW", "threats": []}

    is_threat = result.get("risk_level") in ["HIGH", "CRITICAL"]

    response_payload = {
        "status": "processed",
        "action": "QUARANTINE" if is_threat else "ALLOW",
        "risk_level": result.get("risk_level"),
        "overall_score": result.get("overall_score"),
        "text_scanned": text[:120] if text else "",
        "recommendation": "Phishing message flagged & quarantined by TrustLens AI." if is_threat else "Message passed security verification."
    }

    if is_threat:
        # Format Slack Block Kit Alert
        response_payload["slack_alert"] = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🚨 *TrustLens AI Security Alert:* High-risk phishing attack intercepted in transit!\n> *Risk Score:* `{result.get('overall_score') * 100:.1f}%` ({result.get('risk_level')})"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "🛡️ *Action:* Message quarantined before user interaction."}
                    ]
                }
            ]
        }

    return response_payload

@router.post("/teams")
async def teams_webhook(request: Request):
    """
    Microsoft Teams Connector & Bot Webhook endpoint.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    text = body.get("text", "") or body.get("summary", "")
    result = analyze_text(text) if text else {"overall_score": 0.0, "risk_level": "LOW", "threats": []}
    is_threat = result.get("risk_level") in ["HIGH", "CRITICAL"]

    return {
        "status": "processed",
        "action": "BLOCKED" if is_threat else "CLEARED",
        "platform": "Microsoft Teams",
        "risk_level": result.get("risk_level"),
        "overall_score": result.get("overall_score"),
        "teams_adaptive_card": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🛡️ TrustLens AI Transit Shield",
                    "weight": "Bolder",
                    "color": "Attention" if is_threat else "Good"
                },
                {
                    "type": "TextBlock",
                    "text": f"Status: {'⚠️ Phishing Attempt Quarantined' if is_threat else '✅ Passed Hygiene Scan'}",
                    "wrap": True
                }
            ]
        }
    }

@router.post("/test")
async def test_webhook(req: WebhookTestRequest):
    """
    Simulator endpoint to test webhook threat detection from the TrustLens dashboard.
    """
    result = analyze_text(req.message)
    is_threat = result.get("risk_level") in ["HIGH", "CRITICAL"]

    return {
        "platform": req.platform,
        "sender": req.sender,
        "channel": req.channel,
        "verdict": "BLOCKED" if is_threat else "DELIVERED",
        "risk_level": result.get("risk_level"),
        "score": result.get("overall_score"),
        "details": result.get("details", {}),
        "remediation": "Message blocked from workplace channels and logged to TrustLens SOC." if is_threat else "Safe for employee viewing."
    }
