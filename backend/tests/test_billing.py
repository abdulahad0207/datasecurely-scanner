import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.db.repository import repo

AUTH_HEADERS = {"Authorization": "Bearer test-token-billuser-billing@example.com"}
USER_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "billuser"))


@pytest.mark.asyncio
async def test_list_plans_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/billing/plans")
    assert res.status_code == 200
    plans = res.json()
    assert len(plans) >= 3
    plan_ids = [p["id"] for p in plans]
    assert "free" in plan_ids
    assert "full" in plan_ids
    assert "pro" in plan_ids


@pytest.mark.asyncio
async def test_create_order_authorized(async_client: AsyncClient):
    payload = {"plan": "full"}
    res = await async_client.post(
        "/api/v1/billing/create-order",
        json=payload,
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert "razorpay_order_id" in data
    assert data["amount"] == 49900
    assert data["currency"] == "INR"
    assert data["plan"] == "full"


@pytest.mark.asyncio
async def test_create_order_invalid_plan(async_client: AsyncClient):
    payload = {"plan": "unreal_enterprise"}
    res = await async_client.post(
        "/api/v1/billing/create-order",
        json=payload,
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 400
    assert "invalid plan" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_quota_check_and_enforcement_flow(async_client: AsyncClient):
    from unittest.mock import AsyncMock, patch

    with patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock) as mock_dns:
        mock_dns.return_value = ["93.184.216.34"]

        # 0. Ensure user starts on free plan
        await repo.update_user_plan(user_id=USER_ID, plan="free")

        # 1. Create and verify domain (resolvable to public IP so worker stays in valid scanning/completed state)
        unique_host = f"quota-test-{uuid.uuid4().hex[:6]}.93.184.216.34.nip.io"
        domain = await repo.create_domain(
            user_id=USER_ID,
            hostname=unique_host,
            verify_token="test-token-quota",
        )
        await repo.update_domain_status(
            domain_id=domain.id,
            status="verified",
            verified_at=datetime.now(timezone.utc),
        )

        # 2. Check quota before any scans
        quota_res = await async_client.get(
            f"/api/v1/billing/quota?domain_id={domain.id}",
            headers=AUTH_HEADERS,
        )
        assert quota_res.status_code == 200
        assert quota_res.json()["allowed"] is True

        # 3. Start first scan (should be accepted)
        scan1_res = await async_client.post(
            "/api/v1/scans",
            json={"domain_id": domain.id, "profile": "free"},
            headers=AUTH_HEADERS,
        )
        assert scan1_res.status_code == 202

        # 4. Attempt immediate second scan on same domain under free plan (should be 429)
        scan2_res = await async_client.post(
            "/api/v1/scans",
            json={"domain_id": domain.id, "profile": "free"},
            headers=AUTH_HEADERS,
        )
        assert scan2_res.status_code == 429
        assert "limit reached" in scan2_res.json()["detail"].lower()
        assert "Retry-After" in scan2_res.headers

        # 5. Upgrade user to Pro plan
        await repo.update_user_plan(user_id=USER_ID, plan="pro")

        # 6. Check quota again (should now be allowed)
        quota_res2 = await async_client.get(
            f"/api/v1/billing/quota?domain_id={domain.id}",
            headers=AUTH_HEADERS,
        )
        assert quota_res2.status_code == 200
        assert quota_res2.json()["allowed"] is True

        # 7. Start second scan as Pro user (should now succeed)
        scan3_res = await async_client.post(
            "/api/v1/scans",
            json={"domain_id": domain.id, "profile": "full"},
            headers=AUTH_HEADERS,
        )
        assert scan3_res.status_code == 202


@pytest.mark.asyncio
async def test_webhook_valid_signature_fulfills_upgrade(async_client: AsyncClient):
    webhook_user = "webhook-buyer-user"
    # 1. Create order
    order = await repo.create_order(
        user_id=webhook_user,
        razorpay_order_id="order_rzp_test_12345",
        plan="pro",
        amount=149900,
    )

    # Verify initial user plan is free
    user = await repo.get_or_create_user(user_id=webhook_user, email="buyer@test.in")
    assert user.plan == "free"

    # 2. Craft Razorpay payment.captured webhook payload
    payload_dict = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_987654",
                    "order_id": order.razorpay_order_id,
                    "amount": 149900,
                    "status": "captured",
                }
            }
        },
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    # 3. Compute HMAC-SHA256 signature using test secret
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    # 4. Post to webhook
    res = await async_client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # 5. Assert user is now upgraded to Pro
    updated_user = await repo.get_user(webhook_user)
    assert updated_user is not None
    assert updated_user.plan == "pro"

    # 6. Assert order status is paid
    updated_order = await repo.get_order_by_razorpay_id("order_rzp_test_12345")
    assert updated_order is not None
    assert updated_order.status == "paid"
    assert updated_order.razorpay_payment_id == "pay_test_987654"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected(async_client: AsyncClient):
    payload_bytes = b'{"event": "payment.captured"}'
    res = await async_client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_forged_signature_hex",
        },
    )
    assert res.status_code == 400
    assert "invalid webhook signature" in res.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("plan_tier,amount", [
    ("full", 49900),
    ("pro", 149900),
    ("business", 499900),
])
async def test_webhook_upgrade_to_all_plans_no_constraint_violation(
    async_client: AsyncClient,
    plan_tier: str,
    amount: int,
):
    """
    Verifies that webhook fulfillment upgrades a user to 'full', 'pro', or 'business'
    without triggering a database CHECK constraint violation.
    """
    user_id = f"test-user-upgrade-{plan_tier}"
    order_id = f"order_rzp_{plan_tier}_{uuid.uuid4().hex[:8]}"
    payment_id = f"pay_{plan_tier}_{uuid.uuid4().hex[:8]}"

    # Initial user setup with 'free' plan
    user = await repo.get_or_create_user(user_id=user_id, email=f"{plan_tier}@example.com")
    assert user.plan == "free"

    # Create order for the targeted plan tier
    order = await repo.create_order(
        user_id=user_id,
        razorpay_order_id=order_id,
        plan=plan_tier,
        amount=amount,
    )
    assert order.plan == plan_tier

    # Craft webhook payload
    payload_dict = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                    "status": "captured",
                }
            }
        },
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    # Deliver webhook
    res = await async_client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Assert user upgraded without DB constraint violation
    updated_user = await repo.get_user(user_id)
    assert updated_user is not None
    assert updated_user.plan == plan_tier
