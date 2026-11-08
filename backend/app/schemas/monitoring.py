from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ToggleMonitoringRequest(BaseModel):
    domain_id: str = Field(..., description="Target domain ID to toggle monitoring for")
    enabled: bool = Field(..., description="True to activate weekly monitoring, False to pause")


class ToggleMonitoringResponse(BaseModel):
    domain_id: str
    is_monitored: bool
    message: str


class ScanDiffResponse(BaseModel):
    id: str
    scan_id: str
    domain_id: str
    previous_scan_id: Optional[str] = None
    grade_change: str
    new_findings_count: int
    resolved_findings_count: int
    persistent_findings_count: int
    diff_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RunCycleResponse(BaseModel):
    status: str
    domains_evaluated: int
    scans_enqueued: int
    items: List[Dict[str, str]]
