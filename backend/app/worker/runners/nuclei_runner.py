import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.worker.runners.base import safe_subprocess_exec, validate_target_arg


def parse_nuclei_output(raw_output: str) -> List[Dict[str, Any]]:
    """Parses JSON-lines output from Nuclei scanner."""
    findings = []
    for line in raw_output.strip().splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        try:
            data = json.loads(clean_line)
            info = data.get("info", {})
            findings.append({
                "template_id": data.get("template-id", "unknown"),
                "title": info.get("name", "Untitled Finding"),
                "severity": info.get("severity", "info").lower(),
                "host": data.get("host"),
                "matched_at": data.get("matched-at"),
                "extracted_results": data.get("extracted-results", []),
                "curl_command": data.get("curl-command"),
                "type": data.get("type"),
                "tags": info.get("tags", []),
            })
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode nuclei JSON line: {e}")
    return findings


async def run_nuclei(
    target: str,
    profile_path: Optional[str] = "config/nuclei-safe-profile.yaml",
    timeout: int = 120,
) -> List[Dict[str, Any]]:
    """Runs Nuclei with the safe profile against target."""
    clean_target = validate_target_arg(target)
    config_file = str(settings.BASE_DIR / (profile_path or "config/nuclei-safe-profile.yaml"))

    cmd = [
        "nuclei",
        "-u", f"https://{clean_target}",
        "-config", config_file,
        "-jsonl",
        "-silent",
        "-rate-limit", "10",
        "-concurrency", "5",
        "-timeout", "5",
    ]

    code, stdout, stderr = await safe_subprocess_exec(cmd, timeout_seconds=timeout)
    if code != 0 or not stdout:
        logger.info(f"nuclei CLI returned code {code} or empty output.")
        return []

    return parse_nuclei_output(stdout)
