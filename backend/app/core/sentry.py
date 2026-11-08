import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from app.core.config import settings
from app.core.logging import logger


def init_sentry() -> bool:
    """
    Initializes Sentry exception tracking for production monitoring.
    Safely no-ops if SENTRY_DSN is not configured.
    """
    if not settings.SENTRY_DSN or "mock" in settings.SENTRY_DSN.lower():
        logger.info("Sentry DSN not configured; running without remote telemetry.")
        return False

    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=0.2 if settings.ENVIRONMENT == "production" else 1.0,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                RedisIntegration(),
            ],
            # Filter client-side 4xx errors from polluting issue tracker
            before_send=_filter_client_exceptions,
        )
        logger.info(f"Sentry initialized successfully for environment: {settings.SENTRY_ENVIRONMENT}")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
        return False


def _filter_client_exceptions(event, hint):
    """Discards expected 4xx client errors from Sentry reports."""
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        status_code = getattr(exc_value, "status_code", None)
        if status_code and status_code < 500:
            return None
    return event
