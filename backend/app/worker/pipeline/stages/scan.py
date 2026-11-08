import asyncio
from typing import Any, Dict, List
from app.core.logging import logger
from app.worker.checks.cookies import check_cookie_security
from app.worker.checks.exposed_files import check_exposed_files
from app.worker.checks.headers import check_security_headers
from app.worker.checks.tls import check_tls_configuration
from app.worker.runners.nmap_runner import run_nmap
from app.worker.runners.nuclei_runner import run_nuclei


async def run_scan_stage(hostname: str, profile: str = "free") -> List[Dict[str, Any]]:
    """
    Executes the full vulnerability and misconfiguration scanning stage:
    1. Custom Python checks (headers, TLS, cookies, exposed files)
    2. Safe Nuclei profile templates
    3. Safe unprivileged Nmap top-port scan (if profile is 'full')
    """
    logger.info(f"Scan stage starting for {hostname} (profile: {profile})")
    raw_findings: List[Dict[str, Any]] = []

    # Run custom checks concurrently
    custom_results = await asyncio.gather(
        check_security_headers(hostname),
        check_tls_configuration(hostname),
        check_cookie_security(hostname),
        check_exposed_files(hostname),
        return_exceptions=True,
    )

    for res in custom_results:
        if isinstance(res, list):
            raw_findings.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Custom check error: {res}")

    # Run safe Nuclei checks
    try:
        nuclei_results = await run_nuclei(hostname)
        for item in nuclei_results:
            raw_findings.append({
                "source_tool": "nuclei",
                "template_id": item["template_id"],
                "title": item["title"],
                "severity": item["severity"],
                "host": hostname,
                "evidence": item.get("matched_at") or "",
            })
    except Exception as e:
        logger.warning(f"Nuclei scan error: {e}")

    # Port scanning (Full profile only)
    if profile in ["full", "monitor"]:
        try:
            nmap_ports = await run_nmap(hostname)
            for p in nmap_ports:
                # Flag unexpected sensitive open ports (e.g. database, remote access)
                if p["port"] not in [80, 443]:
                    raw_findings.append({
                        "source_tool": "nmap",
                        "template_id": f"open-port-{p['port']}",
                        "title": f"Non-Standard Port {p['port']} ({p['service']}) Exposed",
                        "severity": "medium" if p["port"] in [21, 22, 23, 3306, 5432, 27017, 6379] else "low",
                        "host": hostname,
                        "evidence": f"Port {p['port']}/{p['protocol']} ({p['service']}) is OPEN to the Internet.",
                    })
        except Exception as e:
            logger.warning(f"Nmap scan error: {e}")

    logger.info(f"Scan stage completed for {hostname}. Gathered {len(raw_findings)} raw findings.")
    return raw_findings
