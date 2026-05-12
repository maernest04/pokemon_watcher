import base64
import re
import time
from typing import Any
import requests

from models import SearchQuery

# Simple cache for OAuth tokens keyed by (app_id, cert_id)
_token_cache = {}

def _get_oauth_token(app_id: str, cert_id: str) -> str:
    if not app_id or not cert_id:
        raise RuntimeError("eBay credentials are not set. Add your eBay App ID and Client Secret in Settings.")

    cache_key = (app_id, cert_id)
    now = time.time()
    
    cached = _token_cache.get(cache_key)
    if cached and now < cached["expiry"] - 60:
        return cached["token"]

    auth_str = f"{app_id}:{cert_id}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    # Use sandbox URL if SBX is in the app_id
    is_sandbox = "SBX" in app_id
    token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if is_sandbox else "https://api.ebay.com/identity/v1/oauth2/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_auth}"
    }
    
    payload = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    
    response = requests.post(token_url, headers=headers, data=payload)
    response.raise_for_status()
    
    data = response.json()
    _token_cache[cache_key] = {
        "token": data["access_token"],
        "expiry": now + data["expires_in"]
    }
    
    return data["access_token"]

def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def search_listings(
    search_query: SearchQuery,
    app_id: str,
    cert_id: str,
) -> list[dict[str, Any]]:
    token = _get_oauth_token(app_id, cert_id)

    is_sandbox = "SBX" in app_id
    base_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search" if is_sandbox else "https://api.ebay.com/buy/browse/v1/item_summary/search"
    
    # Construct query from pokemon_name, set_name, and card_number
    query_parts = []
    if search_query.pokemon_name:
        query_parts.append(search_query.pokemon_name)
    if search_query.set_name:
        query_parts.append(search_query.set_name)
    if search_query.card_number:
        query_parts.append(search_query.card_number)
    
    if query_parts:
        full_query = " ".join(query_parts)
    else:
        # Fallback to query_string if specific fields are empty
        full_query = search_query.query_string

    params = {
        "q": full_query,
        "sort": "newly_listed",
        "limit": 20,
        "category_ids": "261032"
    }

    aspects: list[str] = []
    grading = getattr(search_query, "grading_type", "both")
    if grading == "graded":
        aspects.append("Graded:{Yes}")
    elif grading == "ungraded":
        aspects.append("Graded:{No}")
        params["q"] = str(params.get("q", "")) + " -psa -bgs -cgc -sgc -graded"

    language = getattr(search_query, "language", "english")
    if language == "japanese":
        aspects.append("Language:{Japanese}")
    elif language == "english":
        aspects.append("Language:{English}")

    if aspects:
        params["aspect_filter"] = "categoryId:261032," + ",".join(aspects)
    
    filters = []
    
    # Only USA listings
    filters.append("itemLocationCountry:US")
    
    
    # Buying Options (Listing Type)
    if search_query.listing_type == "buy_it_now":
        filters.append("buyingOptions:{FIXED_PRICE}")
    elif search_query.listing_type == "auction":
        filters.append("buyingOptions:{AUCTION}")
    # "both" means no buyingOptions filter
    
    # Price Filter
    if search_query.min_price is not None or search_query.max_price is not None:
        min_p = search_query.min_price or 0
        max_p = search_query.max_price or 999999
        filters.append(f"price:[{min_p}..{max_p}],priceCurrency:USD")
    
    if filters:
        params["filter"] = ",".join(filters)
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    
    response = requests.get(base_url, headers=headers, params=params)
    
    if response.status_code != 200:
        error_data = response.json()
        error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown error")
        raise RuntimeError(f"eBay Browse API error: {error_msg}")
        
    data = response.json()
    items = data.get("itemSummaries", [])
    
    listings = []
    for item in items:
        title = item.get("title", "").lower()
        if grading == "ungraded":
            # Match whole words to prevent matching Pokemon names like "Capsakid"
            if re.search(r'\b(psa|bgs|cgc|sgc|graded)\b', title):
                continue

        # Determine normalized type
        options = item.get("buyingOptions", [])
        if "AUCTION" in options:
            normalized_type = "auction"
        else:
            normalized_type = "buy_it_now"
            
        listings.append({
            "ebay_item_id": item.get("itemId"),
            "title": item.get("title"),
            "price": _to_float(item.get("price", {}).get("value")),
            "url": item.get("itemWebUrl"),
            "image_url": item.get("image", {}).get("imageUrl"),
            "listing_type": normalized_type,
            "created_at_raw": item.get("itemCreationDate")
        })
        
    return listings
