import os
from typing import Any

from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection as Finding

from models import SearchQuery


def _listing_type_value(listing_type: str) -> str:
    if listing_type == "auction":
        return "Auction"
    return "FixedPrice"


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def search_listings(search_query: SearchQuery) -> list[dict[str, Any]]:
    app_id = os.environ.get("EBAY_APP_ID")
    if not app_id:
        raise RuntimeError("EBAY_APP_ID is not configured")
    api = Finding(appid=app_id, config_file=None)
    item_filters: list[dict[str, Any]] = [
        {"name": "ListingType", "value": _listing_type_value(search_query.listing_type)}
    ]
    if search_query.min_price is not None:
        item_filters.append({"name": "MinPrice", "value": str(search_query.min_price)})
    if search_query.max_price is not None:
        item_filters.append({"name": "MaxPrice", "value": str(search_query.max_price)})
    if search_query.is_graded:
        item_filters.append({"name": "Condition", "value": "3000"})
    try:
        response = api.execute(
            "findItemsByKeywords",
            {
                "keywords": search_query.query_string,
                "sortOrder": "StartTimeNewest",
                "itemFilter": item_filters,
                "paginationInput": {"entriesPerPage": 20},
                "outputSelector": ["SellerInfo", "PictureURLSuperSize"],
            },
        )
    except ConnectionError as exc:
        raise RuntimeError(f"eBay request failed: {exc}") from exc
    data = response.dict()
    raw_items = data.get("searchResult", {}).get("item", [])
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    listings: list[dict[str, Any]] = []
    for item in raw_items:
        selling = item.get("sellingStatus", {})
        current = selling.get("currentPrice", {})
        price = _to_float(current.get("value"))
        listing_info = item.get("listingInfo", {})
        listing_type = listing_info.get("listingType")
        if listing_type == "Auction":
            normalized_type = "auction"
        else:
            normalized_type = "buy_it_now"
        listings.append(
            {
                "ebay_item_id": item.get("itemId"),
                "title": item.get("title"),
                "price": price,
                "url": item.get("viewItemURL"),
                "image_url": item.get("pictureURLSuperSize") or item.get("galleryURL"),
                "listing_type": normalized_type,
            }
        )
    return listings
