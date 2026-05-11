from pathlib import Path
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0",
]


def _pick_user_agent(card_query: str) -> str:
    return _USER_AGENTS[hash(card_query.strip()) % len(_USER_AGENTS)]


def _playwright_fetch_html(url: str) -> tuple[str | None, str | None]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return None, f"Playwright import failed: {exc}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(4000)
            html = page.content()
            browser.close()
            return html, None
    except Exception as exc:
        return None, f"Playwright fetch failed: {exc}"


def _extract_first_card_price_from_rendered_html(html: str) -> tuple[float | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    # Try to find a card link first
    card_link = soup.find("a", href=lambda x: x and "/card/" in x)
    if not card_link:
        return None, None
    
    card_url = urljoin("https://www.pokedata.io", card_link["href"])
    
    # Look for a container that might have the price
    container = card_link.find_parent("div", class_=re.compile(r"MuiCard-root|MuiPaper-root"))
    scope = container if container else soup
    
    # Search for text that looks like a price near a "Market" label
    all_text = scope.get_text(" ", strip=True)
    # Match something like "Market Price $123.45" or just "$123.45"
    price_match = re.search(r"Market\s*(?:Price)?\s*\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", all_text, re.IGNORECASE)
    if not price_match:
        # Fallback: just look for the first dollar amount in the scope
        price_match = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", all_text)
        
    if price_match:
        try:
            return float(price_match.group(1).replace(",", "")), card_url
        except ValueError:
            pass
            
    return None, card_url


def scrape_market_price(card_query: str, *, debug_browser: bool = False) -> dict[str, Any]:
    cq = card_query.strip()
    if not cq:
        return {"market_price": None, "product_url": None, "error": "Empty query"}
    
    # Try to use a more direct search URL
    search_url = f"https://www.pokedata.io/cards?q={quote_plus(cq)}"
    headers = {
        "User-Agent": _pick_user_agent(cq),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    debug: dict[str, Any] = {"pokedata_search_url": search_url}
    
    try:
        r = requests.get(search_url, headers=headers, timeout=15)
        r.raise_for_status()
        
        # Check if the response contains actual card data or just a shell
        if "MuiTable-root" in r.text or "avenir_24_700" in r.text:
            soup = BeautifulSoup(r.text, "html.parser")
            # Try to find market price by looking for cells/labels
            price = None
            
            # Find all currency-looking text
            all_text = soup.get_text(" ", strip=True)
            # PokeData often lists Low, Market, High. Market is usually the middle one.
            # But let's look for the specific "Market" label in table headers or cells
            market_match = re.search(r"Market\s*(?:Price)?\s*\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", all_text, re.IGNORECASE)
            if market_match:
                price = float(market_match.group(1).replace(",", ""))
            
            if price:
                return {"market_price": price, "product_url": search_url, "error": None, "debug": debug}
    except Exception as exc:
        debug["requests_exception"] = str(exc)

    # Fallback to Playwright if requests fails or doesn't find the price
    rendered_html, rendered_err = _playwright_fetch_html(search_url)
    if rendered_html:
        rendered_price, rendered_url = _extract_first_card_price_from_rendered_html(rendered_html)
        if rendered_price is not None:
            return {
                "market_price": rendered_price,
                "product_url": rendered_url or search_url,
                "error": None,
                "debug": debug,
            }
    
    if rendered_err:
        debug["rendered_exception"] = rendered_err
        
    return {
        "market_price": None, 
        "product_url": search_url, 
        "error": "Could not resolve market price from PokeDATA. Check if the query is specific enough.", 
        "debug": debug
    }


def update_market_price_cache(card_query: str, db: Any) -> float | None:
    from datetime import datetime, timezone
    from sqlalchemy import select
    from models import PriceCache

    cq = " ".join(card_query.strip().lower().split())
    if not cq:
        return None

    try:
        result = scrape_market_price(cq)
    except Exception:
        return None

    market_price = result.get("market_price")
    if market_price is not None:
        cache = db.scalar(select(PriceCache).where(PriceCache.card_query == cq))
        if cache is None:
            cache = PriceCache(card_query=cq)
            db.add(cache)
        cache.market_price = market_price
        cache.last_updated = datetime.now(timezone.utc)
        db.commit()
    
    return market_price
