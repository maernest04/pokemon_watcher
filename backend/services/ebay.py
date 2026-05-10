import os
import base64
import time
from typing import Any
import requests

from models import SearchQuery

# Cache for OAuth token
_token_cache = {
    "token": None,
    "expiry": 0
}

def _get_oauth_token() -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expiry"] - 60:
        return _token_cache["token"]

    app_id = os.environ.get("EBAY_APP_ID")
    cert_id = os.environ.get("EBAY_CLIENT_SECRET")
    
    if not app_id or not cert_id:
        raise RuntimeError("eBay credentials (EBAY_APP_ID/EBAY_CLIENT_SECRET) not configured")

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
    _token_cache["token"] = data["access_token"]
    _token_cache["expiry"] = now + data["expires_in"]
    
    return _token_cache["token"]

def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def search_listings(search_query: SearchQuery) -> list[dict[str, Any]]:
    token = _get_oauth_token()
    
    app_id = os.environ.get("EBAY_APP_ID", "")
    is_sandbox = "SBX" in app_id
    base_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search" if is_sandbox else "https://api.ebay.com/buy/browse/v1/item_summary/search"
    
    params = {
        "q": search_query.query_string,
        "sort": "newly_listed",
        "limit": 20
    }
    
    filters = []
    
    # Only USA listings
    filters.append("itemLocationCountry:US")
    
    # Grading Filter
    if search_query.grading_type == "ungraded":
        filters.append("-title:(PSA,BGS,CGC,Grade,Graded)")
    elif search_query.grading_type == "graded":
        filters.append("title:(PSA,BGS,CGC,Grade,Graded)")
    
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
    
    # Condition Filter (Ungraded)
    if search_query.is_graded:
        filters.append("conditionIds:{4000}")
        
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
