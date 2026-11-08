from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.core.errors import VerificationRequiredError
from app.core.logging import logger
from app.db.repository import repo
from app.schemas.finding import FindingListResponse
from app.schemas.scan import ScanCreate, ScanListResponse, ScanResponse
from app.schemas.user import AuthUser
from app.services.queue import queue
from app.services.scope_guard import scope_guard

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


def format_scan_response(scan) -> ScanResponse:
    return ScanResponse(
        id=scan.id,
        domain_id=scan.domain_id,
        user_id=scan.user_id,
        hostname=scan.hostname,
        profile=scan.profile,
        status=scan.status,
        progress=scan.progress,
        stage_message=scan.stage_message,
        grade=scan.grade,
        findings_count=scan.findings_count,
        started_at=scan.started_at,
        finished_at=scan.finished_at,
        error=scan.error,
        created_at=scan.created_at,
    )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    payload: ScanCreate,
    current_user: AuthUser = Depends(get_current_user),
) -> ScanResponse:
    """
    Enqueues an authorized security scan for a verified domain.
    Rejects unverified or expired domains with 403 Forbidden.
    """
    domain = await repo.get_domain(domain_id=payload.domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found under your account",
        )

    # Authorization Gate
    try:
        scope_guard.check_authorization(domain)
    except VerificationRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )

    # Quota Enforcement Gate
    allowed, quota_reason, wait_seconds = await repo.check_scan_quota(
        user_id=current_user.id,
        domain_id=domain.id,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=quota_reason,
            headers={"Retry-After": str(wait_seconds or 3600)},
        )

    # Create scan record
    scan = await repo.create_scan(
        domain_id=domain.id,
        user_id=current_user.id,
        hostname=domain.hostname,
        profile=payload.profile,
    )

    # Enqueue job to background worker
    await queue.enqueue_scan(scan_id=scan.id)

    logger.info(f"User {current_user.id} queued {payload.profile} scan {scan.id} for {domain.hostname}")
    return format_scan_response(scan)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan_status(
    scan_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> ScanResponse:
    """Retrieves live status, progress percentage, and results of a scan."""
    scan = await repo.get_scan(scan_id=scan_id, user_id=current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    return format_scan_response(scan)


@router.get("/{scan_id}/findings", response_model=FindingListResponse)
async def get_scan_findings(
    scan_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> FindingListResponse:
    """Retrieves all normalized, deduplicated security findings for a scan."""
    scan = await repo.get_scan(scan_id=scan_id, user_id=current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    findings = await repo.list_findings_by_scan(scan_id=scan_id)
    return FindingListResponse(findings=findings, total=len(findings))


@router.get("/domain/{domain_id}", response_model=ScanListResponse)
async def list_domain_scans(
    domain_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> ScanListResponse:
    """Lists history of scans performed for a domain."""
    domain = await repo.get_domain(domain_id=domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )

    scans = await repo.list_scans_by_domain(domain_id=domain_id, user_id=current_user.id)
    return ScanListResponse(
        scans=[format_scan_response(s) for s in scans],
        total=len(scans),
    )
