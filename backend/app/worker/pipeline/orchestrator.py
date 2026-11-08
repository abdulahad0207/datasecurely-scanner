import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.errors import ScopeViolationError, VerificationRequiredError
from app.core.logging import logger
from app.db.repository import repo
from app.services.scope_guard import scope_guard
from app.worker.ai.report_writer import generate_executive_report_summary
from app.worker.ai.triage import triage_all_findings
from app.worker.monitoring.alerts import evaluate_and_dispatch_monitoring_alerts
from app.worker.monitoring.diff import compute_and_save_scan_diff
from app.worker.pipeline.stages.normalize import normalize_and_dedupe_findings
from app.worker.pipeline.stages.recon import run_recon_stage
from app.worker.pipeline.stages.scan import run_scan_stage
from app.worker.pipeline.stages.score import calculate_security_grade
from app.worker.reporting.render_pdf import generate_report_pdf


async def run_fake_scan_stage(hostname: str) -> List[Dict[str, Any]]:
    """
    Stub scanner stage for Phase 3.
    Returns realistic mock normalized findings.
    """
    await asyncio.sleep(0.5)
    return [
        {
            "template_id": "missing-csp-header",
            "title": "Missing Content-Security-Policy Header",
            "severity": "medium",
            "host": hostname,
        },
        {
            "template_id": "hsts-missing",
            "title": "HTTP Strict Transport Security (HSTS) Not Enforced",
            "severity": "low",
            "host": hostname,
        },
    ]


async def execute_scan_pipeline(
    scan_id: str,
    timeout_seconds: int = 1200,  # 20 minutes default hard timeout
    fast_mode: bool = False,      # For unit tests
) -> None:
    """
    Executes the end-to-end scan lifecycle:
    1. Scope Guard: ownership check, DNS resolution, SSRF blocklist check
    2. Recon: host status and discovery
    3. Scanning: safe vulnerability engine (stubbed for Phase 3)
    4. Scoring: grade calculation and completion
    """
    delay = 0.05 if fast_mode else 1.0

    scan = await repo.get_scan(scan_id)
    if not scan:
        logger.error(f"Scan ID {scan_id} not found in repository.")
        return

    domain = await repo.get_domain(scan.domain_id)
    if not domain:
        await repo.update_scan_progress(
            scan_id=scan_id,
            status="failed",
            progress=0,
            error="Associated domain record could not be found.",
        )
        return

    try:
        async with asyncio.timeout(timeout_seconds):
            # 1. SCOPE GUARD
            logger.info(f"Scan {scan_id}: Initiating Scope Guard checks for '{domain.hostname}'...")
            try:
                scope_guard.check_authorization(domain)
                pinned_ips = await scope_guard.resolve_and_guard(domain.hostname)
            except (VerificationRequiredError, ScopeViolationError) as e:
                logger.warning(f"Scan {scan_id} failed scope guard: {e.message}")
                await repo.update_scan_progress(
                    scan_id=scan_id,
                    status="failed",
                    progress=0,
                    error=e.message,
                )
                return

            # 2. RECON STAGE
            now = datetime.now(timezone.utc)
            await repo.update_scan_progress(
                scan_id=scan_id,
                status="recon",
                progress=25,
                stage_message=f"Inspecting live host and technology fingerprints ({', '.join(pinned_ips)})...",
                started_at=now,
            )
            if not fast_mode:
                await run_recon_stage(domain.hostname, profile=scan.profile)
            await asyncio.sleep(delay)

            # 3. SCANNING STAGE
            await repo.update_scan_progress(
                scan_id=scan_id,
                status="scanning",
                progress=60,
                stage_message="Executing non-destructive security and misconfiguration checks...",
            )
            if fast_mode:
                findings = await run_fake_scan_stage(domain.hostname)
            else:
                findings = await run_scan_stage(domain.hostname, profile=scan.profile)
            await asyncio.sleep(delay)

            # 4. SCORING & AI TRIAGE STAGE
            await repo.update_scan_progress(
                scan_id=scan_id,
                status="scoring",
                progress=80,
                stage_message="Normalizing findings, deduplicating, and calculating security grade...",
            )
            deduped_findings = normalize_and_dedupe_findings(raw_findings=findings, scan_id=scan_id)
            grade, numeric_score, breakdown = calculate_security_grade(deduped_findings)

            # AI Triage & Fix Guidance
            await repo.update_scan_progress(
                scan_id=scan_id,
                status="scoring",
                progress=90,
                stage_message="Generating AI remediation guidance and plain-language triage...",
            )
            triaged_findings = await triage_all_findings(deduped_findings, language="en")
            await repo.save_findings(scan_id=scan_id, findings=triaged_findings)
            await asyncio.sleep(delay)

            # 5. COMPLETION & REPORT PRE-RENDERING
            finished_at = datetime.now(timezone.utc)
            updated_scan = await repo.update_scan_progress(
                scan_id=scan_id,
                status="completed",
                progress=100,
                stage_message="Security scan completed successfully.",
                grade=grade,
                findings_count=len(deduped_findings),
                finished_at=finished_at,
            )

            # Pre-render executive report and cache
            try:
                summary_en = await generate_executive_report_summary(
                    hostname=domain.hostname,
                    grade=grade,
                    findings=triaged_findings,
                    language="en",
                )
                if updated_scan:
                    await generate_report_pdf(
                        scan=updated_scan,
                        findings=triaged_findings,
                        summary=summary_en,
                        language="en",
                    )
                    await repo.create_or_update_report(
                        scan_id=scan_id,
                        language="en",
                        pdf_url=f"/api/v1/reports/{scan_id}/download?lang=en",
                        html_url=f"/reports/{scan_id}?lang=en",
                        summary_json=summary_en.model_dump(),
                    )
            except Exception as report_err:
                logger.warning(f"Report pre-rendering warning: {report_err}")

            # Compute scan diff and dispatch monitoring change alerts
            try:
                if updated_scan:
                    diff_record = await compute_and_save_scan_diff(current_scan=updated_scan)
                    await evaluate_and_dispatch_monitoring_alerts(
                        scan=updated_scan,
                        diff=diff_record,
                        domain=domain,
                    )
            except Exception as diff_err:
                logger.warning(f"Scan diff computation warning: {diff_err}")

            logger.info(
                f"Scan {scan_id} for '{domain.hostname}' completed with grade {grade} ({numeric_score}/100, {len(deduped_findings)} findings)."
            )

    except TimeoutError:
        logger.error(f"Scan {scan_id} timed out after {timeout_seconds} seconds.")
        await repo.update_scan_progress(
            scan_id=scan_id,
            status="failed",
            progress=0,
            error=f"Scan exceeded hard execution timeout limit ({timeout_seconds}s).",
        )
    except Exception as e:
        logger.exception(f"Unhandled error during scan execution {scan_id}: {e}")
        await repo.update_scan_progress(
            scan_id=scan_id,
            status="failed",
            progress=0,
            error=f"Internal scan worker error: {str(e)}",
        )
