from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from app.db.repository import repo
from app.worker.pipeline.orchestrator import execute_scan_pipeline

AUTH_HEADERS = {"Authorization": "Bearer test-token-finduser1-find@example.com"}


@pytest.mark.asyncio
async def test_get_scan_findings_api(async_client: AsyncClient):
    user_id = "finduser1"
    # 1. Create and verify domain
    domain = await repo.create_domain(
        user_id=user_id,
        hostname="findings-api-test.in",
        verify_token="test-token-find",
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

    # 3. Execute scan pipeline
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
        mock_dns.return_value = ["93.184.216.34"]
        await execute_scan_pipeline(scan_id=scan.id, fast_mode=True)

    # 4. Fetch findings via API
    res = await async_client.get(f"/api/v1/scans/{scan.id}/findings", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "findings" in data
    assert data["total"] >= 1
    f = data["findings"][0]
    assert "template_id" in f
    assert "severity" in f
    assert "fingerprint" in f
