from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.db.models import DomainModel, ScanDiffModel, ScanModel
from app.db.repository import repo
from app.worker.notify.email import email_notifier


async def evaluate_and_dispatch_monitoring_alerts(
    scan: ScanModel,
    diff: ScanDiffModel,
    domain: Optional[DomainModel] = None,
) -> Dict[str, Any]:
    """
    Evaluates scan diff changes and dispatches immediate security alert emails
    if new critical/high vulnerabilities were introduced or posture degraded.
    """
    if diff.grade_change == "first_scan":
        return {"alert_dispatched": False, "reason": "First scan baseline; no delta alert needed."}

    user = await repo.get_user(scan.user_id)
    to_email = user.email if user else f"{scan.user_id}@example.com"

    diff_data = diff.diff_json or {}
    new_findings: List[Dict[str, Any]] = diff_data.get("new_findings", [])
    resolved_findings: List[Dict[str, Any]] = diff_data.get("resolved_findings", [])

    has_urgent_new_findings = any(
        f.get("severity", "").lower() in ("critical", "high") for f in new_findings
    )
    is_degraded = diff.grade_change == "degraded"

    if has_urgent_new_findings or is_degraded:
        subject = f"[datasecurely ALERT] New Security Vulnerabilities on {scan.hostname}"
        summary_text = (
            f"Automated monitoring scan detected {len(new_findings)} new issue(s). "
            f"Security Grade moved to {scan.grade or 'N/A'} ({diff.grade_change}). "
            f"Immediate review recommended."
        )

        logger.warning(f"DISPATCHING ALERT: New urgent findings detected on monitored domain {scan.hostname}")
        res = await email_notifier.send_report_email(
            to_email=to_email,
            hostname=scan.hostname,
            grade=scan.grade or "A",
            scan_id=scan.id,
            language="en",
            summary_text=summary_text,
        )
        return {
            "alert_dispatched": True,
            "type": "degraded_or_critical_alert",
            "recipient": to_email,
            "provider_result": res,
        }

    if resolved_findings and not new_findings:
        summary_text = f"Great news! {len(resolved_findings)} security issue(s) have been verified as resolved on {scan.hostname}."
        logger.info(f"DISPATCHING RESOLUTION NOTICE: {len(resolved_findings)} issues fixed on {scan.hostname}")
        res = await email_notifier.send_report_email(
            to_email=to_email,
            hostname=scan.hostname,
            grade=scan.grade or "A",
            scan_id=scan.id,
            language="en",
            summary_text=summary_text,
        )
        return {
            "alert_dispatched": True,
            "type": "resolution_notice",
            "recipient": to_email,
            "provider_result": res,
        }

    return {"alert_dispatched": False, "reason": "No significant security posture delta."}
