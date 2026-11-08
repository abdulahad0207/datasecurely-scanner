from typing import List, Optional
from app.core.logging import logger
from app.schemas.finding import Finding, ScanAISummary
from app.worker.ai.client import gemini_client


async def generate_executive_report_summary(
    hostname: str,
    grade: str,
    findings: List[Finding],
    language: str = "en",
    base_summary: Optional[ScanAISummary] = None,
) -> ScanAISummary:
    """
    Produces executive summary and top 3 prioritized action items
    using Google Gemini with semantic parity across English and Hinglish.
    """
    logger.info(f"Generating executive summary for {hostname} (Grade: {grade}, Language: {language})")

    summary = await gemini_client.generate_scan_summary(
        hostname=hostname,
        grade=grade,
        findings_count=len(findings),
        language=language,
        findings=findings,
        base_summary=base_summary,
    )

    return summary
