import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from app.api.middleware.rate_limiter import limiter
from app.core.config import settings
from app.core.sentry import _filter_client_exceptions, init_sentry


@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    res = await async_client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "strict-origin-when-cross-origin" in headers.get("Referrer-Policy", "")
    assert "Content-Security-Policy" in headers
    csp = headers.get("Content-Security-Policy")
    assert "default-src 'self'" in csp
    assert "https://checkout.razorpay.com" in csp
    assert "frame-src 'self' https://api.razorpay.com" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "img-src 'self' data: https:" in csp
    assert "connect-src" in csp


def test_csp_policy_environment_conditional(monkeypatch):
    """Verifies unsafe-eval is present in development, but strictly excluded in production."""
    from app.api.middleware.security_headers import build_csp_policy

    # Development mode: unsafe-eval present
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    dev_csp = build_csp_policy()
    assert "'unsafe-eval'" in dev_csp
    assert "https://checkout.razorpay.com" in dev_csp
    assert "https://api.razorpay.com" in dev_csp

    # Production mode: unsafe-eval strictly excluded
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    prod_csp = build_csp_policy()
    assert "'unsafe-eval'" not in prod_csp
    assert "https://checkout.razorpay.com" in prod_csp
    assert "https://api.razorpay.com" in prod_csp
    assert "'unsafe-inline'" in prod_csp


def test_csp_dynamic_settings_urls(monkeypatch):
    """Verifies that CSP connect-src uses settings.API_URL and FRONTEND_URL dynamically."""
    from app.api.middleware.security_headers import build_csp_policy

    monkeypatch.setattr(settings, "API_URL", "https://api.staging.example.com")
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://app.staging.example.com")
    csp = build_csp_policy()
    assert "https://api.staging.example.com" in csp
    assert "https://app.staging.example.com" in csp


@pytest.mark.asyncio
async def test_rate_limiter_headers_and_limit(async_client: AsyncClient):
    limiter.clear()
    res = await async_client.get("/api/v1/billing/plans")
    assert res.status_code == 200
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers


@pytest.mark.asyncio
async def test_rate_limiter_blocks_flood_abuse(async_client: AsyncClient):
    limiter.clear()
    client_ip = "198.51.100.42"
    headers = {"X-Forwarded-For": client_ip}

    # Fill quota up to limit for a test key
    rule_key = "POST:/api/v1/billing/create-order:198.51.100.42"
    for _ in range(20):
        limiter.is_rate_limited(rule_key, max_requests=20, window_seconds=60)

    # Next request from this IP to this endpoint should be blocked with 429
    auth_headers = {
        "Authorization": "Bearer test-token-flooduser-flood@test.in",
        "X-Forwarded-For": client_ip,
    }
    blocked_res = await async_client.post(
        "/api/v1/billing/create-order",
        json={"plan": "full"},
        headers=auth_headers,
    )
    assert blocked_res.status_code == 429
    assert "Retry-After" in blocked_res.headers
    assert "rate limit exceeded" in blocked_res.json()["detail"].lower()


def test_sentry_init_safely_no_ops_without_dsn(monkeypatch):
    # When DSN is None or mock, init_sentry returns False without raising
    monkeypatch.setattr(settings, "SENTRY_DSN", None)
    result = init_sentry()
    assert result is False


def test_sentry_filters_client_4xx_exceptions():
    # 404 error should be dropped
    hint_404 = {"exc_info": (HTTPException, HTTPException(status_code=404, detail="Not Found"), None)}
    event = {"message": "Client error"}
    filtered = _filter_client_exceptions(event, hint_404)
    assert filtered is None

    # 500 error should be retained
    hint_500 = {"exc_info": (HTTPException, HTTPException(status_code=500, detail="Server Error"), None)}
    retained = _filter_client_exceptions(event, hint_500)
    assert retained is not None
