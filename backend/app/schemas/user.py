from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    plan: str = "free"


class UserResponse(UserBase):
    id: str
    razorpay_customer_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthUser(BaseModel):
    """Authenticated user context extracted from JWT."""
    id: str
    email: str
    plan: str = "free"

