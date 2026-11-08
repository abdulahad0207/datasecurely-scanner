from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest
from app.core.errors import ScopeViolationError, VerificationRequiredError
from app.db.models import DomainModel
from app.services.scope_guard import ScopeGuard


@pytest.fixture
def guard():
    return ScopeGuard()


def test_scope_guard_blocked_ips(guard: ScopeGuard):
    # Prohibited IP ranges (SSRF & internal boundaries)
    prohibited_ips = [
        "127.0.0.1",
        "127.0.0.2",
        "10.0.0.1",
        "10.254.0.1",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.1",
        "192.168.1.254",
        "169.254.169.254",  # AWS/GCP metadata
        "169.254.1.1",
        "100.64.0.1",       # CGNAT
        "::1",
    ]
    for ip in prohibited_ips:
        assert guard.is_ip_blocked(ip) is True, f"Expected {ip} to be blocked"


def test_scope_guard_allowed_ips(guard: ScopeGuard):
    # Routable public IP ranges
    public_ips = [
        "93.184.216.34",   # example.com
        "1.1.1.1",
        "8.8.8.8",
        "142.250.190.46",  # google.com
    ]
    for ip in public_ips:
        assert guard.is_ip_blocked(ip) is False, f"Expected {ip} to be allowed"


def test_check_authorization(guard: ScopeGuard):
    now = datetime.now(timezone.utc)

    # Pending domain must fail
    pending_domain = DomainModel(
        id="d1", user_id="u1", hostname="pending.com", verify_token="t1", status="pending"
    )
    with pytest.raises(VerificationRequiredError, match="not verified"):
        guard.check_authorization(pending_domain)

    # Expired domain must fail
    expired_domain = DomainModel(
        id="d2",
        user_id="u1",
        hostname="expired.com",
        verify_token="t2",
        status="verified",
        verified_at=now - timedelta(days=95),
    )
    with pytest.raises(VerificationRequiredError, match="expired"):
        guard.check_authorization(expired_domain)

    # Valid verified domain must pass
    valid_domain = DomainModel(
        id="d3",
        user_id="u1",
        hostname="valid.com",
        verify_token="t3",
        status="verified",
        verified_at=now - timedelta(days=10),
    )
    guard.check_authorization(valid_domain)  # Should not raise


@pytest.mark.asyncio
async def test_resolve_and_guard_ssrf_blocked(guard: ScopeGuard):
    # Mock DNS resolving to internal loopback
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_res:
        mock_res.return_value = ["127.0.0.1"]
        with pytest.raises(ScopeViolationError, match="prohibited/internal IP range"):
            await guard.resolve_and_guard("internal-trap.com")


@pytest.mark.asyncio
async def test_resolve_and_guard_cloud_metadata_blocked(guard: ScopeGuard):
    # Mock DNS resolving to AWS/GCP cloud metadata service
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_res:
        mock_res.return_value = ["169.254.169.254"]
        with pytest.raises(ScopeViolationError, match="prohibited/internal IP range"):
            await guard.resolve_and_guard("cloud-metadata.com")


@pytest.mark.asyncio
async def test_resolve_and_guard_public_allowed(guard: ScopeGuard):
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_res:
        mock_res.return_value = ["93.184.216.34"]
        ips = await guard.resolve_and_guard("example.com")
        assert ips == ["93.184.216.34"]
