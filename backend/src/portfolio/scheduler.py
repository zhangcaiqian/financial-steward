"""Background scheduler for rebalance batches."""
from __future__ import annotations

import asyncio
import os
from typing import Optional

from .rebalance_plan import mark_due_batches_ready


async def batch_scheduler_loop(interval_seconds: int = 60) -> None:
    while True:
        try:
            mark_due_batches_ready()
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)


def start_batch_scheduler() -> Optional[asyncio.Task]:
    if os.getenv("PORTFOLIO_SCHEDULER_ENABLED", "true").lower() != "true":
        return None
    interval = int(os.getenv("PORTFOLIO_SCHEDULER_INTERVAL", "60"))
    return asyncio.create_task(batch_scheduler_loop(interval))
