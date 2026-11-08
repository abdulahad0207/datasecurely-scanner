from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from app.services.verification import (
    check_dns_txt,
    check_well_known_file,
    is_verification_expired,
    verify_domain_ownership,
)

AUTH_HEADERS = {"Authorization": "Bearer test-token-verify-user-1"}


def test_is_verification_expired():
    now = datetime.now(timezone.utc)
    assert is_verification_expired(None) is True
    assert is_verification_expired(now) is False
    assert is_verification_expired(now - timedelta(days=89)) is False
    assert is_verification_expired(now - timedelta(days=91)) is True


@pytest.mark.asyncio
async def test_dns_txt_matched():
    token = "test-token-123456"

    class MockRdata:
        strings = [b"datasecurely-verify=test-token-123456"]

    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = [MockRdata()]
        ok, msg = await check_dns_txt("example.com", token)
        assert ok is True
        assert "Valid TXT record detected" in msg


@pytest.mark.asyncio
async def test_dns_txt_unmatched():
    token = "test-token-123456"

    class MockRdata:
        strings = [b"v=spf1 include:_spf.google.com ~all"]

    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = [MockRdata()]
        ok, msg = await check_dns_txt("example.com", token)
        assert ok is False
        assert "none matched" in msg


@pytest.mark.asyncio
async def test_well_known_matched():
    token = "test-token-secret-789"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = f"  {token}  "
        mock_resp.url.host = "example.com"
        mock_get.return_value = mock_resp

        ok, msg = await check_well_known_file("example.com", token)
        assert ok is True
        assert "Verification token found" in msg


@pytest.mark.asyncio
async def test_well_known_offscope_redirect():
    token = "test-token-secret-789"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = token
        mock_resp.url.host = "evil-site.com"  # Off-scope redirect
        mock_get.return_value = mock_resp

        ok, msg = await check_well_known_file("example.com", token)
        assert ok is False
        assert "Redirected off-scope" in msg


@pytest.mark.asyncio
async def test_verify_domain_api_flow(async_client: AsyncClient):
    # 1. Add domain
    add_res = await async_client.post(
        "/api/v1/domains",
        json={"hostname": "verify-flow-test.in"},
        headers=AUTH_HEADERS,
    )
    assert add_res.status_code == 201
    domain_id = add_res.json()["id"]
    assert add_res.json()["status"] == "pending"

    # 2. Trigger verify endpoint (fails because domain does not exist in DNS/HTTP)
    verify_res1 = await async_client.post(
        f"/api/v1/domains/{domain_id}/verify",
        headers=AUTH_HEADERS,
    )
    assert verify_res1.status_code == 200
    data1 = verify_res1.json()
    assert data1["verified"] is False
    assert data1["status"] == "pending"

    # 3. Mock a successful DNS TXT check and trigger verify again
    with patch("app.services.verification.check_dns_txt", new_callable=AsyncMock) as mock_dns:
        mock_dns.return_value = (True, "Valid TXT record verified")
        verify_res2 = await async_client.post(
            f"/api/v1/domains/{domain_id}/verify",
            headers=AUTH_HEADERS,
        )
        assert verify_res2.status_code == 200
        data2 = verify_res2.json()
        assert data2["verified"] is True
        assert data2["status"] == "verified"
        assert data2["method"] == "dns_txt"
        assert data2["verified_at"] is not None

    # 4. Confirm domain status in GET
    get_res = await async_client.get(f"/api/v1/domains/{domain_id}", headers=AUTH_HEADERS)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "verified"
    assert get_res.json()["verified_at"] is not None
