import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from app.db.repository import repo
from app.worker.pipeline.orchestrator import execute_scan_pipeline


@pytest.mark.asyncio
async def test_execute_scan_pipeline_lifecycle():
    user_id = "test-orch-user-1"
    # 1. Create verified domain
    domain = await repo.create_domain(
        user_id=user_id,
        hostname="scan-lifecycle.org",
        verify_token="test-token-orch",
    )
    await repo.update_domain_status(
        domain_id=domain.id,
        status="verified",
        verified_at=datetime.now(timezone.utc),
    )

    # 2. Create scan
    scan = await repo.create_scan(
        domain_id=domain.id,
        user_id=user_id,
        hostname=domain.hostname,
        profile="free",
    )
    assert scan.status == "queued"

    # 3. Mock public DNS resolution and execute pipeline with fast_mode
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
        mock_dns.return_value = ["93.184.216.34"]
        await execute_scan_pipeline(scan_id=scan.id, fast_mode=True)

    # 4. Verify completed state and progress
    updated = await repo.get_scan(scan.id)
    assert updated.status == "completed"
    assert updated.progress == 100
    assert updated.grade in ["A", "B"]
    assert updated.findings_count >= 1
    assert updated.finished_at is not None
    assert updated.error is None


@pytest.mark.asyncio
async def test_execute_scan_pipeline_ssrf_aborted():
    user_id = "test-orch-user-2"
    # Create verified domain pointing to internal IP
    domain = await repo.create_domain(
        user_id=user_id,
        hostname="internal-target.lan.com",
        verify_token="test-token-orch2",
    )
    await repo.update_domain_status(
        domain_id=domain.id,
        status="verified",
        verified_at=datetime.now(timezone.utc),
    )

    scan = await repo.create_scan(
        domain_id=domain.id,
        user_id=user_id,
        hostname=domain.hostname,
        profile="free",
    )

    # Mock DNS resolving to private IP 10.0.0.1
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
        mock_dns.return_value = ["10.0.0.1"]
        await execute_scan_pipeline(scan_id=scan.id, fast_mode=True)

    updated = await repo.get_scan(scan.id)
    assert updated.status == "failed"
    assert "prohibited/internal IP range" in updated.error


@pytest.mark.asyncio
async def test_execute_scan_pipeline_timeout():
    user_id = "test-orch-user-3"
    domain = await repo.create_domain(
        user_id=user_id,
        hostname="timeout-target.com",
        verify_token="test-token-orch3",
    )
    await repo.update_domain_status(
        domain_id=domain.id,
        status="verified",
        verified_at=datetime.now(timezone.utc),
    )

    scan = await repo.create_scan(
        domain_id=domain.id,
        user_id=user_id,
        hostname=domain.hostname,
        profile="free",
    )

    # Execute with an almost-zero timeout (e.g. 0.001s)
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
        # Simulate DNS delay to trigger timeout
        async def slow_dns(*args, **kwargs):
            await asyncio.sleep(0.1)
            return ["93.184.216.34"]

        mock_dns.side_effect = slow_dns
        await execute_scan_pipeline(scan_id=scan.id, timeout_seconds=0.01, fast_mode=True)

    updated = await repo.get_scan(scan.id)
    assert updated.status == "failed"
    assert "timeout" in updated.error.lower()
