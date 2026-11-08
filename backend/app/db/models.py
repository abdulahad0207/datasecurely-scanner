from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserModel:
    id: str
    email: str
    plan: str = "free"
    razorpay_customer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DomainModel:
    id: str
    user_id: str
    hostname: str
    verify_token: str
    status: str = "pending"  # pending, verified, expired
    is_monitored: bool = False
    last_monitored_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ScanModel:
    id: str
    domain_id: str
    user_id: str
    hostname: str
    profile: str = "free"  # free, full, monitor
    status: str = "queued"  # queued, recon, scanning, scoring, completed, failed, cancelled
    progress: int = 0
    stage_message: Optional[str] = "Queued for scan"
    grade: Optional[str] = None
    findings_count: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ReportModel:
    id: str
    scan_id: str
    language: str = "en"  # en, hi-Latn
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    summary_json: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class OrderModel:
    id: str
    user_id: str
    razorpay_order_id: str
    plan: str
    amount: int  # in paise
    currency: str = "INR"
    status: str = "created"  # created, attempted, paid, failed
    domain_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ScanDiffModel:
    id: str
    scan_id: str
    domain_id: str
    previous_scan_id: Optional[str] = None
    grade_change: str = "unchanged"  # improved, degraded, unchanged, first_scan
    new_findings_count: int = 0
    resolved_findings_count: int = 0
    persistent_findings_count: int = 0
    diff_json: Optional[dict] = None
    created_at: Optional[datetime] = None
