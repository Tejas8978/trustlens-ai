from pydantic import BaseModel, ConfigDict
from typing import Optional, List
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
    model_config = ConfigDict(populate_by_name=True)

    id: str                    # MongoDB ObjectId serialized as string
    scan_type: str
    filename: Optional[str] = None
    risk_score: float
    verdict: str
    summary: str
    created_at: datetime
