from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
import redis.asyncio as aioredis
from app.core.logging import logger
from app.services.queue import get_redis_settings
from arq.worker import async_check_health

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    redis: Optional[str] = None
    worker: Optional[str] = None


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Returns the operational status of the API service and connected worker subsystem."""
    rs = get_redis_settings()
    redis_status = "unknown"
    worker_status = "offline"

    try:
        client = aioredis.from_url(f"redis://{rs.host}:{rs.port}/{rs.database}")
        await client.ping()
        redis_status = "connected"
        await client.aclose()

        try:
            worker_code = await async_check_health(rs, health_check_key="arq:health-check")
            worker_status = "healthy" if worker_code == 0 else "standby"
        except Exception:
            worker_status = "offline"
    except Exception as e:
        logger.debug(f"Redis health check probe failed: {e}")
        redis_status = "unreachable"

    return HealthResponse(
        status="ok",
        service="api",
        version="0.1.0",
        redis=redis_status,
        worker=worker_status,
    )
