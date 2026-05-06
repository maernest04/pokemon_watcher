from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import SearchQuery, User

router = APIRouter(prefix="/api/searches", tags=["searches"])


class SearchQueryCreate(BaseModel):
    query_string: str = Field(min_length=1, max_length=512)
    is_graded: bool = False
    character_name: str | None = Field(default=None, max_length=256)
    listing_type: Literal["buy_it_now", "auction"] = "buy_it_now"
    min_price: float | None = None
    max_price: float | None = None
    deal_threshold: float | None = None
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
    is_graded: bool | None = None
    character_name: str | None = Field(default=None, max_length=256)
    listing_type: Literal["buy_it_now", "auction"] | None = None
    min_price: float | None = None
    max_price: float | None = None
    deal_threshold: float | None = None
    is_active: bool | None = None


class SearchQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query_string: str
    is_graded: bool
    character_name: str | None
    listing_type: Literal["buy_it_now", "auction"]
    min_price: float | None
    max_price: float | None
    deal_threshold: float | None
    is_active: bool
    created_at: datetime


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
    return rows


@router.post("", response_model=SearchQueryResponse, status_code=status.HTTP_201_CREATED)
def create_search(
    body: SearchQueryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sq = SearchQuery(
        user_id=user.id,
        query_string=body.query_string,
        is_graded=body.is_graded,
        character_name=body.character_name,
        listing_type=body.listing_type,
        min_price=body.min_price,
        max_price=body.max_price,
        deal_threshold=body.deal_threshold,
        is_active=body.is_active,
    )
    db.add(sq)
    db.commit()
    db.refresh(sq)
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
