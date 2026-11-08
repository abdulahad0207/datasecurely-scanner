from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReportResponse(BaseModel):
    id: str
    scan_id: str
    hostname: str
    grade: Optional[str] = None
    language: str = "en"
    pdf_download_url: str
    summary: Optional[Dict[str, Any]] = None
    findings_count: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmailReportRequest(BaseModel):
    email: Optional[str] = Field(None, description="Recipient email address. Defaults to account email.")
    language: str = Field("en", description="Report language: 'en' or 'hi-Latn'")


class EmailReportResponse(BaseModel):
    success: bool
    message: str
    recipient: str
    provider: str
