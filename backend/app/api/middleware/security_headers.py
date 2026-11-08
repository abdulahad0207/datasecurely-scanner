from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.config import settings


def build_csp_policy() -> str:
    """
    Constructs a robust Content-Security-Policy header string based on environment settings:
    1. Gated 'unsafe-eval': included strictly in development, never in staging or production.
    2. Razorpay integration: script-src includes checkout.razorpay.com; frame-src includes api.razorpay.com.
    3. Dynamic origins: reads API and frontend origins dynamically from settings rather than hardcoded URLs.
    4. Next.js hydration: includes 'unsafe-inline' for React Server Component hydration streaming.
       (Follow-up planned to implement cryptographic per-request nonces before public launch).
    """
    # 1. Script sources
    script_sources = ["'self'", "https://checkout.razorpay.com", "'unsafe-inline'"]
    if settings.ENVIRONMENT == "development":
        script_sources.append("'unsafe-eval'")
    script_src = " ".join(script_sources)

    # 2. Dynamic origins from settings
    supabase_origin = settings.SUPABASE_URL.rstrip("/")
    supabase_wss = supabase_origin.replace("https://", "wss://").replace("http://", "ws://")
    frontend_origin = settings.FRONTEND_URL.rstrip("/")
    api_origin = settings.api_base_url

    # Connect sources: local app origins, Supabase, and Razorpay endpoints
    connect_origins = {
        "'self'",
        supabase_origin,
        supabase_wss,
        frontend_origin,
        api_origin,
        "https://api.razorpay.com",
        "https://lumberjack.razorpay.com",
    }
    connect_src = " ".join(sorted(connect_origins))

    directives = [
        "default-src 'self'",
        f"script-src {script_src}",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "frame-src 'self' https://api.razorpay.com",
        f"connect-src {connect_src}",
    ]

    return "; ".join(directives) + ";"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Appends standard defensive HTTP security headers to all API responses.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = build_csp_policy()
        return response
