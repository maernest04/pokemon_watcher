from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Alert, User

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    id: int
    search_query_id: UUID
    ebay_item_id: str
    title: str
    listing_price: float
    listing_url: str
    image_url: str | None
    market_price: float | None
    pct_below_market: float | None
    sent_at: datetime


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Alert)
        .where(Alert.user_id == user.id)
        .order_by(Alert.sent_at.desc())
        .limit(20)
    ).all()
    return rows
