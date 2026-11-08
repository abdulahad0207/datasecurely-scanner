from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

SeverityLevel = Literal["info", "low", "medium", "high", "critical"]


class FindingAITriage(BaseModel):
    plain_summary: str = Field(..., description="Plain-language explanation for non-technical owners")
    business_impact: str = Field(..., description="Real-world financial or operational impact")
    fix_steps: List[str] = Field(..., description="Step-by-step remediation commands or instructions")
    priority: int = Field(..., ge=1, le=5, description="Priority ranking from 1 (immediate) to 5")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score to filter false positives")
    effort: Literal["low", "medium", "high"] = Field(..., description="Effort required to fix")

    model_config = ConfigDict(from_attributes=True)


class ScanAISummary(BaseModel):
    executive_summary: str = Field(..., description="3-5 sentence plain English/Hinglish summary of security posture")
    top_actions: List[str] = Field(..., description="Top 3 immediate remediation actions")
    grade_rationale: str = Field(..., description="Rationale explaining the assigned grade")
    language: str = Field(default="en", description="Output language ('en' or 'hi-Latn')")

    model_config = ConfigDict(from_attributes=True)


class Finding(BaseModel):
    id: Optional[str] = None
    scan_id: Optional[str] = None
    source_tool: str = Field(..., description="Tool that detected this issue")
    template_id: str = Field(..., description="Identifier for vulnerability or check rule")
    title: str = Field(..., description="Descriptive title of finding")
    severity: SeverityLevel = Field(..., description="Mapped severity level")
    host: str = Field(..., description="Host or endpoint where finding was observed")
    evidence: Optional[str] = Field(None, max_length=2048, description="Truncated proof or response snippet")
    raw_ref: Optional[str] = None
    fingerprint: str = Field(..., description="SHA-256 deduplication fingerprint")
    ai_json: Optional[FindingAITriage] = None

    model_config = ConfigDict(from_attributes=True)


class FindingListResponse(BaseModel):
    findings: List[Finding]
    total: int
