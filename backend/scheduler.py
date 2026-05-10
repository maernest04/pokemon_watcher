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


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _resolve_market_price(search_query: SearchQuery, db) -> float | None:
    if search_query.manual_market_price is not None:
        return search_query.manual_market_price
    normalized_query = _normalize_query(search_query.query_string)
    cache = db.scalar(
        select(PriceCache).where(PriceCache.card_query == normalized_query)
    )
    if cache is None:
        return None
    return cache.market_price


def _should_send_alert(
    listing: dict,
    market_price: float | None,
    deal_threshold: float | None,
) -> tuple[bool, float | None]:
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
    
    # Filter out suspiciously low prices (potential fakes/scams)
    # If price is below 60% of market (i.e. > 40% off), ignore it.
    if pct_below_market > 0.4:
        return False, pct_below_market

    if deal_threshold is None or pct_below_market >= deal_threshold:
        return True, pct_below_market
    return False, pct_below_market


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

    fields = [
        {"name": "Listing Price", "value": f"${price:.2f}" if price is not None else "Unknown", "inline": True},
        {"name": "Market Price", "value": comparison_text, "inline": True},
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
        user = db.get(User, search_query.user_id)
        if user is None:
            return
        try:
            listings = search_listings(search_query)
        except Exception:
            return
        market_price = _resolve_market_price(search_query, db)
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
                continue
            db.add(
                SeenListing(
                    search_query_id=search_query.id,
                    ebay_item_id=ebay_item_id,
                )
            )
            db.commit()
            should_send, pct_below_market = _should_send_alert(
                listing,
                market_price,
                search_query.deal_threshold,
            )
            if not should_send:
                continue
            try:
                _send_listing_alert(
                    user,
                    search_query,
                    listing,
                    market_price,
                    pct_below_market,
                )
            except Exception:
                continue
            db.add(
                Alert(
                    user_id=user.id,
                    search_query_id=search_query.id,
                    ebay_item_id=ebay_item_id,
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
    finally:
        db.close()


async def poll_active_searches_job() -> None:
    db = SessionLocal()
    try:
        search_ids = db.scalars(
            select(SearchQuery.id).where(SearchQuery.is_active.is_(True))
        ).all()
    finally:
        db.close()
    for search_id in search_ids:
        poll_search_query(search_id)


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
        minutes=5,
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
