import asyncio
import socket
from typing import Optional
from urllib.parse import urlparse, urlunparse
from arq.connections import ArqRedis, RedisSettings, create_pool
from app.core.config import settings
from app.core.logging import logger


_resolved_redis_settings: Optional[RedisSettings] = None


def get_redis_settings(url: Optional[str] = None) -> RedisSettings:
    """
    Parses REDIS_URL into ARQ RedisSettings.
    Automatically resolves 'redis' hostname to '127.0.0.1' when running on a host
    environment outside Docker where the container name is not resolvable.
    """
    global _resolved_redis_settings
    if url is None and _resolved_redis_settings is not None:
        return _resolved_redis_settings

    import os
    raw_url = url or settings.REDIS_URL
    parsed = urlparse(raw_url)
    if parsed.hostname == "redis":
        # If not inside a docker container, map to localhost immediately without DNS wait
        if not os.path.exists("/.dockerenv") and not os.environ.get("RUNNING_IN_DOCKER"):
            netloc = parsed.netloc.replace("redis", "127.0.0.1")
            raw_url = urlunparse(parsed._replace(netloc=netloc))
        else:
            try:
                socket.gethostbyname("redis")
            except (socket.gaierror, socket.timeout):
                netloc = parsed.netloc.replace("redis", "127.0.0.1")
                raw_url = urlunparse(parsed._replace(netloc=netloc))

    rs = RedisSettings.from_dsn(raw_url)
    if url is None:
        _resolved_redis_settings = rs
    return rs


class ScanQueue:
    """
    Job dispatcher for background security scans.
    Enqueues jobs to Redis via ARQ for persistent, decoupled worker processing.
    Falls back gracefully to in-process execution in lightweight test environments if Redis is unavailable.
    """

    def __init__(self):
        self._pool: Optional[ArqRedis] = None
        self._lock = asyncio.Lock()

    async def get_pool(self) -> Optional[ArqRedis]:
        """Returns the active ARQ Redis connection pool, initializing it if necessary."""
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    try:
                        self._pool = await create_pool(get_redis_settings())
                    except Exception as e:
                        logger.warning(f"Could not connect to Redis pool: {e}")
                        return None
        return self._pool

    async def enqueue_scan(
        self,
        scan_id: str,
        timeout_seconds: int = 1200,
        fast_mode: bool = False,
    ) -> Optional[str]:
        """
        Enqueues a scan job into the Redis queue via ARQ.
        Uses deterministic job_id (f"scan_{scan_id}") to prevent duplicate runs.
        """
        logger.info(f"Enqueuing scan job {scan_id}...")
        pool = await self.get_pool()
        if pool:
            try:
                job = await pool.enqueue_job(
                    "run_scan_job",
                    scan_id=scan_id,
                    timeout_seconds=timeout_seconds,
                    fast_mode=fast_mode,
                    _job_id=f"scan_{scan_id}",
                )
                if job:
                    logger.info(f"Scan job {scan_id} enqueued into Redis with job_id: {job.job_id}")
                    return job.job_id
                else:
                    logger.info(f"Scan job {scan_id} already exists in queue (deduplicated)")
                    return f"scan_{scan_id}"
            except Exception as e:
                logger.error(f"Failed to enqueue scan {scan_id} to Redis: {e}. Falling back to in-process task.")

        # Fallback for environments where Redis is not running (e.g. lightweight unit tests)
        logger.warning(f"Running scan {scan_id} via in-process asyncio task fallback.")
        from app.worker.pipeline.orchestrator import execute_scan_pipeline

        asyncio.create_task(
            execute_scan_pipeline(
                scan_id=scan_id,
                timeout_seconds=timeout_seconds,
                fast_mode=fast_mode,
            )
        )
        return None

    async def close(self) -> None:
        """Closes the ARQ Redis connection pool."""
        if self._pool:
            try:
                await self._pool.aclose()
            except Exception as e:
                logger.debug(f"Error closing Redis pool: {e}")
            finally:
                self._pool = None


queue = ScanQueue()
