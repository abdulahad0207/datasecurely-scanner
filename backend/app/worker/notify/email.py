from pathlib import Path
from typing import Any, Dict, List, Optional
import resend
from app.core.config import settings
from app.core.logging import logger


class EmailNotifier:
    """
    Handles sending notification and assessment report emails using Resend,
    with automatic mock fallback for local tests and development.
    """

    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    async def send_report_email(
        self,
        to_email: str,
        hostname: str,
        grade: str,
        scan_id: str,
        pdf_path: Optional[Path] = None,
        language: str = "en",
        summary_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends the scan report to the user via Resend (or mock if not configured).
        """
        if language == "hi-Latn":
            subject = f"[datasecurely] Suraksha Report: {hostname} - Grade {grade}"
            greeting = f"Namaste! Aapke domain <strong>{hostname}</strong> ka security scan poora ho gaya hai."
            grade_msg = f"Overall Security Grade: <strong>{grade}</strong>."
            view_cta = "Poori Report Dekhein"
        else:
            subject = f"[datasecurely] Security Scan Report: {hostname} - Grade {grade}"
            greeting = f"Hello! The security assessment for <strong>{hostname}</strong> is complete."
            grade_msg = f"Overall Security Grade: <strong>{grade}</strong>."
            view_cta = "View Full Report"

        report_url = f"{settings.FRONTEND_URL}/reports/{scan_id}?lang={language}"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
          <div style="background-color: #2563eb; color: #ffffff; padding: 12px 16px; border-radius: 6px; font-size: 18px; font-weight: bold;">
            🛡️ datasecurely Scanner
          </div>
          <div style="padding: 20px 0;">
            <p style="font-size: 15px; color: #1e293b;">{greeting}</p>
            <p style="font-size: 18px; color: #0f172a; margin: 15px 0;">{grade_msg}</p>
            {f'<blockquote style="border-left: 4px solid #3b82f6; padding-left: 12px; color: #475569; font-style: italic; margin: 15px 0;">{summary_text}</blockquote>' if summary_text else ''}
            <div style="margin: 25px 0;">
              <a href="{report_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                {view_cta} &rarr;
              </a>
            </div>
            <p style="font-size: 12px; color: #64748b; margin-top: 20px;">
              Attached is the PDF version of your executive summary and remediation roadmap.
            </p>
          </div>
          <div style="border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: 11px; color: #94a3b8; text-align: center;">
            datasecurely Scanner &bull; One-click website security for Indian SMBs
          </div>
        </div>
        """

        is_mock = (
            not settings.RESEND_API_KEY
            or settings.RESEND_API_KEY == "mock"
            or "mock" in settings.RESEND_API_KEY.lower()
        )

        record = {
            "to": to_email,
            "subject": subject,
            "scan_id": scan_id,
            "hostname": hostname,
            "grade": grade,
            "language": language,
            "has_pdf": bool(pdf_path and Path(pdf_path).exists()),
            "report_url": report_url,
        }

        if is_mock:
            logger.info(f"[MOCK EMAIL] Sent report for '{hostname}' to {to_email} (Grade: {grade})")
            self.sent_emails.append(record)
            return {
                "status": "sent",
                "provider": "mock",
                "id": f"mock-{scan_id[:8]}",
                "to": to_email,
            }

        try:
            resend.api_key = settings.RESEND_API_KEY
            params: Dict[str, Any] = {
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            }

            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, "rb") as f:
                    content_bytes = list(f.read())
                params["attachments"] = [
                    {
                        "filename": f"datasecurely-{hostname}-report.pdf",
                        "content": content_bytes,
                    }
                ]

            response = resend.Emails.send(params)
            logger.info(f"Report email sent to {to_email} via Resend. ID: {response.get('id')}")
            self.sent_emails.append(record)
            return {
                "status": "sent",
                "provider": "resend",
                "id": response.get("id"),
                "to": to_email,
            }
        except Exception as e:
            logger.error(f"Failed to send email via Resend to {to_email}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "to": to_email,
            }


email_notifier = EmailNotifier()
