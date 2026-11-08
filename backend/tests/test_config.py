from app.core.config import settings
from app.core.security import compute_finding_fingerprint, verify_hmac_signature


def test_settings_loaded():
    assert settings.API_PORT == 8000
    assert settings.GEMINI_MODEL == "gemini-3.8-flash"
    assert settings.ENVIRONMENT in ["development", "test", "production"]


def test_compute_finding_fingerprint():
    fp1 = compute_finding_fingerprint("cve-2024-1234", "example.com", "/api/v1")
    fp2 = compute_finding_fingerprint("cve-2024-1234", "EXAMPLE.COM", "/api/v1")
    fp3 = compute_finding_fingerprint("cve-2024-5678", "example.com", "/api/v1")

    # Host should be normalized to lowercase
    assert fp1 == fp2
    assert fp1 != fp3


def test_verify_hmac_signature():
    secret = "test-webhook-secret"
    payload = b'{"event": "payment.authorized"}'
    import hmac
    import hashlib

    valid_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(payload, valid_sig, secret) is True
    assert verify_hmac_signature(payload, "invalid_sig", secret) is False
