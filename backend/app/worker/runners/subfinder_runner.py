import json
from typing import List
from app.core.logging import logger
from app.worker.runners.base import safe_subprocess_exec, validate_target_arg


def parse_subfinder_output(raw_output: str) -> List[str]:
    """Parses JSON or plaintext output from subfinder into list of hostnames."""
    subdomains = set()
    for line in raw_output.strip().splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        try:
            data = json.loads(clean_line)
            host = data.get("host")
            if host:
                subdomains.add(host.lower().strip())
        except json.JSONDecodeError:
            # Fallback to plain line output
            subdomains.add(clean_line.lower())
    return sorted(list(subdomains))


async def run_subfinder(domain: str, timeout: int = 30) -> List[str]:
    """Runs subfinder passive reconnaissance on verified domain."""
    clean_domain = validate_target_arg(domain)
    cmd = [
        "subfinder",
        "-d", clean_domain,
        "-json",
        "-silent",
        "-timeout", "5",
        "-max-time", "20",
    ]

    code, stdout, stderr = await safe_subprocess_exec(cmd, timeout_seconds=timeout)
    if code != 0 or not stdout:
        logger.info(f"subfinder CLI returned code {code} or empty output.")
        return []

    return parse_subfinder_output(stdout)
