import json
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import logger
from app.db.repository import repo
from app.schemas.billing import (
    AccountBillingResponse,
    BillingOrderItem,
    CreateOrderRequest,
    CreateOrderResponse,
    PlanInfo,
    QuotaStatusResponse,
    WebhookResponse,
)
from app.schemas.user import AuthUser
from app.services.billing import AVAILABLE_PLANS, billing_service

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.get("/plans", response_model=List[PlanInfo])
async def list_plans() -> List[PlanInfo]:
    """
    Returns public pricing tiers and feature comparisons.
    """
    return AVAILABLE_PLANS


@router.get("/account", response_model=AccountBillingResponse)
async def get_account_billing(
    current_user: AuthUser = Depends(get_current_user),
) -> AccountBillingResponse:
    """
    Returns current user's active plan, renewal date (if on a paid plan), and billing history.
    """
    user = await repo.get_user(current_user.id)
    plan = user.plan if user else (current_user.plan or "free")
    orders = await repo.list_orders_by_user(current_user.id)

    renewal_date = None
    if plan and plan.lower() not in ("free", "none"):
        paid_orders = [o for o in orders if o.status == "paid"]
        if paid_orders and paid_orders[0].created_at:
            renewal_date = paid_orders[0].created_at + timedelta(days=30)

    order_items = [
        BillingOrderItem(
            id=o.id,
            razorpay_order_id=o.razorpay_order_id,
            razorpay_payment_id=o.razorpay_payment_id,
            plan=o.plan,
            amount=o.amount,
            currency=o.currency,
            status=o.status,
            created_at=o.created_at,
        )
        for o in orders
    ]

    return AccountBillingResponse(
        plan=plan,
        renewal_date=renewal_date,
        orders=order_items,
    )


@router.get("/quota", response_model=QuotaStatusResponse)
async def check_quota(
    domain_id: str = Query(..., description="Target domain ID to evaluate quota against"),
    current_user: AuthUser = Depends(get_current_user),
) -> QuotaStatusResponse:
    """
    Checks if a scan can be launched for a given domain under current user's plan.
    """
    user = await repo.get_user(current_user.id)
    plan = user.plan if user else "free"

    allowed, reason, wait_seconds = await repo.check_scan_quota(
        user_id=current_user.id,
        domain_id=domain_id,
    )

    return QuotaStatusResponse(
        allowed=allowed,
        reason=reason,
        plan=plan,
        wait_seconds=wait_seconds,
        domain_id=domain_id,
    )


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_checkout_order(
    payload: CreateOrderRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> CreateOrderResponse:
    """
    Initiates a Razorpay order for purchasing a plan or a single deep scan.
    """
    try:
        order = await billing_service.create_order(
            user_id=current_user.id,
            plan=payload.plan,
            domain_id=payload.domain_id,
        )
        return CreateOrderResponse(
            order_id=order.id,
            razorpay_order_id=order.razorpay_order_id,
            amount=order.amount,
            currency=order.currency,
            key_id=settings.RAZORPAY_KEY_ID,
            plan=order.plan,
            domain_id=order.domain_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/webhook", response_model=WebhookResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
) -> WebhookResponse:
    """
    Receives and cryptographically verifies Razorpay webhook events to fulfill upgrades.
    """
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header",
        )

    raw_body = await request.body()
    is_valid = billing_service.verify_webhook(
        payload_bytes=raw_body,
        signature=x_razorpay_signature,
    )

    if not is_valid:
        logger.warning("Rejected Razorpay webhook with invalid HMAC signature.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    try:
        event_data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload in webhook body",
        )

    result = await billing_service.process_webhook_event(event_data)
    return WebhookResponse(
        status="ok",
        message=f"Webhook handled: {result.get('status')}",
    )
