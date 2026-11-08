from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.core.logging import logger
from app.db.repository import repo
from app.schemas.monitoring import (
    RunCycleResponse,
    ScanDiffResponse,
    ToggleMonitoringRequest,
    ToggleMonitoringResponse,
)
from app.schemas.user import AuthUser
from app.worker.monitoring.diff import compute_and_save_scan_diff
from app.worker.monitoring.scheduler import run_monitoring_cycle

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.post("/toggle", response_model=ToggleMonitoringResponse)
async def toggle_monitoring(
    payload: ToggleMonitoringRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> ToggleMonitoringResponse:
    """
    Enables or disables continuous weekly automated scanning for a verified domain.
    """
    domain = await repo.get_domain(domain_id=payload.domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found under your account",
        )

    if domain.status != "verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Domain ownership must be verified before enabling automated monitoring.",
        )

    updated = await repo.update_domain_monitoring(
        domain_id=domain.id,
        is_monitored=payload.enabled,
        user_id=current_user.id,
    )

    action_text = "activated" if payload.enabled else "paused"
    logger.info(f"User {current_user.id} {action_text} continuous monitoring for {domain.hostname}")

    return ToggleMonitoringResponse(
        domain_id=domain.id,
        is_monitored=payload.enabled,
        message=f"Continuous weekly security monitoring successfully {action_text}.",
    )


@router.get("/diff/{scan_id}", response_model=ScanDiffResponse)
async def get_scan_diff(
    scan_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> ScanDiffResponse:
    """
    Returns vulnerability delta (new, resolved, and persistent findings)
    compared against the domain's previous scan.
    """
    scan = await repo.get_scan(scan_id=scan_id, user_id=current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found under your account",
        )

    diff = await repo.get_scan_diff(scan_id=scan_id)
    if not diff and scan.status == "completed":
        diff = await compute_and_save_scan_diff(current_scan=scan)

    if not diff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No differential comparison available for this scan yet.",
        )

    return ScanDiffResponse(
        id=diff.id,
        scan_id=diff.scan_id,
        domain_id=diff.domain_id,
        previous_scan_id=diff.previous_scan_id,
        grade_change=diff.grade_change,
        new_findings_count=diff.new_findings_count,
        resolved_findings_count=diff.resolved_findings_count,
        persistent_findings_count=diff.persistent_findings_count,
        diff_json=diff.diff_json,
        created_at=diff.created_at,
    )


@router.post("/run-cycle", response_model=RunCycleResponse)
async def trigger_monitoring_cycle(
    current_user: AuthUser = Depends(get_current_user),
) -> RunCycleResponse:
    """
    Manually triggers an immediate evaluation of scheduled monitoring cycles.
    """
    result = await run_monitoring_cycle(days_due=7)
    return RunCycleResponse(
        status=result["status"],
        domains_evaluated=result["domains_evaluated"],
        scans_enqueued=result["scans_enqueued"],
        items=result["items"],
    )
