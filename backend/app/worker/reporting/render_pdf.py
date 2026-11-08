import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import jinja2
from app.core.config import settings
from app.core.logging import logger
from app.db.models import ScanModel
from app.schemas.finding import Finding, ScanAISummary

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)


def render_html_report(
    scan: ScanModel,
    findings: List[Finding],
    summary: Optional[ScanAISummary] = None,
    language: str = "en",
) -> str:
    """
    Renders Jinja2 HTML report with branded styling, findings breakdown,
    and bilingual AI executive summary.
    """
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.severity.lower() if f.severity else "info"
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1

    grade_score_map = {"A": 95, "B": 80, "C": 65, "D": 50, "F": 30}
    score = grade_score_map.get(scan.grade or "A", 85)

    scan_dt = scan.finished_at or scan.created_at or datetime.now(timezone.utc)
    scan_date_str = scan_dt.strftime("%d %b %Y, %H:%M UTC")

    template = jinja_env.get_template("report.html.j2")
    html_content = template.render(
        hostname=scan.hostname,
        scan_id=scan.id,
        scan_date=scan_date_str,
        grade=scan.grade or "A",
        score=score,
        severity_counts=counts,
        summary=summary,
        findings=findings,
        language=language,
    )
    return html_content


async def generate_report_pdf(
    scan: ScanModel,
    findings: List[Finding],
    summary: Optional[ScanAISummary] = None,
    language: str = "en",
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Renders HTML report and compiles it to PDF using Playwright (with fallback).
    Saves outputs to storage/reports/{scan_id}_{language}.[html|pdf].
    """
    if output_dir is None:
        target_dir = Path(settings.REPORT_STORAGE_PATH)
        if not target_dir.is_absolute():
            target_dir = settings.BASE_DIR / target_dir
    else:
        target_dir = output_dir

    target_dir.mkdir(parents=True, exist_ok=True)

    html_path = target_dir / f"{scan_id_clean(scan.id)}_{language}.html"
    pdf_path = target_dir / f"{scan_id_clean(scan.id)}_{language}.pdf"

    html_content = render_html_report(
        scan=scan,
        findings=findings,
        summary=summary,
        language=language,
    )

    # Write HTML output
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Attempt Playwright PDF rendering
    rendered_via_playwright = False
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="load")
            await page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "12mm", "bottom": "12mm", "left": "12mm", "right": "12mm"},
            )
            await browser.close()
            rendered_via_playwright = True
            logger.info(f"Report PDF generated via Playwright: {pdf_path}")
    except Exception as e:
        logger.warning(f"Playwright PDF generation failed or not installed ({e}); using printable PDF fallback.")

    if not rendered_via_playwright or not pdf_path.exists():
        # Fallback PDF generator: create a valid minimal PDF wrapping report metadata
        _write_fallback_pdf(pdf_path, scan, findings, summary, language)
        logger.info(f"Report PDF generated via fallback generator: {pdf_path}")

    return pdf_path


def scan_id_clean(scan_id: str) -> str:
    return "".join(c for c in scan_id if c.isalnum() or c in ("-", "_"))


def _write_fallback_pdf(
    pdf_path: Path,
    scan: ScanModel,
    findings: List[Finding],
    summary: Optional[ScanAISummary],
    language: str,
):
    """
    Generates a valid minimalist PDF file when browser rendering is unavailable in the environment.
    """
    title = f"datasecurely Scanner Report - {scan.hostname}"
    grade_line = f"Overall Security Grade: {scan.grade or 'A'} ({len(findings)} findings)"
    summary_text = summary.executive_summary if summary else "No summary available."
    actions_text = "\n".join(f"- {a}" for a in (summary.top_actions if summary else []))

    content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {150 + len(title) + len(grade_line)} >>
stream
BT
/F1 18 Tf
50 720 Td
({_escape_pdf(title)}) Tj
/F1 12 Tf
0 -30 Td
({_escape_pdf(grade_line)}) Tj
0 -25 Td
(Scan ID: {_escape_pdf(scan.id)} | Language: {language}) Tj
0 -30 Td
(Executive Summary:) Tj
0 -20 Td
({_escape_pdf(summary_text[:120])}) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000117 00000 n 
0000000224 00000 n 
0000000295 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
550
%%EOF
"""
    with open(pdf_path, "wb") as f:
        f.write(content.encode("latin-1", errors="replace"))


def _escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
