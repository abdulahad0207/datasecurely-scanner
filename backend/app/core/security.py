import hmac
import hashlib
from typing import Optional
from app.core.config import settings


def verify_hmac_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Safely verifies HMAC SHA256 signatures (e.g. for Razorpay webhooks)."""
    computed = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)


def compute_finding_fingerprint(template_id: str, host: str, path: Optional[str] = None) -> str:
    """Computes a deterministic hash fingerprint for finding deduplication."""
    clean_path = (path or "").strip().lower()
    raw = f"{template_id.strip()}:{host.strip().lower()}:{clean_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
