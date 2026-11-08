from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from app.db.models import ScanModel
from app.db.repository import repo
from app.schemas.finding import Finding
from app.worker.monitoring.alerts import evaluate_and_dispatch_monitoring_alerts
from app.worker.monitoring.diff import compare_grades, compute_and_save_scan_diff
from app.worker.monitoring.scheduler import run_monitoring_cycle

AUTH_HEADERS = {"Authorization": "Bearer test-token-monuser-mon@example.com"}
USER_ID = "monuser"


@pytest.fixture
def base_domain():
    return "test-mon-store.in"


def make_finding(template_id: str, severity: str, fp: str) -> Finding:
    return Finding(
        source_tool="custom-headers",
        template_id=template_id,
        title=f"Test Finding {template_id}",
        severity=severity,
        host="test-mon-store.in",
        fingerprint=fp,
    )


@pytest.mark.asyncio
async def test_compare_grades():
    assert compare_grades("B", "A") == "improved"
    assert compare_grades("B", "C") == "degraded"
    assert compare_grades("B", "B") == "unchanged"
    assert compare_grades(None, "A") == "first_scan"


@pytest.mark.asyncio
async def test_diff_engine_first_scan():
    domain = await repo.create_domain(user_id=USER_ID, hostname="first-scan.in", verify_token="tok1")
    scan = await repo.create_scan(domain_id=domain.id, user_id=USER_ID, hostname=domain.hostname, profile="free")
    scan.status = "completed"
    scan.grade = "B"

    findings = [make_finding("f1", "medium", "fp1"), make_finding("f2", "low", "fp2")]
    await repo.save_findings(scan.id, findings)

    diff = await compute_and_save_scan_diff(current_scan=scan)
    assert diff.grade_change == "first_scan"
    assert diff.new_findings_count == 2
    assert diff.resolved_findings_count == 0
    assert diff.persistent_findings_count == 0


@pytest.mark.asyncio
async def test_diff_engine_new_and_resolved_findings():
    domain = await repo.create_domain(user_id=USER_ID, hostname="diff-test.in", verify_token="tok2")

    # Scan 1
    scan1 = await repo.create_scan(domain_id=domain.id, user_id=USER_ID, hostname=domain.hostname, profile="free")
    scan1.status = "completed"
    scan1.grade = "B"
    scan1.finished_at = datetime.now(timezone.utc) - timedelta(days=2)
    await repo.save_findings(scan1.id, [make_finding("f1", "medium", "fp1"), make_finding("f2", "low", "fp2")])

    # Scan 2: f1 resolved, f2 persistent, f3 newly detected
    scan2 = await repo.create_scan(domain_id=domain.id, user_id=USER_ID, hostname=domain.hostname, profile="free")
    scan2.status = "completed"
    scan2.grade = "C"
    scan2.finished_at = datetime.now(timezone.utc)
    await repo.save_findings(scan2.id, [make_finding("f2", "low", "fp2"), make_finding("f3", "high", "fp3")])

    diff = await compute_and_save_scan_diff(current_scan=scan2, previous_scan=scan1)
    assert diff.grade_change == "degraded"
    assert diff.new_findings_count == 1
    assert diff.resolved_findings_count == 1
    assert diff.persistent_findings_count == 1

    diff_data = diff.diff_json
    assert diff_data["new_findings"][0]["fingerprint"] == "fp3"
    assert diff_data["resolved_findings"][0]["fingerprint"] == "fp1"
    assert diff_data["persistent_findings"][0]["fingerprint"] == "fp2"


@pytest.mark.asyncio
async def test_alert_dispatching_on_degraded_critical():
    domain = await repo.create_domain(user_id=USER_ID, hostname="alert-test.in", verify_token="tok3")
    scan = await repo.create_scan(domain_id=domain.id, user_id=USER_ID, hostname=domain.hostname, profile="monitor")
    scan.status = "completed"
    scan.grade = "D"

    # Diff containing a new critical finding
    diff_payload = {
        "new_findings": [{"title": "RCE vulnerability", "severity": "critical"}],
        "resolved_findings": [],
        "persistent_findings": [],
    }
    diff = await repo.save_scan_diff(
        scan_id=scan.id,
        domain_id=domain.id,
        previous_scan_id="scan-prev-1",
        grade_change="degraded",
        new_findings_count=1,
        resolved_findings_count=0,
        persistent_findings_count=0,
        diff_json=diff_payload,
    )

    alert_result = await evaluate_and_dispatch_monitoring_alerts(scan=scan, diff=diff, domain=domain)
    assert alert_result["alert_dispatched"] is True
    assert alert_result["type"] == "degraded_or_critical_alert"


@pytest.mark.asyncio
async def test_alert_dispatching_on_resolved_notice():
    domain = await repo.create_domain(user_id=USER_ID, hostname="resolved-test.in", verify_token="tok4")
    scan = await repo.create_scan(domain_id=domain.id, user_id=USER_ID, hostname=domain.hostname, profile="monitor")
    scan.status = "completed"
    scan.grade = "A"

    # Diff with 0 new, 2 resolved
    diff_payload = {
        "new_findings": [],
        "resolved_findings": [{"title": "Missing HSTS", "severity": "medium"}],
        "persistent_findings": [],
    }
    diff = await repo.save_scan_diff(
        scan_id=scan.id,
        domain_id=domain.id,
        previous_scan_id="scan-prev-2",
        grade_change="improved",
        new_findings_count=0,
        resolved_findings_count=1,
        persistent_findings_count=0,
        diff_json=diff_payload,
    )

    alert_result = await evaluate_and_dispatch_monitoring_alerts(scan=scan, diff=diff, domain=domain)
    assert alert_result["alert_dispatched"] is True
    assert alert_result["type"] == "resolution_notice"


@pytest.mark.asyncio
async def test_api_toggle_monitoring(async_client: AsyncClient):
    # 1. Create domain (pending)
    domain = await repo.create_domain(user_id=USER_ID, hostname="toggle-test.in", verify_token="tok5")

    # 2. Toggle should fail while unverified
    res_unverified = await async_client.post(
        "/api/v1/monitoring/toggle",
        json={"domain_id": domain.id, "enabled": True},
        headers=AUTH_HEADERS,
    )
    assert res_unverified.status_code == 403

    # 3. Verify domain
    await repo.update_domain_status(domain.id, "verified", verified_at=datetime.now(timezone.utc))

    # 4. Toggle should succeed
    res_verified = await async_client.post(
        "/api/v1/monitoring/toggle",
        json={"domain_id": domain.id, "enabled": True},
        headers=AUTH_HEADERS,
    )
    assert res_verified.status_code == 200
    assert res_verified.json()["is_monitored"] is True

    # 5. Toggle off
    res_off = await async_client.post(
        "/api/v1/monitoring/toggle",
        json={"domain_id": domain.id, "enabled": False},
        headers=AUTH_HEADERS,
    )
    assert res_off.status_code == 200
    assert res_off.json()["is_monitored"] is False


@pytest.mark.asyncio
async def test_api_get_scan_diff(async_client: AsyncClient):
    domain = await repo.create_domain(user_id=USER_ID, hostname="api-diff.in", verify_token="tok6")
    scan = await repo.create_scan(domain_id=domain.id, user_id=USER_ID, hostname=domain.hostname, profile="free")
    scan.status = "completed"
    scan.grade = "A"

    findings = [make_finding("f1", "low", "fp_api")]
    await repo.save_findings(scan.id, findings)

    res = await async_client.get(f"/api/v1/monitoring/diff/{scan.id}", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["scan_id"] == scan.id
    assert data["new_findings_count"] == 1
    assert data["grade_change"] == "first_scan"


@pytest.mark.asyncio
async def test_scheduler_monitoring_cycle():
    # Setup pro user and domain
    pro_user = "pro-scheduler-user"
    await repo.get_or_create_user(user_id=pro_user, email="pro@sched.in", plan="pro")
    domain = await repo.create_domain(user_id=pro_user, hostname="sched-mon.in", verify_token="tok7")
    await repo.update_domain_status(domain.id, "verified", verified_at=datetime.now(timezone.utc))
    await repo.update_domain_monitoring(domain.id, is_monitored=True, user_id=pro_user)

    # Run cycle
    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
        mock_dns.return_value = ["93.184.216.34"]
        cycle = await run_monitoring_cycle(days_due=7)
        assert cycle["status"] == "completed"
        assert cycle["scans_enqueued"] >= 1
