import asyncio
from typing import List
from app.core.logging import logger
from app.schemas.finding import Finding
from app.worker.ai.client import gemini_client
from app.worker.ai.sanitizer import prepare_finding_for_ai


async def triage_all_findings(
    findings: List[Finding],
    language: str = "en",
    max_concurrency: int = 5,
) -> List[Finding]:
    """
    Applies AI triage across all findings:
    - Sanitizes evidence blocks against prompt injection.
    - Limits concurrency to protect rate limits.
    - Populates finding.ai_json with structured remediation guidance.
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _triage_single(finding: Finding) -> None:
        async with semaphore:
            finding_dict = {
                "title": finding.title,
                "template_id": finding.template_id,
                "severity": finding.severity,
                "host": finding.host,
                "evidence": finding.evidence or "",
                "fingerprint": finding.fingerprint,
            }
            safe_payload = prepare_finding_for_ai(finding_dict)
            safe_payload["fingerprint"] = finding.fingerprint

            ai_result = await gemini_client.triage_finding(
                finding_data=safe_payload,
                language=language,
            )
            finding.ai_json = ai_result

    tasks = [_triage_single(f) for f in findings]
    if tasks:
        await asyncio.gather(*tasks)

    logger.info(f"AI Triage completed for {len(findings)} findings in language '{language}'.")
    return findings
