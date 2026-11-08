from typing import Any, Dict, List
from app.core.logging import logger
from app.worker.runners.httpx_runner import run_httpx
from app.worker.runners.subfinder_runner import run_subfinder


async def run_recon_stage(hostname: str, profile: str = "free") -> Dict[str, Any]:
    """
    Executes reconnaissance stage:
    - Probes live web services and tech fingerprinting via httpx.
    - If profile is 'full', executes passive subdomain discovery via subfinder.
    """
    logger.info(f"Recon stage starting for {hostname} (profile: {profile})")

    # 1. Probe live host
    httpx_results = await run_httpx(hostname)

    # 2. Subdomains (Full profile only)
    subdomains = []
    if profile in ["full", "monitor"]:
        subdomains = await run_subfinder(hostname)

    return {
        "hostname": hostname,
        "profile": profile,
        "live_hosts": httpx_results,
        "subdomains": subdomains,
    }
