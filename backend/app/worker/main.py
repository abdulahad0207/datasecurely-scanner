import sys
import redis.asyncio as aioredis
from arq.connections import RedisSettings
from arq.worker import check_health, run_worker
from app.core.config import settings
from app.core.logging import logger
from app.core.sentry import init_sentry
from app.services.queue import get_redis_settings
from app.worker.pipeline.orchestrator import execute_scan_pipeline


async def run_scan_job(
    ctx: dict,
    scan_id: str,
    timeout_seconds: int = 1200,
    fast_mode: bool = False,
) -> None:
    """
    ARQ worker entrypoint for security scan jobs.
    Executes the full scan pipeline (scope guard -> recon -> scan -> score -> AI triage -> report).
    """
    logger.info(f"[ARQ Worker] Picked up scan job: {scan_id} (timeout={timeout_seconds}s, fast_mode={fast_mode})")
    try:
        await execute_scan_pipeline(scan_id=scan_id, timeout_seconds=timeout_seconds, fast_mode=fast_mode)
        logger.info(f"[ARQ Worker] Successfully completed scan job: {scan_id}")
    except Exception as e:
        logger.error(f"[ARQ Worker] Scan job {scan_id} encountered an error: {e}", exc_info=True)
        raise


async def startup(ctx: dict) -> None:
    """Worker startup hook: verifies Redis connection and initializes monitoring."""
    logger.info("Initializing datasecurely Scanner Worker...")
    init_sentry()

    rs = get_redis_settings()
    logger.info(f"Target Redis Queue: {rs.host}:{rs.port}/{rs.database}")

    # Ping Redis to verify connectivity immediately at startup
    client = aioredis.from_url(f"redis://{rs.host}:{rs.port}/{rs.database}")
    try:
        await client.ping()
        logger.info("Worker successfully connected to Redis. Ready to consume scan jobs.")
    except Exception as e:
        logger.critical(f"Worker failed to connect to Redis at {rs.host}:{rs.port}: {e}")
        raise
    finally:
        await client.aclose()


async def shutdown(ctx: dict) -> None:
    """Worker graceful shutdown hook."""
    logger.info("Worker stopped successfully. Terminating gracefully.")


class WorkerSettings:
    """ARQ Worker configuration."""
    functions = [run_scan_job]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 1200  # 20 minutes default hard timeout
    max_jobs = 10
    health_check_interval = 10  # Writes health check heartbeat every 10 seconds
    health_check_key = "arq:health-check"


def main():
    if "--check" in sys.argv:
        sys.exit(check_health(WorkerSettings))

    logger.info("Starting datasecurely ARQ Worker daemon...")
    run_worker(WorkerSettings)


if __name__ == "__main__":
    main()
