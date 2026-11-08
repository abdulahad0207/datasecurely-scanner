from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PlanInfo(BaseModel):
    id: str
    name: str
    tagline: str
    price_inr: int
    billing_cycle: str  # one_time, monthly, yearly
    features: List[str]
    popular: bool = False

    model_config = ConfigDict(from_attributes=True)


class CreateOrderRequest(BaseModel):
    plan: str = Field(..., description="Plan ID: 'full', 'pro', or 'business'")
    domain_id: Optional[str] = Field(None, description="Optional target domain ID for single-scan purchases")


class CreateOrderResponse(BaseModel):
    order_id: str
    razorpay_order_id: str
    amount: int  # in paise
    currency: str
    key_id: str
    plan: str
    domain_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuotaStatusResponse(BaseModel):
    allowed: bool
    reason: str
    plan: str
    wait_seconds: Optional[int] = None
    domain_id: Optional[str] = None


class WebhookResponse(BaseModel):
    status: str
    message: str


class BillingOrderItem(BaseModel):
    id: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    plan: str
    amount: int  # in paise
    currency: str = "INR"
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AccountBillingResponse(BaseModel):
    plan: str
    renewal_date: Optional[datetime] = None
    orders: List[BillingOrderItem]

