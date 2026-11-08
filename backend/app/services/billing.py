import uuid
from typing import Dict, List, Optional
import razorpay
from app.core.config import settings
from app.core.logging import logger
from app.core.security import verify_hmac_signature
from app.db.models import OrderModel
from app.db.repository import repo
from app.schemas.billing import PlanInfo

PLAN_PRICES = {
    "free": 0,
    "full": 49900,       # ₹499 in paise
    "pro": 149900,      # ₹1,499 in paise
    "business": 499900, # ₹4,999 in paise
}

AVAILABLE_PLANS: List[PlanInfo] = [
    PlanInfo(
        id="free",
        name="Free Starter",
        tagline="Essential perimeter security for personal & testing domains",
        price_inr=0,
        billing_cycle="forever",
        features=[
            "1 automated scan per domain / 7 days",
            "Subdomain discovery & open ports",
            "SSL & security header checks",
            "Deterministic A–F Security Score",
            "Standard English report",
        ],
        popular=False,
    ),
    PlanInfo(
        id="full",
        name="Single Deep Scan",
        tagline="Comprehensive one-time audit with executive PDF & remediation roadmap",
        price_inr=499,
        billing_cycle="one_time",
        features=[
            "One full deep vulnerability scan",
            "Google Gemini AI triage & business impact analysis",
            "Bilingual report (English & Hinglish)",
            "Executive PDF download & email delivery",
            "Actionable fix commands for developers",
        ],
        popular=True,
    ),
    PlanInfo(
        id="pro",
        name="Pro SMB",
        tagline="Continuous protection & unlimited on-demand audits for growing businesses",
        price_inr=1499,
        billing_cycle="monthly",
        features=[
            "Unlimited on-demand security scans",
            "Up to 5 verified domains",
            "Automated weekly recurring monitoring",
            "Priority Gemini 3.8 Flash triage",
            "Executive PDF reports & email alerts",
            "Priority email support",
        ],
        popular=False,
    ),
    PlanInfo(
        id="business",
        name="Agency / Multi-brand",
        tagline="Centralized security monitoring for agencies & multi-store brands",
        price_inr=4999,
        billing_cycle="monthly",
        features=[
            "Up to 25 verified client domains",
            "Unlimited scans & scheduled weekly diffing",
            "Instant change-detection alert emails",
            "Custom PDF reports with agency branding",
            "Dedicated support channel",
        ],
        popular=False,
    ),
]


class BillingService:
    """
    Manages Razorpay checkout order creation, webhook verification,
    and plan upgrade fulfillment.
    """

    def __init__(self):
        self._is_live_configured = (
            bool(settings.RAZORPAY_KEY_ID)
            and not settings.RAZORPAY_KEY_ID.startswith("rzp_test_mock")
            and bool(settings.RAZORPAY_KEY_SECRET)
            and "mock" not in settings.RAZORPAY_KEY_SECRET
        )
        if self._is_live_configured:
            self._client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        else:
            self._client = None

    async def create_order(
        self,
        user_id: str,
        plan: str,
        domain_id: Optional[str] = None,
    ) -> OrderModel:
        """
        Creates an order with Razorpay and records it in the database.
        """
        if plan not in PLAN_PRICES or plan == "free":
            raise ValueError(f"Invalid plan for order creation: {plan}")

        amount = PLAN_PRICES[plan]
        currency = "INR"

        if self._is_live_configured and self._client:
            try:
                order_payload = {
                    "amount": amount,
                    "currency": currency,
                    "receipt": f"rcpt_{uuid.uuid4().hex[:10]}",
                    "notes": {
                        "user_id": user_id,
                        "plan": plan,
                        "domain_id": domain_id or "",
                    },
                }
                rzp_order = self._client.order.create(data=order_payload)
                rzp_order_id = rzp_order["id"]
            except Exception as e:
                logger.error(f"Razorpay order creation failed: {e}; falling back to test order.")
                rzp_order_id = f"order_mock_{uuid.uuid4().hex[:14]}"
        else:
            rzp_order_id = f"order_mock_{uuid.uuid4().hex[:14]}"

        order = await repo.create_order(
            user_id=user_id,
            razorpay_order_id=rzp_order_id,
            plan=plan,
            amount=amount,
            currency=currency,
            domain_id=domain_id,
        )
        logger.info(f"Created order {order.id} ({rzp_order_id}) for user {user_id} - Plan: {plan}")
        return order

    def verify_webhook(self, payload_bytes: bytes, signature: str) -> bool:
        """
        Validates HMAC-SHA256 signature from Razorpay webhook header.
        """
        secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            logger.warning("No RAZORPAY_WEBHOOK_SECRET configured; rejecting webhook.")
            return False
        return verify_hmac_signature(
            payload=payload_bytes,
            signature=signature,
            secret=secret,
        )

    async def process_webhook_event(self, event_data: dict) -> dict:
        """
        Processes payment events and fulfills plan upgrades.
        """
        event_name = event_data.get("event", "")
        payload = event_data.get("payload", {})
        logger.info(f"Processing Razorpay webhook event: {event_name}")

        if event_name in ("payment.captured", "order.paid"):
            payment_obj = payload.get("payment", {}).get("entity", {})
            order_id = payment_obj.get("order_id")
            payment_id = payment_obj.get("id")

            if not order_id and "order" in payload:
                order_id = payload["order"]["entity"].get("id")

            if not order_id:
                return {"status": "ignored", "reason": "No order_id found in event"}

            order = await repo.get_order_by_razorpay_id(order_id)
            if not order:
                logger.warning(f"Webhook received for unknown Razorpay order {order_id}")
                return {"status": "not_found", "order_id": order_id}

            # Mark order as paid
            await repo.update_order_payment(
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id or f"pay_mock_{uuid.uuid4().hex[:8]}",
                status="paid",
            )

            # Upgrade user plan
            await repo.update_user_plan(
                user_id=order.user_id,
                plan=order.plan,
            )
            logger.info(f"User {order.user_id} upgraded to plan '{order.plan}' via order {order_id}")
            return {
                "status": "processed",
                "event": event_name,
                "order_id": order_id,
                "plan": order.plan,
                "user_id": order.user_id,
            }

        return {"status": "ignored", "event": event_name}


billing_service = BillingService()
