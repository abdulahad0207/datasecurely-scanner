import asyncio
from typing import Any, Dict, List
import httpx
from app.core.logging import logger

SENSITIVE_TARGETS = [
    {
        "path": "/.git/HEAD",
        "template_id": "exposed-git-head",
        "title": "Exposed Git Repository Directory (/.git/HEAD)",
        "severity": "high",
        "validator": lambda text: "ref: refs/" in text,
    },
    {
        "path": "/.git/config",
        "template_id": "exposed-git-config",
        "title": "Exposed Git Configuration File (/.git/config)",
        "severity": "high",
        "validator": lambda text: "[core]" in text or "[remote" in text,
    },
    {
        "path": "/.env",
        "template_id": "exposed-env-file",
        "title": "Exposed Application Environment File (/.env)",
        "severity": "critical",
        "validator": lambda text: any(key in text for key in ["DB_", "APP_", "SECRET", "API_KEY", "AWS_"]),
    },
    {
        "path": "/robots.txt",
        "template_id": "disclosed-robots-txt",
        "title": "Robots.txt Disclosing Administrative Paths",
        "severity": "info",
        "validator": lambda text: "disallow:" in text.lower(),
    },
]


async def check_exposed_files(hostname: str) -> List[Dict[str, Any]]:
    """
    Safely probes for exposed configuration files and sensitive directories.
    Strictly rate-limited and non-destructive.
    """
    findings = []
    headers = {"User-Agent": "datasecurely-scanner/1.0"}

    async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
        for item in SENSITIVE_TARGETS:
            url = f"https://{hostname}{item['path']}"
            try:
                resp = await client.get(url, headers=headers)
                # Ensure redirect did not leave target host
                if resp.url.host != hostname:
                    continue

                if resp.status_code == 200:
                    body = resp.text
                    if item["validator"](body):
                        # Truncate evidence to prevent leaking secrets in logs
                        evidence_sample = body[:120].strip().replace("\n", " ")
                        findings.append({
                            "source_tool": "custom_files",
                            "template_id": item["template_id"],
                            "title": item["title"],
                            "severity": item["severity"],
                            "host": hostname,
                            "evidence": f"File accessible at {url}: '{evidence_sample}'",
                        })
            except Exception as e:
                logger.debug(f"File probe error for {url}: {e}")

            await asyncio.sleep(0.1)  # Polite pacing

    return findings
