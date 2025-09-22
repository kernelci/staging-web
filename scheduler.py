"""Background scheduler setup for automatic staging runs."""

import logging
from datetime import datetime, timedelta

from fastapi_crons import Crons

from database import SessionLocal
from db_constraints import (
    validate_single_running_staging,
    enforce_single_running_staging,
)
from discord_webhook import discord_webhook
from models import (
    InitiatedVia,
    StagingRun,
    StagingRunStatus,
)
from scheduler_config import (
    SCHEDULER_AUTO_KERNEL_TREE,
    SCHEDULER_SKIP_WINDOW_SECONDS,
    SCHEDULER_USERNAME,
)
from scheduler_user import ensure_scheduler_user

logger = logging.getLogger(__name__)

CRON_EXPRESSION = "0 0,8,16 * * *"  # 00:00, 08:00, 16:00 UTC


async def _run_scheduled_staging() -> None:
    """Execute a staging run if cooldown and concurrency constraints allow it."""
    db = SessionLocal()
    try:
        scheduler_user = ensure_scheduler_user(db)

        now = datetime.utcnow()
        cooldown_start = now - timedelta(seconds=SCHEDULER_SKIP_WINDOW_SECONDS)

        # Skip if another user triggered a run recently
        recent_manual_run = (
            db.query(StagingRun)
            .filter(StagingRun.start_time >= cooldown_start)
            .filter(StagingRun.user_id != scheduler_user.id)
            .order_by(StagingRun.start_time.desc())
            .first()
        )
        if recent_manual_run:
            logger.info(
                "Skipping scheduled staging: recent run #%s by %s at %s",
                recent_manual_run.id,
                recent_manual_run.user.username,
                recent_manual_run.start_time,
            )
            return

        # Skip if a run is in progress
        running_staging = validate_single_running_staging(db)
        if running_staging:
            logger.info(
                "Skipping scheduled staging: run #%s is currently %s",
                running_staging.id,
                running_staging.status.value,
            )
            return

        staging_run = StagingRun(
            user_id=scheduler_user.id,
            status=StagingRunStatus.RUNNING,
            initiated_via=InitiatedVia.CRON,
            kernel_tree=SCHEDULER_AUTO_KERNEL_TREE,
        )
        db.add(staging_run)
        db.flush()

        if not enforce_single_running_staging(db, staging_run.id):
            logger.warning(
                "Scheduled staging run #%s cancelled due to concurrency enforcement",
                staging_run.id,
            )
            db.rollback()
            return

        db.commit()
        db.refresh(staging_run)
        logger.info("Scheduled staging run #%s started", staging_run.id)

        logger.info("Using virtual scheduler user '%s'", SCHEDULER_USERNAME)

        if discord_webhook:
            try:
                await discord_webhook.send_staging_start(
                    SCHEDULER_USERNAME, staging_run.id
                )
            except Exception as exc:
                logger.warning(
                    "Discord notification failed for scheduler run #%s: %s",
                    staging_run.id,
                    exc,
                )

    except Exception as exc:
        logger.error("Scheduler job failed: %s", exc)
        db.rollback()
    finally:
        db.close()


def register_cron_jobs(crons: Crons) -> None:
    """Attach scheduled staging jobs to the provided cron scheduler."""

    @crons.cron(CRON_EXPRESSION, name="staging_scheduler")
    async def scheduled_staging_job():
        await _run_scheduled_staging()

    logger.info("Registered scheduled staging job for expression '%s'", CRON_EXPRESSION)
