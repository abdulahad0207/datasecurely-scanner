from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import logger
from app.db.repository import repo
from app.schemas.finding import ScanAISummary
from app.schemas.report import EmailReportRequest, EmailReportResponse, ReportResponse
from app.schemas.user import AuthUser
from app.worker.ai.report_writer import generate_executive_report_summary
from app.worker.notify.email import email_notifier
from app.worker.reporting.render_pdf import generate_report_pdf, scan_id_clean

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/{scan_id}", response_model=ReportResponse)
async def get_report(
    scan_id: str,
    lang: str = Query("en", pattern="^(en|hi-Latn)$"),
    current_user: AuthUser = Depends(get_current_user),
) -> ReportResponse:
    """
    Retrieves the generated report for a completed scan, generating
    summary and PDF if not yet cached.
    """
    scan = await repo.get_scan(scan_id=scan_id, user_id=current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found under your account",
        )

    if scan.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan has status '{scan.status}' and has not completed yet.",
        )

    report = await repo.get_report_by_scan_and_language(scan_id=scan_id, language=lang)
    findings = await repo.list_findings_by_scan(scan_id)

    if not report or not report.summary_json:
        # Check if an English summary already exists to guarantee 100% semantic alignment
        base_en_summary = None
        if lang != "en":
            en_report = await repo.get_report_by_scan_and_language(scan_id=scan_id, language="en")
            if en_report and en_report.summary_json:
                base_en_summary = ScanAISummary(**en_report.summary_json)

        # Generate summary using Gemini
        ai_summary = await generate_executive_report_summary(
            hostname=scan.hostname,
            grade=scan.grade or "A",
            findings=findings,
            language=lang,
            base_summary=base_en_summary,
        )
        # Generate PDF and HTML
        pdf_path = await generate_report_pdf(
            scan=scan,
            findings=findings,
            summary=ai_summary,
            language=lang,
        )

        pdf_url = f"/api/v1/reports/{scan_id}/download?lang={lang}"
        html_url = f"/reports/{scan_id}?lang={lang}"

        report = await repo.create_or_update_report(
            scan_id=scan_id,
            language=lang,
            pdf_url=pdf_url,
            html_url=html_url,
            summary_json=ai_summary.model_dump(),
        )

    return ReportResponse(
        id=report.id,
        scan_id=scan.id,
        hostname=scan.hostname,
        grade=scan.grade,
        language=lang,
        pdf_download_url=f"/api/v1/reports/{scan_id}/download?lang={lang}",
        summary=report.summary_json,
        findings_count=scan.findings_count,
        created_at=report.created_at,
    )


@router.get("/{scan_id}/download")
async def download_report_pdf(
    scan_id: str,
    lang: str = Query("en", pattern="^(en|hi-Latn)$"),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Streams the PDF report download for the specified scan.
    """
    scan = await repo.get_scan(scan_id=scan_id, user_id=current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found under your account",
        )

    if scan.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan has status '{scan.status}' and has not completed yet.",
        )

    # Determine storage directory and path
    storage_dir = Path(settings.REPORT_STORAGE_PATH)
    if not storage_dir.is_absolute():
        storage_dir = settings.BASE_DIR / storage_dir

    pdf_path = storage_dir / f"{scan_id_clean(scan_id)}_{lang}.pdf"

    if not pdf_path.exists():
        # Generate on the fly
        findings = await repo.list_findings_by_scan(scan_id)
        report = await repo.get_report_by_scan_and_language(scan_id=scan_id, language=lang)
        summary_obj = None
        if report and report.summary_json:
            summary_obj = ScanAISummary(**report.summary_json)
        else:
            base_en_summary = None
            if lang != "en":
                en_rep = await repo.get_report_by_scan_and_language(scan_id=scan_id, language="en")
                if en_rep and en_rep.summary_json:
                    base_en_summary = ScanAISummary(**en_rep.summary_json)

            summary_obj = await generate_executive_report_summary(
                hostname=scan.hostname,
                grade=scan.grade or "A",
                findings=findings,
                language=lang,
                base_summary=base_en_summary,
            )

        pdf_path = await generate_report_pdf(
            scan=scan,
            findings=findings,
            summary=summary_obj,
            language=lang,
            output_dir=storage_dir,
        )

    filename = f"datasecurely-{scan.hostname}-security-report-{lang}.pdf"
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )


@router.post("/{scan_id}/email", response_model=EmailReportResponse)
async def email_report(
    scan_id: str,
    payload: EmailReportRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> EmailReportResponse:
    """
    Dispatches the scan report via email with PDF attachment.
    """
    scan = await repo.get_scan(scan_id=scan_id, user_id=current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found under your account",
        )

    if scan.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan has status '{scan.status}' and has not completed yet.",
        )

    to_email = payload.email or current_user.email
    if not to_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipient email address provided.",
        )

    # Resolve PDF
    storage_dir = Path(settings.REPORT_STORAGE_PATH)
    if not storage_dir.is_absolute():
        storage_dir = settings.BASE_DIR / storage_dir

    pdf_path = storage_dir / f"{scan_id_clean(scan_id)}_{payload.language}.pdf"
    findings = await repo.list_findings_by_scan(scan_id)
    report = await repo.get_report_by_scan_and_language(scan_id=scan_id, language=payload.language)

    summary_obj = None
    if report and report.summary_json:
        summary_obj = ScanAISummary(**report.summary_json)
    else:
        summary_obj = await generate_executive_report_summary(
            hostname=scan.hostname,
            grade=scan.grade or "A",
            findings=findings,
            language=payload.language,
        )

    if not pdf_path.exists():
        pdf_path = await generate_report_pdf(
            scan=scan,
            findings=findings,
            summary=summary_obj,
            language=payload.language,
            output_dir=storage_dir,
        )

    summary_text = summary_obj.executive_summary if summary_obj else None

    delivery = await email_notifier.send_report_email(
        to_email=to_email,
        hostname=scan.hostname,
        grade=scan.grade or "A",
        scan_id=scan.id,
        pdf_path=pdf_path,
        language=payload.language,
        summary_text=summary_text,
    )

    if delivery.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email delivery failed: {delivery.get('error')}",
        )

    return EmailReportResponse(
        success=True,
        message=f"Report successfully delivered to {to_email}",
        recipient=to_email,
        provider=delivery.get("provider", "mock"),
    )
