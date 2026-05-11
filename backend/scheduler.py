import asyncio
import os
from datetime import datetime, timezone

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import SessionLocal
from models import Alert, PriceCache, SearchQuery, SeenListing, User
from services.discord_bot import send_embed
from services.ebay import search_listings
from services.pokedata import scrape_market_price, update_market_price_cache


import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def get_cached_market_price(db, query_string: str) -> float | None:
    normalized_query = _normalize_query(query_string)
    cache = db.scalar(
        select(PriceCache).where(PriceCache.card_query == normalized_query)
    )
    return cache.market_price if cache else None


def _resolve_market_price(search_query: SearchQuery, db) -> float | None:
    if search_query.manual_market_price is not None:
        return search_query.manual_market_price
    return get_cached_market_price(db, search_query.query_string)


def _should_send_alert(
    listing: dict,
    market_price: float | None,
    deal_threshold: float | None,
) -> tuple[bool, float | None]:
    # Ignore listings older than 60 minutes to prevent initial spam
    raw_date = listing.get("created_at_raw")
    if raw_date:
        try:
            created_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_mins = (now - created_at).total_seconds() / 60.0
            if age_mins > 60:
                return False, None
        except Exception:
            pass

    if listing.get("listing_type") == "auction":
        return True, None
    listing_price = listing.get("price")
    if listing_price is None:
        return False, None
    if market_price is None:
        return True, None
    if market_price <= 0:
        return False, None
    pct_below_market = (market_price - listing_price) / market_price
    
    # We no longer filter by deal_threshold. 
    # We only filter out suspiciously low prices (spam/scams).
    if pct_below_market is not None and pct_below_market > 0.4:
        return False, pct_below_market

    return True, pct_below_market


def _send_listing_alert(
    user: User,
    search_query: SearchQuery,
    listing: dict,
    market_price: float | None,
    pct_below_market: float | None,
) -> None:
    if not user.discord_channel_id:
        raise RuntimeError("discord_channel_id is not set for this user")
    price = listing.get("price")
    if market_price is None:
        comparison_text = "Market price not available"
    else:
        diff = price - market_price
        pct = (abs(diff) / market_price) * 100
        if diff < 0:
            comparison_text = f"${market_price:.2f} (**{pct:.1f}% below** market)"
        elif diff > 0:
            comparison_text = f"${market_price:.2f} (**{pct:.1f}% above** market)"
        else:
            comparison_text = f"${market_price:.2f} (At market price)"

    # Embed color: Green for deal, Yellow for market, Red for above market
    color = 0x99F0B4 if (pct_below_market or 0) > 0 else 0xF6F7FB
    if pct_below_market is not None and pct_below_market < 0:
        color = 0xF17373

    # Timezone conversion for Discord message
    tz_name = os.environ.get("TZ", "America/Los_Angeles")
    local_tz = pytz.timezone(tz_name)
    now_local = datetime.now(timezone.utc).astimezone(local_tz)
    time_str = now_local.strftime("%I:%M:%S %p")

    # Format the listing creation date
    raw_date = listing.get("created_at_raw")
    listing_time_str = "Unknown"
    if raw_date:
        try:
            # eBay format: 2024-05-10T12:34:56.000Z
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            listing_time_str = dt.astimezone(local_tz).strftime("%I:%M %p")
        except:
            listing_time_str = raw_date

    fields = [
        {"name": "Listing Price", "value": f"${price:.2f}" if price is not None else "Unknown", "inline": True},
        {"name": "Market Price", "value": comparison_text, "inline": True},
        {"name": "Listed At", "value": listing_time_str, "inline": True},
        {"name": "Alert Time", "value": f"{time_str} ({tz_name})", "inline": True},
        {"name": "Search Query", "value": search_query.query_string, "inline": False},
        {"name": "View Listing", "value": f"[Click here to view]({listing.get('url') or ''})", "inline": False},
    ]

    send_embed(
        user.discord_channel_id,
        title="🔥 New Deal Found!" if (pct_below_market or 0) > 0.1 else "New Listing Found",
        description=listing.get("title") or search_query.query_string,
        fields=fields,
        image_url=listing.get("image_url"),
        color=color,
    )


def poll_search_query(search_query_id: str) -> None:
    db = SessionLocal()
    try:
        search_query = db.get(SearchQuery, search_query_id)
        if search_query is None or not search_query.is_active:
            return
        logger.info(f"Polling search: {search_query.query_string} (ID: {search_query.id})")
        user = db.get(User, search_query.user_id)
        if user is None:
            logger.warning(f"User {search_query.user_id} not found for search {search_query.id}")
            return
        try:
            from services.encryption import decrypt_secret
            ebay_app_id = user.ebay_app_id
            ebay_client_secret = decrypt_secret(user.ebay_client_secret)
            
            listings = search_listings(search_query, app_id=ebay_app_id, cert_id=ebay_client_secret)
            logger.info(f"Found {len(listings)} listings on eBay for '{search_query.query_string}'")
        except Exception as e:
            logger.error(f"Error searching eBay for '{search_query.query_string}': {e}")
            return
        market_price = _resolve_market_price(search_query, db)
        seen_count = 0
        new_listings = []

        for listing in listings:
            ebay_item_id = listing.get("ebay_item_id")
            if not ebay_item_id:
                continue
            existing_seen = db.scalar(
                select(SeenListing).where(
                    SeenListing.search_query_id == search_query.id,
                    SeenListing.ebay_item_id == ebay_item_id,
                )
            )
            if existing_seen is not None:
                seen_count += 1
                continue

            # This is a new listing
            new_listings.append(listing)
            db.add(
                SeenListing(
                    search_query_id=search_query.id,
                    ebay_item_id=ebay_item_id,
                )
            )
            db.commit()

        logger.info(f"Results for '{search_query.query_string}': {seen_count} seen, {len(new_listings)} new")
        
        for listing in new_listings:
            logger.info(f"  - NEW: {listing.get('title')} -> {listing.get('url')}")
            
            should_send, pct_below_market = _should_send_alert(
                listing,
                market_price,
                search_query.deal_threshold,
            )
            
            if not should_send:
                if pct_below_market is not None and pct_below_market > 0.4:
                    logger.info(f"    Filtered (SPAM): {pct_below_market*100:.1f}% off")
                elif pct_below_market is not None:
                    logger.info(f"    Skipping (not a deal): {pct_below_market*100:.1f}% off")
                else:
                    logger.info(f"    Skipping (too old or no price)")
                continue
                
            listing_date = listing.get("created_at_raw", "Unknown date")
            logger.info(f"    MATCH! [Listed: {listing_date}] Sending Discord alert...")
            try:
                _send_listing_alert(
                    user,
                    search_query,
                    listing,
                    market_price,
                    pct_below_market,
                )
            except Exception as e:
                logger.error(f"    Error sending Discord alert: {e}")
                continue

            db.add(
                Alert(
                    user_id=user.id,
                    search_query_id=search_query.id,
                    ebay_item_id=listing.get("ebay_item_id"),
                    title=listing.get("title") or search_query.query_string,
                    listing_price=listing.get("price") or 0.0,
                    listing_url=listing.get("url") or "",
                    image_url=listing.get("image_url"),
                    market_price=market_price,
                    pct_below_market=pct_below_market,
                    sent_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
            
        # Update last_polled_at
        search_query.last_polled_at = datetime.now(timezone.utc)
        db.add(search_query)
        db.commit()
    finally:
        db.close()


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
        queries = db.scalars(
            select(SearchQuery.query_string).where(SearchQuery.is_active.is_(True))
        ).all()
        unique_queries: list[str] = []
        seen_queries: set[str] = set()
        for query in queries:
            normalized_query = _normalize_query(query)
            if not normalized_query or normalized_query in seen_queries:
                continue
            seen_queries.add(normalized_query)
            unique_queries.append(normalized_query)
    finally:
        db.close()
    for index, card_query in enumerate(unique_queries):
        db = SessionLocal()
        try:
            update_market_price_cache(card_query, db)
        except Exception:
            pass
        finally:
            db.close()
        
        if index < len(unique_queries) - 1:
            await asyncio.sleep(60)


def create_scheduler() -> AsyncIOScheduler:
    tz_name = os.environ.get("TZ", "America/Los_Angeles")
    timezone_obj = pytz.timezone(tz_name)
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
    return scheduler
