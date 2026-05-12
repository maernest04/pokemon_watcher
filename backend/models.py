from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column()
    discord_channel_id: Mapped[str | None] = mapped_column(nullable=True)
    ebay_app_id: Mapped[str | None] = mapped_column(nullable=True)
    ebay_client_secret: Mapped[str | None] = mapped_column(nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_approved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    search_queries: Mapped[list["SearchQuery"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    query_string: Mapped[str] = mapped_column()
    pokemon_name: Mapped[str | None] = mapped_column(nullable=True)
    set_name: Mapped[str | None] = mapped_column(nullable=True)
    card_number: Mapped[str | None] = mapped_column(nullable=True)
    grading_type: Mapped[str] = mapped_column(default="ungraded")  # ungraded, graded, both
    language: Mapped[str] = mapped_column(default="english")  # english, japanese
    listing_type: Mapped[str] = mapped_column(default="buy_it_now")
    pokedata_url: Mapped[str | None] = mapped_column(nullable=True)
    manual_market_price: Mapped[float | None] = mapped_column(nullable=True)
    min_price: Mapped[float | None] = mapped_column(nullable=True)
    max_price: Mapped[float | None] = mapped_column(nullable=True)
    deal_threshold: Mapped[float | None] = mapped_column(nullable=True)
    check_interval_mins: Mapped[int] = mapped_column(default=5)
    last_polled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="search_queries")
    seen_listings: Mapped[list["SeenListing"]] = relationship(
        back_populates="search_query", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="search_query", cascade="all, delete-orphan"
    )


class SeenListing(Base):
    __tablename__ = "seen_listings"
    __table_args__ = (
        UniqueConstraint("search_query_id", "ebay_item_id", name="uq_seen_query_item"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    search_query_id: Mapped[str] = mapped_column(
        ForeignKey("search_queries.id"), index=True
    )
    ebay_item_id: Mapped[str] = mapped_column()
    first_seen_at: Mapped[datetime] = mapped_column(default=_utcnow)

    search_query: Mapped["SearchQuery"] = relationship(back_populates="seen_listings")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    search_query_id: Mapped[str] = mapped_column(
        ForeignKey("search_queries.id"), index=True
    )
    ebay_item_id: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    listing_price: Mapped[float] = mapped_column()
    listing_url: Mapped[str] = mapped_column()
    image_url: Mapped[str | None] = mapped_column(nullable=True)
    market_price: Mapped[float | None] = mapped_column(nullable=True)
    pct_below_market: Mapped[float | None] = mapped_column(nullable=True)
    sent_at: Mapped[datetime] = mapped_column(default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="alerts")
    search_query: Mapped["SearchQuery"] = relationship(back_populates="alerts")


class PriceCache(Base):
    __tablename__ = "price_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    card_query: Mapped[str] = mapped_column(unique=True, index=True)
    market_price: Mapped[float | None] = mapped_column(nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(nullable=True)
