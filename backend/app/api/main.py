from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.middleware.rate_limiter import RateLimitMiddleware
from app.api.middleware.security_headers import SecurityHeadersMiddleware
from app.api.routers import billing, domains, health, monitoring, reports, scans
from app.core.config import settings
from app.core.logging import logger
from app.core.sentry import init_sentry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation: strictly refuse to start if dev token bypass is enabled outside development
    if settings.ENABLE_DEV_TOKEN_BYPASS and settings.ENVIRONMENT not in ("development", "test"):
        fatal_msg = (
            f"FATAL: ENABLE_DEV_TOKEN_BYPASS is set to True, but ENVIRONMENT is '{settings.ENVIRONMENT}'. "
            "Server startup aborted: dev-token bypass is strictly forbidden in staging or production."
        )
        logger.critical(fatal_msg)
        raise RuntimeError(fatal_msg)

    logger.info("Starting datasecurely Scanner API...")
    init_sentry()
    yield
    from app.services.queue import queue
    await queue.close()
    logger.info("Stopping datasecurely Scanner API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="datasecurely Scanner API",
        description="One-click, AI-assisted website security scanner for Indian SMBs",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware Stack
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include core routers
    app.include_router(health.router)
    app.include_router(domains.router)
    app.include_router(scans.router)
    app.include_router(reports.router)
    app.include_router(billing.router)
    app.include_router(monitoring.router)

    return app


app = create_app()

