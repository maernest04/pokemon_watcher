from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import SearchQuery, User

router = APIRouter(prefix="/api/searches", tags=["searches"])


def _refresh_market_price_async(query_string: str, pokedata_url: str | None = None, search_query_id: str | None = None) -> None:
    from database import SessionLocal
    from services.pokedata import update_market_price_cache

    db = SessionLocal()
    try:
        update_market_price_cache(query_string, db, override_url=pokedata_url, search_query_id=search_query_id)
    finally:
        db.close()


class SearchQueryCreate(BaseModel):
    query_string: str = Field(min_length=1, max_length=512)
    pokemon_name: str | None = Field(default=None, max_length=256)
    set_name: str | None = Field(default=None, max_length=256)
    card_number: str | None = Field(default=None, max_length=128)
    grading_type: Literal["ungraded", "graded", "both"] = "both"
    language: Literal["english", "japanese"] = "english"
    check_interval_mins: int = Field(default=5, ge=1, le=1440)
    listing_type: Literal["buy_it_now", "auction", "both"] = "buy_it_now"
    pokedata_url: str | None = None
    manual_market_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def check_price_range(self):
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price cannot be greater than max_price")
        return self


class SearchQueryUpdate(BaseModel):
    query_string: str | None = Field(default=None, min_length=1, max_length=512)
    pokemon_name: str | None = Field(default=None, max_length=256)
    set_name: str | None = Field(default=None, max_length=256)
    card_number: str | None = Field(default=None, max_length=128)
    grading_type: Literal["ungraded", "graded", "both"] | None = None
    language: Literal["english", "japanese"] | None = None
    check_interval_mins: int | None = Field(default=None, ge=1, le=1440)
    listing_type: Literal["buy_it_now", "auction", "both"] | None = None
    pokedata_url: str | None = None
    manual_market_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    is_active: bool | None = None


class SearchQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query_string: str
    pokemon_name: str | None
    set_name: str | None
    card_number: str | None
    grading_type: str
    language: Literal["english", "japanese"]
    check_interval_mins: int
    listing_type: Literal["buy_it_now", "auction", "both"]
    pokedata_url: str | None
    manual_market_price: float | None
    min_price: float | None
    max_price: float | None
    is_active: bool
    created_at: datetime
    market_price: float | None = None


def _get_owned_search(
    db: Session,
    user: User,
    search_id: UUID,
) -> SearchQuery:
    sq = db.get(SearchQuery, str(search_id))
    if sq is None or sq.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
        )
    return sq


@router.get("/", response_model=list[SearchQueryResponse])
def list_searches(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(SearchQuery)
        .where(SearchQuery.user_id == user.id)
        .order_by(SearchQuery.created_at.desc())
    ).all()
    
    from scheduler import get_cached_market_price
    for row in rows:
        if row.manual_market_price is not None:
            row.market_price = row.manual_market_price
        else:
            row.market_price = get_cached_market_price(db, row.query_string)
        
    return rows


@router.post("", response_model=SearchQueryResponse, status_code=status.HTTP_201_CREATED)
def create_search(
    body: SearchQueryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sq = SearchQuery(
        user_id=user.id,
        query_string=body.query_string,
        pokemon_name=body.pokemon_name,
        set_name=body.set_name,
        card_number=body.card_number,
        grading_type=body.grading_type,
        language=body.language,
        check_interval_mins=body.check_interval_mins,
        listing_type=body.listing_type,
        pokedata_url=body.pokedata_url,
        manual_market_price=body.manual_market_price,
        min_price=body.min_price,
        max_price=body.max_price,
        is_active=body.is_active,
    )
    db.add(sq)
    db.commit()
    db.refresh(sq)

    if sq.language == "english":
        background_tasks.add_task(_refresh_market_price_async, sq.query_string, sq.pokedata_url, str(sq.id))

    from scheduler import get_cached_market_price
    if sq.manual_market_price is not None:
        sq.market_price = sq.manual_market_price
    else:
        sq.market_price = get_cached_market_price(db, sq.query_string)

    return sq


@router.get("/{search_id}", response_model=SearchQueryResponse)
def get_search(
    search_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_owned_search(db, user, search_id)


@router.patch("/{search_id}", response_model=SearchQueryResponse)
def update_search(
    search_id: UUID,
    body: SearchQueryUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sq = _get_owned_search(db, user, search_id)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(sq, key, value)
    if (
        sq.min_price is not None
        and sq.max_price is not None
        and sq.min_price > sq.max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price",
        )
    db.add(sq)
    db.commit()
    db.refresh(sq)

    # If the user updated the pokedata_url, trigger an immediate refresh
    if body.pokedata_url and sq.language == "english":
        background_tasks.add_task(_refresh_market_price_async, sq.query_string, sq.pokedata_url, str(sq.id))
    from scheduler import get_cached_market_price
    if sq.manual_market_price is not None:
        sq.market_price = sq.manual_market_price
    else:
        sq.market_price = get_cached_market_price(db, sq.query_string)
    return sq


@router.post("/{search_id}/refresh-market", response_model=SearchQueryResponse)
def refresh_market_price(
    search_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sq = _get_owned_search(db, user, search_id)
    if sq.language == "english":
        from services.pokedata import update_market_price_cache
        update_market_price_cache(sq.query_string, db, override_url=sq.pokedata_url, search_query_id=str(sq.id))
        db.refresh(sq)
    from scheduler import get_cached_market_price
    if sq.manual_market_price is not None:
        sq.market_price = sq.manual_market_price
    else:
        sq.market_price = get_cached_market_price(db, sq.query_string)
    return sq


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search(
    search_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sq = _get_owned_search(db, user, search_id)
    db.delete(sq)
    db.commit()
    return None
