"""
Utility functions for Streamlit app
"""

def get_risk_status(risk_level):
    """Convert risk level to display status"""
    if not risk_level:
        return "✅ SAFE"
    
    risk_str = str(risk_level).upper().strip()
    
    if "HIGH" in risk_str or "SUSPICIOUS" in risk_str:
        return "🔴 HIGH RISK"
    elif "MEDIUM" in risk_str or "MODERATE" in risk_str or "WARNING" in risk_str:
        return "🟡 MODERATE"
    elif "LOW" in risk_str or "SAFE" in risk_str:
        return "🟢 SAFE"
    else:
        return "✅ ORIGINAL"


def get_risk_color(risk_level):
    """Get color for risk level"""
    if not risk_level:
        return "green"
    
    risk_str = str(risk_level).upper().strip()
    
    if "HIGH" in risk_str or "SUSPICIOUS" in risk_str:
        return "red"
    elif "MEDIUM" in risk_str or "MODERATE" in risk_str or "WARNING" in risk_str:
        return "orange"
    else:
        return "green"


def get_confidence_percentage(confidence):
    """Format confidence as percentage"""
    try:
        conf = float(confidence) if confidence else 0
        return f"{conf:.1%}"
    except:
        return "N/A"
