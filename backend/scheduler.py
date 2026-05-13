import asyncio
import os
from datetime import datetime, timedelta, timezone

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import SessionLocal
from models import Alert, SearchQuery, SeenListing, User
from services.pokedata import update_market_price_cache
from services.alerts import poll_search_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def poll_active_searches_job() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Find searches that are active, for approved users, and due for a poll
        # A search is due if (now - last_polled_at) >= check_interval_mins
        # Or if last_polled_at is None (first time)
        searches = db.scalars(
            select(SearchQuery)
            .join(User)
            .where(SearchQuery.is_active.is_(True))
            .where(User.is_approved.is_(True))
        ).all()
        
        due_search_ids = []
        for s in searches:
            if s.last_polled_at is None:
                due_search_ids.append(s.id)
                continue
                
            elapsed = (now - s.last_polled_at.replace(tzinfo=timezone.utc)).total_seconds() / 60.0
            if elapsed >= s.check_interval_mins - 0.1: # Small buffer for timing jitter
                due_search_ids.append(s.id)

        if due_search_ids:
            logger.info(f"Dynamic Poll: {len(due_search_ids)} searches are due for checking.")
            for search_id in due_search_ids:
                poll_search_query(search_id)
    finally:
        db.close()


async def refresh_market_prices_job() -> None:
    db = SessionLocal()
    try:
        # Find all active searches that need market price updates
        searches = db.scalars(
            select(SearchQuery)
            .where(SearchQuery.is_active.is_(True))
            .where(SearchQuery.language == "english")
        ).all()
        
        # Group by (query_string, pokedata_url) to avoid redundant scrapes
        to_refresh = []
        seen = set()
        for s in searches:
            key = (s.query_string.strip().lower(), s.pokedata_url)
            if key not in seen:
                seen.add(key)
                to_refresh.append(s)
    finally:
        db.close()

    for index, search in enumerate(to_refresh):
        db = SessionLocal()
        try:
            update_market_price_cache(
                search.query_string, 
                db, 
                override_url=search.pokedata_url
            )
        except Exception as e:
            logger.error(f"Error refreshing market price for '{search.query_string}': {e}")
        finally:
            db.close()
        
        if index < len(to_refresh) - 1:
            # Rate limit to avoid being blocked by PokeDATA
            await asyncio.sleep(60)


async def cleanup_old_data_job() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # 1. Clean up seen listings older than 14 days
        seen_cutoff = now - timedelta(days=14)
        db.query(SeenListing).filter(SeenListing.first_seen_at < seen_cutoff).delete()
        
        # 2. Clean up alerts older than 30 days
        alert_cutoff = now - timedelta(days=30)
        db.query(Alert).filter(Alert.sent_at < alert_cutoff).delete()
        
        db.commit()
        logger.info("Daily cleanup completed: Removed stale seen_listings and alerts.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during data cleanup: {e}")
    finally:
        db.close()


def create_scheduler() -> AsyncIOScheduler:
    tz_name = os.environ.get("TZ", "America/Los_Angeles").strip().lstrip(":")
    try:
        timezone_obj = pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        timezone_obj = pytz.UTC
        logger.warning(f"Unknown timezone '{tz_name}', defaulting to UTC")
    scheduler = AsyncIOScheduler(timezone=timezone_obj)
    scheduler.add_job(
        poll_active_searches_job,
        "interval",
        minutes=1,
        id="poll_active_searches",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_market_prices_job,
        "cron",
        hour=0,
        minute=0,
        id="refresh_market_prices",
        replace_existing=True,
    )
    scheduler.add_job(
        cleanup_old_data_job,
        "cron",
        hour=3,
        minute=0,
        id="cleanup_old_data",
        replace_existing=True,
    )
    return scheduler
