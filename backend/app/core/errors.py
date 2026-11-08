from typing import Any, Optional
from fastapi import HTTPException, status


class AppError(Exception):
    """Base application exception."""
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or "INTERNAL_ERROR"


class ScopeViolationError(AppError):
    """Raised when target domain or IP violates scope guardrails."""
    def __init__(self, message: str):
        super().__init__(message, code="SCOPE_VIOLATION")


class VerificationRequiredError(AppError):
    """Raised when scan requested for an unverified domain."""
    def __init__(self, message: str = "Domain ownership must be verified before scanning."):
        super().__init__(message, code="VERIFICATION_REQUIRED")


class QuotaExceededError(AppError):
    """Raised when plan scan quota is exceeded."""
    def __init__(self, message: str = "Scan quota exceeded for current billing period."):
        super().__init__(message, code="QUOTA_EXCEEDED")
