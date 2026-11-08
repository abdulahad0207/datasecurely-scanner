from unittest.mock import AsyncMock, patch
import httpx
import pytest
from app.worker.checks.cookies import check_cookie_security
from app.worker.checks.exposed_files import check_exposed_files
from app.worker.checks.headers import check_security_headers
from app.worker.checks.tls import check_tls_configuration


@pytest.mark.asyncio
async def test_check_security_headers():
    mock_resp = AsyncMock()
    mock_resp.headers = {
        "Server": "nginx/1.18.0 (Ubuntu)",
        "X-Powered-By": "PHP/7.4.3",
        # Missing HSTS, CSP, X-Frame-Options
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        findings = await check_security_headers("test-headers.com")

        template_ids = [f["template_id"] for f in findings]
        assert "missing-strict-transport-security" in template_ids
        assert "missing-content-security-policy" in template_ids
        assert "exposed-server-version" in template_ids
        assert "exposed-x-powered-by" in template_ids


@pytest.mark.asyncio
async def test_check_cookie_security():
    mock_resp = AsyncMock()
    # Headers in httpx is synchronous
    mock_resp.headers = httpx.Headers([
        ("set-cookie", "session_id=12345; Path=/"),
        ("set-cookie", "theme=dark; Secure; SameSite=Lax"),
    ])

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        findings = await check_cookie_security("test-cookies.com")

        template_ids = [f["template_id"] for f in findings]
        assert "cookie-missing-secure" in template_ids
        assert "cookie-missing-httponly" in template_ids
        assert "cookie-missing-samesite" in template_ids


@pytest.mark.asyncio
async def test_check_exposed_files():
    mock_resp_git = AsyncMock()
    mock_resp_git.status_code = 200
    mock_resp_git.text = "ref: refs/heads/main\n"
    mock_resp_git.url.host = "test-exposed.com"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp_git
        findings = await check_exposed_files("test-exposed.com")

        template_ids = [f["template_id"] for f in findings]
        assert "exposed-git-head" in template_ids


@pytest.mark.asyncio
async def test_check_tls_configuration_mock():
    # Mocking SSL/TLS cert returned by _sync_tls_inspect
    mock_cert = {
        "notAfter": "May  1 12:00:00 2020 GMT",  # Expired
    }
    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = (mock_cert, "TLSv1.2", ("ECDHE-RSA-AES128-GCM-SHA256", "TLSv1.2", 128))
        findings = await check_tls_configuration("test-tls.com")

        template_ids = [f["template_id"] for f in findings]
        assert "tls-cert-expired" in template_ids
