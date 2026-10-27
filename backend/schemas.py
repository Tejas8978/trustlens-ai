from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Union, Dict, Any
from datetime import datetime


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str
    value: str
    risk_contribution: float   # 0.0 - 1.0
    severity: str              # low | medium | high


class FrameTimelineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    frame_idx: int
    timestamp: float
    risk_score: float
    verdict: str


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scan_type: str
    filename: Optional[str] = None
    risk_score: float          # 0 - 100
    verdict: str               # SAFE | SUSPICIOUS | HIGH_RISK
    summary: str
    evidence: List[EvidenceItem]
    recommendations: List[str]
    ai_builder_prompt: str
    visual_artifact: Optional[str] = None
    frame_timeline: Optional[List[FrameTimelineItem]] = None
    user_email: Optional[str] = None

    @field_validator("evidence", mode="before")
    @classmethod
    def _coerce_evidence(cls, v):
        if not isinstance(v, list):
            return v
        cleaned = []
        for item in v:
            if hasattr(item, "model_dump"):
                cleaned.append(item.model_dump())
            elif isinstance(item, dict):
                cleaned.append(item)
            elif hasattr(item, "__dict__"):
                cleaned.append(item.__dict__)
            else:
                cleaned.append(item)
        return cleaned

    @field_validator("frame_timeline", mode="before")
    @classmethod
    def _coerce_frame_timeline(cls, v):
        if not isinstance(v, list):
            return v
        cleaned = []
        for item in v:
            if hasattr(item, "model_dump"):
                cleaned.append(item.model_dump())
            elif isinstance(item, dict):
                cleaned.append(item)
            elif hasattr(item, "__dict__"):
                cleaned.append(item.__dict__)
            else:
                cleaned.append(item)
        return cleaned


class ScanLogOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str                    # MongoDB ObjectId serialized as string
    scan_type: str
    filename: Optional[str] = None
    risk_score: float
    verdict: str
    summary: str
    created_at: datetime
    user_email: Optional[str] = None


class ScanDetailOut(ScanLogOut):
    evidence: List[EvidenceItem] = []
    recommendations: List[str] = []
    ai_builder_prompt: Optional[str] = None


class HistoryResponse(BaseModel):
    items: List[ScanLogOut]
    total: int
    skip: int
    limit: int
