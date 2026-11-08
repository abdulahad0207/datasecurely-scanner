import re
from typing import Any, Dict

# Prohibited prompt-injection patterns
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?prior", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|developer)", re.IGNORECASE),
    re.compile(r"<\/?system>", re.IGNORECASE),
    re.compile(r"<\/?instruction>", re.IGNORECASE),
]

MAX_FIELD_LENGTH = 500


def sanitize_untrusted_text(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """
    Sanitizes arbitrary text originating from target web servers:
    1. Removes non-printable/control characters.
    2. Defuses prompt-injection strings by neutralizing known trigger phrases.
    3. Truncates text to max_length.
    """
    if not text:
        return ""

    # Remove non-printable control characters except \n and \t
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t ")

    # Defuse injection phrases
    for pattern in INJECTION_PATTERNS:
        cleaned = pattern.sub("[FILTERED_INJECTION_ATTEMPT]", cleaned)

    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + " [TRUNCATED]"

    return cleaned.strip()


def wrap_untrusted_evidence(text: str) -> str:
    """Wraps sanitized text in strict XML boundary tags."""
    safe_text = sanitize_untrusted_text(text)
    # Neutralize any accidental closing tags inside the text
    safe_text = safe_text.replace("</untrusted_evidence>", "[ESCAPED_TAG]")
    return f"<untrusted_evidence>\n{safe_text}\n</untrusted_evidence>"


def prepare_finding_for_ai(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares a Finding object for prompt inclusion, isolating untrusted
    evidence from server responses.
    """
    return {
        "title": sanitize_untrusted_text(finding.get("title", ""), max_length=150),
        "template_id": sanitize_untrusted_text(finding.get("template_id", ""), max_length=100),
        "severity": finding.get("severity", "info"),
        "host": sanitize_untrusted_text(finding.get("host", ""), max_length=100),
        "evidence_block": wrap_untrusted_evidence(finding.get("evidence", "")),
    }
