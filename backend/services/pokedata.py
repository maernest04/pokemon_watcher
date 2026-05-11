from pathlib import Path
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup


def _playwright_fetch_html(url: str) -> tuple[str | None, str | None]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return None, f"Playwright import failed: {exc}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.route(
                re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|woff|woff2|ttf|otf|mp4)(\?|$)", re.IGNORECASE),
                lambda route: route.abort(),
            )
            # Use networkidle to ensure all async price data is loaded
            page.goto(url, wait_until="networkidle", timeout=45000)
            try:
                # Wait for at least one card or price element to appear
                page.wait_for_selector("a[href*='/card/'], span[class*='avenir'], span[class*='mui-style']", timeout=15000)
            except Exception:
                pass
            html = page.content()
            browser.close()
            return html, None
    except Exception as exc:
        return None, f"Playwright fetch failed: {exc}"


def _extract_first_card_price_from_rendered_html(html: str) -> tuple[float | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    
    # Focus on the body to avoid picking up keywords from meta tags
    body = soup.find("body") or soup
    
    # If we found a card link (for search results page), identify the scope
    card_link = body.find("a", href=lambda x: x and "/card/" in x)
    scope = card_link.find_parent("div", class_=re.compile(r"MuiCard-root|MuiPaper-root")) if card_link else body
    card_url = urljoin("https://www.pokedata.io", card_link["href"]) if card_link else None

    # STRATEGY 1: Look for TCGPlayer specifically (High Priority)
    # Search for "TCGPlayer" or "TCG Player"
    tcg_labels = body.find_all(string=re.compile(r"TCG\s*Player", re.IGNORECASE))
    for label in tcg_labels:
        # Traverse up to find a container and look for a price near this label
        curr = label.parent
        for _ in range(5): # Check up to 5 levels up
            if not curr: break
            price_span = curr.find("span", class_=re.compile(r"avenir_24_700|mui-style-1i0sqsh"))
            if price_span and "$" in price_span.get_text():
                try:
                    val = price_span.get_text().strip().replace("$", "").replace(",", "")
                    return float(val), card_url
                except ValueError:
                    pass
            # Fallback within this container: any dollar amount
            price_match = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", curr.get_text())
            if price_match:
                return float(price_match.group(1).replace(",", "")), card_url
            curr = curr.parent

    # STRATEGY 2: Direct price span check (main price on page)
    # If we are on a card page, the main price often has this specific class
    card_page_price_span = body.find("span", class_=re.compile(r"avenir_24_700"))
    if card_page_price_span and "$" in card_page_price_span.get_text():
        # Check if "eBay" is the label immediately preceding or near this span
        # If so, we might want to keep looking, but usually this is the main Market Price
        try:
            val = card_page_price_span.get_text().strip().replace("$", "").replace(",", "")
            return float(val), card_url
        except ValueError:
            pass

    # STRATEGY 3: Fallback to general Market Price search, but avoid "eBay" if possible
    all_text = scope.get_text(" ", strip=True)
    
    # Try finding "TCGPlayer" in the text and the first price after it
    tcg_index = all_text.lower().find("tcgplayer")
    if tcg_index != -1:
        after_tcg = all_text[tcg_index:]
        price_match = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", after_tcg)
        if price_match:
            return float(price_match.group(1).replace(",", "")), card_url

    # General Market Price search
    price_match = re.search(r"Market\s*(?:Price)?\s*\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", all_text, re.IGNORECASE)
    if not price_match:
        # Last resort: first dollar amount that isn't clearly labeled eBay
        price_match = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", all_text)
        
    if price_match:
        try:
            return float(price_match.group(1).replace(",", "")), card_url
        except ValueError:
            pass
            
    return None, card_url


def scrape_market_price(card_query: str, *, override_url: str | None = None) -> dict[str, Any]:
    cq = card_query.strip()
    
    if override_url:
        search_url = override_url
    else:
        if not cq:
            return {"market_price": None, "product_url": None, "error": "Empty query"}
        search_url = f"https://www.pokedata.io/cards?q={quote_plus(cq)}"

    debug: dict[str, Any] = {"pokedata_url": search_url}

    rendered_html, rendered_err = _playwright_fetch_html(search_url)
    if rendered_html:
        rendered_price, rendered_url = _extract_first_card_price_from_rendered_html(rendered_html)
        if rendered_price is not None:
            # If we used a direct link, use that as product_url.
            # If we searched, rendered_url is the actual card page found.
            final_url = override_url if override_url else (rendered_url or search_url)
            return {
                "market_price": rendered_price,
                "product_url": final_url,
                "error": None,
                "debug": debug,
            }

    if rendered_err:
        debug["rendered_exception"] = rendered_err

    return {
        "market_price": None,
        "product_url": search_url,
        "error": "Could not resolve market price from PokeDATA. Check if the query is specific enough or the link is correct.",
        "debug": debug
    }


def update_market_price_cache(card_query: str, db: Any, *, override_url: str | None = None, search_query_id: str | None = None) -> float | None:
    from datetime import datetime, timezone
    from sqlalchemy import select
    from models import PriceCache, SearchQuery

    cq = " ".join(card_query.strip().lower().split())
    if not cq and not override_url:
        return None

    try:
        result = scrape_market_price(cq, override_url=override_url)
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
        
        # If this was a successful override-based scrape, and we have a search_query_id,
        # remove the override URL from the search record as requested.
        if override_url and search_query_id:
            sq = db.get(SearchQuery, search_query_id)
            if sq:
                sq.pokedata_url = None
                db.add(sq)
                
        db.commit()
    
    return market_price
