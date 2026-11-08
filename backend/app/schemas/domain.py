from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DomainCreate(BaseModel):
    hostname: str = Field(
        ...,
        description="Target domain or hostname (e.g. example.com or app.example.com)",
        examples=["example.com", "subdomain.example.in"],
    )


class LatestScanSummary(BaseModel):
    id: str
    status: str
    grade: Optional[str] = None
    findings_count: int = 0
    created_at: datetime
    finished_at: Optional[datetime] = None


class DomainResponse(BaseModel):
    id: str
    user_id: str
    hostname: str
    verify_token: str
    status: str  # pending, verified, expired
    verified_at: Optional[datetime] = None
    created_at: datetime
    dns_record_name: str
    dns_record_value: str
    well_known_url: str
    latest_scan: Optional[LatestScanSummary] = None

    model_config = ConfigDict(from_attributes=True)


class VerificationCheckDetails(BaseModel):
    dns: Optional[str] = None
    well_known: Optional[str] = None


class VerificationCheckResponse(BaseModel):
    verified: bool
    status: str
    method: Optional[str] = None
    message: str
    verified_at: Optional[datetime] = None
    details: VerificationCheckDetails


class InfrastructureTelemetry(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    tls_version: Optional[str] = None
    tls_cipher: Optional[str] = None
    cert_issuer: Optional[str] = None
    cert_expires: Optional[str] = None
    cert_days_remaining: Optional[int] = None
    server_banner: Optional[str] = None
    hsts_header: Optional[str] = None
    csp_header: Optional[str] = None


class DomainListResponse(BaseModel):
    domains: List[DomainResponse]
    total: int

