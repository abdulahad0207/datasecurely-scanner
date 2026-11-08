from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScanCreate(BaseModel):
    domain_id: str = Field(..., description="ID of the verified domain to scan")
    profile: str = Field(
        default="free",
        description="Scan profile: 'free' or 'full'",
        examples=["free", "full"],
    )


class ScanResponse(BaseModel):
    id: str
    domain_id: str
    user_id: str
    hostname: str
    profile: str
    status: str
    progress: int
    stage_message: Optional[str] = None
    grade: Optional[str] = None
    findings_count: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int
