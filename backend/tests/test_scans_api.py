import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from app.db.repository import repo

AUTH_HEADERS = {"Authorization": "Bearer test-token-scan-user-1"}


@pytest.mark.asyncio
async def test_start_scan_unverified_rejected(async_client: AsyncClient):
    # Add domain (default status pending)
    uid = uuid.uuid4().hex[:6]
    domain_res = await async_client.post(
        "/api/v1/domains",
        json={"hostname": f"unverified-scan-{uid}.com"},
        headers=AUTH_HEADERS,
    )
    domain_id = domain_res.json()["id"]

    # Attempt to scan unverified domain
    scan_res = await async_client.post(
        "/api/v1/scans",
        json={"domain_id": domain_id, "profile": "free"},
        headers=AUTH_HEADERS,
    )
    assert scan_res.status_code == 403
    assert "not verified" in scan_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_scan_verified_accepted(async_client: AsyncClient):
    # 1. Add domain
    uid = uuid.uuid4().hex[:6]
    domain_res = await async_client.post(
        "/api/v1/domains",
        json={"hostname": f"verified-scan-{uid}.com"},
        headers=AUTH_HEADERS,
    )
    domain_id = domain_res.json()["id"]

    # 2. Mark verified
    await repo.update_domain_status(
        domain_id=domain_id,
        status="verified",
        verified_at=datetime.now(timezone.utc),
    )

    # 3. Start scan
    scan_res = await async_client.post(
        "/api/v1/scans",
        json={"domain_id": domain_id, "profile": "free"},
        headers=AUTH_HEADERS,
    )
    assert scan_res.status_code == 202
    scan_data = scan_res.json()
    assert scan_data["status"] == "queued"
    assert scan_data["progress"] == 0
    assert scan_data["domain_id"] == domain_id
    scan_id = scan_data["id"]

    # 4. Get scan status
    status_res = await async_client.get(f"/api/v1/scans/{scan_id}", headers=AUTH_HEADERS)
    assert status_res.status_code == 200
    assert status_res.json()["id"] == scan_id

    # 5. List domain scans
    list_res = await async_client.get(f"/api/v1/scans/domain/{domain_id}", headers=AUTH_HEADERS)
    assert list_res.status_code == 200
    assert len(list_res.json()["scans"]) >= 1
