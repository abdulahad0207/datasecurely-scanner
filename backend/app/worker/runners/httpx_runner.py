import json
from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.worker.runners.base import safe_subprocess_exec, validate_target_arg


def parse_httpx_output(raw_output: str) -> List[Dict[str, Any]]:
    """Parses JSON or JSON-lines output from httpx."""
    results = []
    for line in raw_output.strip().splitlines():
        clean_line = line.strip()
        if clean_line:
            try:
                data = json.loads(clean_line)
                results.append({
                    "url": data.get("url"),
                    "host": data.get("input") or data.get("host"),
                    "status_code": data.get("status_code"),
                    "title": data.get("title"),
                    "webserver": data.get("webserver"),
                    "tech": data.get("tech", []),
                    "tls_version": data.get("tls", {}).get("version"),
                    "tls_cipher": data.get("tls", {}).get("cipher"),
                })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode httpx JSON line: {e}")
    return results


async def run_httpx(target: str, timeout: int = 15) -> List[Dict[str, Any]]:
    """Runs httpx against a validated target hostname."""
    clean_target = validate_target_arg(target)
    cmd = [
        "httpx",
        "-u", clean_target,
        "-title",
        "-status-code",
        "-tech-detect",
        "-json",
        "-silent",
        "-timeout", "5",
        "-rate-limit", "10",
    ]

    code, stdout, stderr = await safe_subprocess_exec(cmd, timeout_seconds=timeout)
    if code != 0 or not stdout:
        logger.info(f"httpx CLI returned code {code} or empty output. Using parser fallback.")
        return []

    return parse_httpx_output(stdout)
