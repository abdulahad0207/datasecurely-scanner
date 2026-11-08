from typing import Any, Dict, List
from app.core.logging import logger
from app.db.repository import repo
from app.services.queue import queue


async def run_monitoring_cycle(days_due: int = 7) -> Dict[str, Any]:
    """
    Executes a periodic monitoring sweep:
    - Queries all verified domains with active monitoring due for a scan.
    - Validates user subscription tier.
    - Enqueues automated recurring audit jobs.
    """
    logger.info(f"Running automated continuous monitoring cycle (due every {days_due} days)...")
    due_domains = await repo.list_monitored_domains_due(days=days_due)
    enqueued: List[Dict[str, str]] = []

    for domain in due_domains:
        user = await repo.get_user(domain.user_id)
        plan = user.plan if user else "free"

        # Continuous monitoring is enabled for pro, business, and monitor tiers
        if plan not in ("pro", "business", "monitor"):
            logger.info(
                f"Skipping scheduled scan for {domain.hostname}: user plan '{plan}' does not include automated recurring monitoring."
            )
            continue

        try:
            scan = await repo.create_scan(
                domain_id=domain.id,
                user_id=domain.user_id,
                hostname=domain.hostname,
                profile="monitor",
            )
            await queue.enqueue_scan(scan_id=scan.id)
            await repo.update_domain_last_monitored(domain.id)

            enqueued.append({"scan_id": scan.id, "domain": domain.hostname})
            logger.info(f"Scheduled recurring scan {scan.id} enqueued for {domain.hostname}")
        except Exception as e:
            logger.error(f"Failed to enqueue scheduled monitoring scan for {domain.hostname}: {e}")

    return {
        "status": "completed",
        "domains_evaluated": len(due_domains),
        "scans_enqueued": len(enqueued),
        "items": enqueued,
    }
