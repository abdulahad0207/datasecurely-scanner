from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from app.db.models import ScanModel
from app.db.repository import repo
from app.schemas.finding import Finding, FindingAITriage, ScanAISummary
from app.worker.notify.email import email_notifier
from app.worker.reporting.render_pdf import generate_report_pdf, render_html_report

AUTH_HEADERS = {"Authorization": "Bearer test-token-reportuser-report@example.com"}
USER_ID = "reportuser"


@pytest.fixture
def sample_scan():
    return ScanModel(
        id="test-scan-rep-1",
        domain_id="test-dom-rep-1",
        user_id=USER_ID,
        hostname="kirana-store.in",
        profile="free",
        status="completed",
        progress=100,
        stage_message="Security scan completed successfully.",
        grade="B",
        findings_count=2,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_findings():
    return [
        Finding(
            source_tool="custom-headers",
            template_id="missing-csp",
            title="Missing Content Security Policy (CSP)",
            severity="medium",
            host="kirana-store.in",
            evidence="Content-Security-Policy header is absent",
            fingerprint="fp1",
            ai_json=FindingAITriage(
                plain_summary="Website mein Content Security Policy nahi hai, jisse malicious scripts chal sakti hain.",
                business_impact="Attackers can inject malicious scripts, potentially compromising checkout forms.",
                fix_steps=["Add Content-Security-Policy header to web server", "Test with report-only mode first"],
                priority=2,
                confidence=0.95,
                effort="medium",
            ),
        ),
        Finding(
            source_tool="custom-tls",
            template_id="ssl-expiring-soon",
            title="SSL Certificate Expiring in 14 Days",
            severity="high",
            host="kirana-store.in",
            evidence="Valid until 22-Nov-2026",
            fingerprint="fp2",
            ai_json=FindingAITriage(
                plain_summary="Aapka SSL certificate 14 din mein expire ho raha hai.",
                business_impact="Browsers will show untrusted warnings, causing immediate customer drop-off.",
                fix_steps=["Renew certificate via Certbot or host control panel"],
                priority=1,
                confidence=0.99,
                effort="low",
            ),
        ),
    ]


@pytest.fixture
def sample_summary():
    return ScanAISummary(
        executive_summary="kirana-store.in shows a moderate security posture with an expiring SSL cert and missing CSP header.",
        top_actions=[
            "Renew SSL certificate immediately to prevent browser security blocks.",
            "Deploy Content-Security-Policy to protect your customer data.",
        ],
        grade_rationale="Grade B assigned due to 1 High severity item and 1 Medium severity item.",
        language="en",
    )


def test_render_html_report_english(sample_scan, sample_findings, sample_summary):
    html = render_html_report(
        scan=sample_scan,
        findings=sample_findings,
        summary=sample_summary,
        language="en",
    )
    assert "kirana-store.in" in html
    assert "test-scan-rep-1" in html
    assert "grade-B" in html
    assert "80/100" in html
    assert "Missing Content Security Policy" in html
    assert "SSL Certificate Expiring" in html
    assert "Executive Summary" in html
    assert "Immediate Priority Actions" in html


def test_render_html_report_hinglish(sample_scan, sample_findings, sample_summary):
    hinglish_summary = ScanAISummary(
        executive_summary="kirana-store.in ki security theek hai lekin SSL certificate turant renew karna zaroori hai.",
        top_actions=[
            "SSL certificate ko turant renew karein taaki customers ko security warning na dikhe.",
            "CSP header lagayein taaki checkout page surakshit rahe.",
        ],
        grade_rationale="Grade B mila hai kyunki 1 High issue aur 1 Medium issue mila.",
        language="hi-Latn",
    )
    html = render_html_report(
        scan=sample_scan,
        findings=sample_findings,
        summary=hinglish_summary,
        language="hi-Latn",
    )
    assert "Executive Summary (Sankshep)" in html
    assert "Turant Karne Wale Kaam" in html
    assert "Samasya Kya Hai?" in html
    assert "Business Par Asar" in html
    assert "Ise Kaise Theek Karein?" in html


@pytest.mark.asyncio
async def test_generate_report_pdf(sample_scan, sample_findings, sample_summary, tmp_path):
    pdf_path = await generate_report_pdf(
        scan=sample_scan,
        findings=sample_findings,
        summary=sample_summary,
        language="en",
        output_dir=tmp_path,
    )
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_email_notifier_mock(tmp_path):
    test_pdf = tmp_path / "mock-report.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 test")

    res = await email_notifier.send_report_email(
        to_email="testowner@smb.in",
        hostname="kirana-store.in",
        grade="B",
        scan_id="test-scan-123",
        pdf_path=test_pdf,
        language="en",
        summary_text="Quick summary test",
    )
    assert res["status"] == "sent"
    assert res["provider"] == "mock"
    assert res["to"] == "testowner@smb.in"
    assert len(email_notifier.sent_emails) >= 1
    last_sent = email_notifier.sent_emails[-1]
    assert last_sent["hostname"] == "kirana-store.in"
    assert last_sent["has_pdf"] is True


@pytest.mark.asyncio
async def test_api_get_report_and_download(async_client: AsyncClient, sample_scan, sample_findings, sample_summary):
    # Setup scan and domain in repo
    domain = await repo.create_domain(
        user_id=USER_ID,
        hostname="kirana-store.in",
        verify_token="test-tok-rep",
    )
    sample_scan.domain_id = domain.id
    repo._in_memory_scans[sample_scan.id] = sample_scan
    repo._in_memory_findings[sample_scan.id] = sample_findings

    # Pre-create report
    await repo.create_or_update_report(
        scan_id=sample_scan.id,
        language="en",
        pdf_url=f"/api/v1/reports/{sample_scan.id}/download?lang=en",
        html_url=f"/reports/{sample_scan.id}?lang=en",
        summary_json=sample_summary.model_dump(),
    )

    # 1. GET /api/v1/reports/{scan_id}
    res = await async_client.get(f"/api/v1/reports/{sample_scan.id}", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["scan_id"] == sample_scan.id
    assert data["hostname"] == "kirana-store.in"
    assert data["grade"] == "B"
    assert data["language"] == "en"
    assert "pdf_download_url" in data

    # 2. GET /api/v1/reports/{scan_id}/download
    dl_res = await async_client.get(f"/api/v1/reports/{sample_scan.id}/download", headers=AUTH_HEADERS)
    assert dl_res.status_code == 200
    assert "application/pdf" in dl_res.headers.get("content-type", "")
    assert dl_res.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_api_get_report_scan_not_completed(async_client: AsyncClient):
    domain = await repo.create_domain(
        user_id=USER_ID,
        hostname="in-progress.in",
        verify_token="test-tok-prog",
    )
    scan = await repo.create_scan(
        domain_id=domain.id,
        user_id=USER_ID,
        hostname=domain.hostname,
        profile="free",
    )
    # Scan status is queued / not completed
    res = await async_client.get(f"/api/v1/reports/{scan.id}", headers=AUTH_HEADERS)
    assert res.status_code == 400
    assert "has not completed yet" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_email_report(async_client: AsyncClient, sample_scan, sample_findings, sample_summary):
    domain = await repo.create_domain(
        user_id=USER_ID,
        hostname="email-test.in",
        verify_token="test-tok-em",
    )
    sample_scan.id = "email-test-scan-id"
    sample_scan.domain_id = domain.id
    sample_scan.hostname = domain.hostname
    repo._in_memory_scans[sample_scan.id] = sample_scan
    repo._in_memory_findings[sample_scan.id] = sample_findings

    payload = {
        "email": "notify-owner@retailer.in",
        "language": "en",
    }
    res = await async_client.post(
        f"/api/v1/reports/{sample_scan.id}/email",
        json=payload,
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["recipient"] == "notify-owner@retailer.in"
    assert "provider" in data


@pytest.mark.asyncio
async def test_api_reports_unauthorized(async_client: AsyncClient):
    res = await async_client.get("/api/v1/reports/some-scan-id")
    assert res.status_code == 401
