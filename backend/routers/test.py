from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import SearchQuery, User
from services.discord_bot import send_embed
from services.ebay import search_listings
from services.pokedata import scrape_market_price

router = APIRouter(prefix="/api/test", tags=["test"])


class EbayTestBody(BaseModel):
    search_query_id: UUID


class PokeDataTestBody(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    debug_browser: bool = False


@router.post("/discord")
def test_discord(user: User = Depends(get_current_user)) -> dict[str, Any]:
    if not user.discord_channel_id:
        return {
            "success": False,
            "message": "discord_channel_id is not set for this user",
            "data": None,
        }
    try:
        send_embed(
            user.discord_channel_id,
            title="Pokemon Watcher Test",
            description="Discord test message from /api/test/discord",
            fields=[
                {"name": "User", "value": user.username, "inline": True},
                {"name": "Status", "value": "ok", "inline": True},
            ],
        )
    except RuntimeError as exc:
        return {"success": False, "message": str(exc), "data": None}
    return {"success": True, "message": "Test Discord message sent", "data": None}


@router.post("/pokedata")
def test_pokedata(
    body: PokeDataTestBody,
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = scrape_market_price(body.query, debug_browser=body.debug_browser)
    if data.get("error"):
        return {
            "success": False,
            "message": data["error"],
            "data": data,
        }
    if data.get("market_price") is None:
        return {
            "success": False,
            "message": "Could not resolve market price",
            "data": data,
        }
    return {
        "success": True,
        "message": "Market price scraped",
        "data": data,
    }


@router.post("/ebay")
def test_ebay(
    body: EbayTestBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    search_query = db.get(SearchQuery, str(body.search_query_id))
    if search_query is None or search_query.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found",
        )
    try:
        listings = search_listings(search_query)
    except RuntimeError as exc:
        return {"success": False, "message": str(exc), "data": []}
    return {
        "success": True,
        "message": f"Fetched {len(listings)} listings",
        "data": listings,
    }
