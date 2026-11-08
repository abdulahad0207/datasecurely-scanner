import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from arq.worker import Worker, async_check_health
from app.api.main import create_app
from app.db.repository import repo
from app.services.queue import ScanQueue, get_redis_settings, queue
from app.worker.main import WorkerSettings, run_scan_job


@pytest.mark.asyncio
async def test_redis_settings_and_connection():
    """Confirms get_redis_settings resolves valid connection parameters and connects to Redis."""
    rs = get_redis_settings()
    assert rs.port == 6379
    assert rs.database == 0
    pool = await queue.get_pool()
    assert pool is not None
    res = await pool.ping()
    assert res is True


@pytest.mark.asyncio
async def test_worker_health_check():
    """Confirms worker health check reporting via ARQ and /health endpoint."""
    rs = get_redis_settings()
    pool = await queue.get_pool()
    assert pool is not None

    # Verify async_check_health returns 0 when worker is registered in Redis
    code = await async_check_health(rs, health_check_key=WorkerSettings.health_check_key)
    assert code == 0

    # Query API /health endpoint
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["redis"] == "connected"
        assert data["worker"] in ("healthy", "standby")


@pytest.mark.asyncio
async def test_scan_job_deduplication():
    """Confirms enqueuing the same scan ID multiple times returns deterministic job ID without duplicates."""
    scan_id = str(uuid.uuid4())
    job_id_1 = await queue.enqueue_scan(scan_id=scan_id, timeout_seconds=60, fast_mode=True)
    assert job_id_1 == f"scan_{scan_id}"

    # Second enqueue attempt should return deduplicated ID
    job_id_2 = await queue.enqueue_scan(scan_id=scan_id, timeout_seconds=60, fast_mode=True)
    assert job_id_2 == f"scan_{scan_id}"


@pytest.mark.asyncio
async def test_enqueue_job_survives_api_crash_and_completes_in_worker():
    """
    Core Architecture Test:
    1. An authorized user enqueues a scan job via the API.
    2. The API process abruptly crashes (client closed, pool closed, memory discarded).
    3. The job remains durable in Redis.
    4. An ARQ worker consumes the job from Redis and executes the complete pipeline.
    5. A restarted API process reads the database and confirms the scan successfully finished.
    """
    # 1. Setup user and verified domain
    unique_suffix = uuid.uuid4().hex[:6]
    test_user_id = f"worker-test-user-{unique_suffix}"
    auth_headers = {"Authorization": f"Bearer test-token-{test_user_id}-worker@example.com"}

    # Start initial API instance
    api_app_1 = create_app()
    transport_1 = ASGITransport(app=api_app_1)
    async with AsyncClient(transport=transport_1, base_url="http://test") as client_1:
        # Register domain (using unique nip.io hostname that resolves to public IP 93.184.216.34)
        unique_hostname = f"durability-{unique_suffix}.93.184.216.34.nip.io"
        domain_res = await client_1.post(
            "/api/v1/domains",
            json={"hostname": unique_hostname},
            headers=auth_headers,
        )
        assert domain_res.status_code == 201, domain_res.text
        domain_id = domain_res.json()["id"]

        # Mark domain as verified
        await repo.update_domain_status(
            domain_id=domain_id,
            status="verified",
            verified_at=datetime.now(timezone.utc),
        )

        # Enqueue scan via POST /api/v1/scans
        scan_res = await client_1.post(
            "/api/v1/scans",
            json={"domain_id": domain_id, "profile": "free"},
            headers=auth_headers,
        )
        assert scan_res.status_code == 202, scan_res.text
        scan_data = scan_res.json()
        scan_id = scan_data["id"]
        assert scan_data["status"] == "queued"

    # 2. SIMULATE API PROCESS CRASH / TERMINATION
    del client_1
    del transport_1
    del api_app_1
    await queue.close()

    # 3. VERIFY JOB PERSISTENCE & EXECUTION
    # If the live Docker worker hasn't consumed it yet, run burst worker to process it
    pool = await queue.get_pool()
    if pool:
        try:
            job = await pool.get_job(f"scan_{scan_id}")
            if job:
                job_status = await job.status()
                if job_status in ("queued", "deferred"):
                    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
                        mock_dns.return_value = ["93.184.216.34"]
                        worker = Worker(
                            functions=[run_scan_job],
                            redis_settings=get_redis_settings(),
                            burst=True,
                        )
                        await worker.async_run()
                        await worker.close()
        except Exception:
            pass

    # 4. RESTART API PROCESS AND POLL SCAN COMPLETION
    api_app_2 = create_app()
    transport_2 = ASGITransport(app=api_app_2)
    async with AsyncClient(transport=transport_2, base_url="http://test") as client_2:
        finished_scan = None
        for _ in range(40):
            poll_res = await client_2.get(f"/api/v1/scans/{scan_id}", headers=auth_headers)
            assert poll_res.status_code == 200, poll_res.text
            finished_scan = poll_res.json()
            if finished_scan["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.5)

        assert finished_scan is not None
        assert finished_scan["status"] == "completed", f"Scan ended with unexpected state: {finished_scan}"
        assert finished_scan["progress"] == 100
        assert finished_scan["grade"] in ("A", "B", "C")
        assert finished_scan["findings_count"] >= 0
        assert finished_scan["finished_at"] is not None
        assert finished_scan["error"] is None


@pytest.mark.asyncio
async def test_queue_in_process_fallback_when_redis_offline():
    """Confirms queue gracefully falls back to in-process task if Redis pool cannot be established."""
    fallback_queue = ScanQueue()

    with patch.object(fallback_queue, "get_pool", return_value=None):
        with patch("asyncio.create_task") as mock_create_task:
            job_id = await fallback_queue.enqueue_scan(scan_id="test-fallback-scan", fast_mode=True)
            assert job_id is None
            assert mock_create_task.called
