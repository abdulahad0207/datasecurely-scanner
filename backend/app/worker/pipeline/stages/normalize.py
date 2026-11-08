import hashlib
from typing import Any, Dict, List
from app.core.logging import logger
from app.schemas.finding import Finding

# Equivalence map to normalize template IDs across multiple scanner engines
CANONICAL_TEMPLATE_MAP = {
    # Security Headers
    "missing-content-security-policy": "canonical:missing-csp",
    "missing-csp-header": "canonical:missing-csp",
    "csp-detect": "canonical:missing-csp",
    "missing-strict-transport-security": "canonical:missing-hsts",
    "hsts-missing": "canonical:missing-hsts",
    "missing-x-frame-options": "canonical:missing-x-frame-options",
    "x-frame-options": "canonical:missing-x-frame-options",
    "missing-x-content-type-options": "canonical:missing-x-content-type-options",
    "missing-referrer-policy": "canonical:missing-referrer-policy",
    "missing-permissions-policy": "canonical:missing-permissions-policy",
    # Sensitive Exposures
    "exposed-git-head": "canonical:exposed-git",
    "exposed-git-config": "canonical:exposed-git",
    "git-config": "canonical:exposed-git",
    "exposed-env-file": "canonical:exposed-env",
    "env-file": "canonical:exposed-env",
    # TLS
    "tls-cert-expired": "canonical:tls-cert-expired",
    "ssl-cert-expired": "canonical:tls-cert-expired",
    "deprecated-tls-protocol": "canonical:tls-deprecated-version",
}

SEVERITY_ORDER = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def compute_normalized_fingerprint(template_id: str, host: str, path: str = "") -> str:
    """Computes a deterministic SHA-256 fingerprint from canonical template and target."""
    canonical_id = CANONICAL_TEMPLATE_MAP.get(template_id, template_id)
    clean_host = host.lower().strip()
    clean_path = path.lower().strip().split("?")[0]
    raw = f"{canonical_id}:{clean_host}:{clean_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_and_dedupe_findings(raw_findings: List[Dict[str, Any]], scan_id: str) -> List[Finding]:
    """
    Normalizes diverse raw scanner outputs into the unified Finding schema
    and deduplicates findings with matching signatures.
    """
    grouped_findings: Dict[str, Dict[str, Any]] = {}

    for raw in raw_findings:
        template_id = raw.get("template_id", "unknown")
        canonical_id = CANONICAL_TEMPLATE_MAP.get(template_id, template_id)
        host = raw.get("host", "unknown").lower().replace("https://", "").replace("http://", "").strip("/")
        severity = raw.get("severity", "info").lower()
        if severity not in SEVERITY_ORDER:
            severity = "info"

        fingerprint = compute_normalized_fingerprint(canonical_id, host)

        if fingerprint not in grouped_findings:
            grouped_findings[fingerprint] = {
                "scan_id": scan_id,
                "source_tool": raw.get("source_tool", "unknown"),
                "template_id": canonical_id,
                "title": raw.get("title", "Detected Security Issue"),
                "severity": severity,
                "host": host,
                "evidence": raw.get("evidence", "")[:2048],
                "raw_ref": raw.get("template_id"),
                "fingerprint": fingerprint,
            }
        else:
            # Merge duplicate
            existing = grouped_findings[fingerprint]
            # 1. Escalate to highest severity
            if SEVERITY_ORDER[severity] > SEVERITY_ORDER[existing["severity"]]:
                existing["severity"] = severity

            # 2. Track contributing tools
            tool_name = raw.get("source_tool", "unknown")
            if tool_name not in existing["source_tool"]:
                existing["source_tool"] = f"{existing['source_tool']}, {tool_name}"

            # 3. Append extra evidence if not already present
            new_evidence = raw.get("evidence", "")
            if new_evidence and new_evidence not in existing["evidence"]:
                combined = f"{existing['evidence']} | {new_evidence}"
                existing["evidence"] = combined[:2048]

    # Convert to Pydantic Finding objects
    deduped = [Finding(**data) for data in grouped_findings.values()]
    # Sort deterministically by severity (highest first) then title
    deduped.sort(key=lambda f: (-SEVERITY_ORDER.get(f.severity, 0), f.title))

    logger.info(
        f"Normalized {len(raw_findings)} raw findings down to {len(deduped)} deduplicated findings for scan {scan_id}."
    )
    return deduped
