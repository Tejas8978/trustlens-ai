from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class EvidenceItem(BaseModel):
    label: str
    value: str
    risk_contribution: float   # 0.0 - 1.0
    severity: str              # low | medium | high


class AnalysisResult(BaseModel):
    scan_type: str
    filename: Optional[str] = None
    risk_score: float          # 0 - 100
    verdict: str               # SAFE | SUSPICIOUS | HIGH_RISK
    summary: str
    evidence: List[EvidenceItem]
    recommendations: List[str]
    ai_builder_prompt: str


class ScanLogOut(BaseModel):
    id: int
    scan_type: str
    filename: Optional[str]
    risk_score: float
    verdict: str
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
