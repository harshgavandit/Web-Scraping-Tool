from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.logging import logger
from app.database.session import SessionLocal
from app.services.collection_service import collection_service

_scheduler = BackgroundScheduler(timezone="UTC")


def scheduled_collection_job():
    """Periodic job to collect and analyze brand mentions."""
    logger.info("Executing scheduled brand listening collection job...")
    db = SessionLocal()
    try:
        results = collection_service.run_pipeline(db=db, brand_id=1, source="all")
        total_added = sum(r.records_added for r in results)
        logger.info(f"Scheduled collection finished successfully. Added {total_added} new posts.")
    except Exception as e:
        logger.error(f"Scheduled collection job failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start background scheduler if not already running."""
    if not _scheduler.running:
        interval = max(settings.COLLECTION_INTERVAL_MINUTES, 5)
        _scheduler.add_job(
            scheduled_collection_job,
            trigger=IntervalTrigger(minutes=interval),
            id="periodic_brand_collection",
            name="Periodic Brand Social Collection",
            replace_existing=True
        )
        _scheduler.start()
        logger.info(f"Background scheduler started with interval {interval} minutes.")


def shutdown_scheduler():
    """Safely stop background scheduler."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")
