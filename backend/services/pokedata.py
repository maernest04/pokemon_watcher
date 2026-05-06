from pathlib import Path
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urljoin

import httpx
import requests
from bs4 import BeautifulSoup

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0",
]

_MARKET_PATTERNS = [
    re.compile(r"Market Price[:\s]*\$?\s*(\d(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)", re.I),
    re.compile(r"\"marketPrice\"\s*:\s*([\d.]+)", re.I),
    re.compile(r"\"MarketPrice\"\s*:\s*([\d.]+)", re.I),
]


def _pick_user_agent(card_query: str) -> str:
    return _USER_AGENTS[hash(card_query.strip()) % len(_USER_AGENTS)]


def _extract_cards_from_soup(soup: BeautifulSoup) -> list[tuple[str, float | None]]:
    cards: list[tuple[str, float | None]] = []
    seen: set[str] = set()
    card_containers = soup.find_all("div", class_=re.compile(r"MuiCard-root"))
    for container in card_containers:
        a = container.find("a", href=True)
        if not a or "/card/" not in a["href"]:
            continue
        full_url = urljoin("https://www.pokedata.io", a["href"])
        if full_url in seen:
            continue
        seen.add(full_url)
        price: float | None = None
        price_el = container.find("span", string=re.compile(r"\$"))
        if not price_el:
            price_el = container.find(lambda tag: tag.name == "span" and "$" in tag.get_text())
        if price_el:
            price_text = price_el.get_text(strip=True)
            match = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)", price_text)
            if match:
                try:
                    price = float(match.group(1).replace(",", ""))
                except ValueError:
                    pass
        cards.append((full_url, price))
    return cards


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
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/card/" not in href:
            continue
        card_url = urljoin("https://www.pokedata.io", href)
        container = a.find_parent("div", class_=re.compile(r"MuiCard-root|MuiPaper-root"))
        scope = container if container else a
        price_el = scope.find(
            lambda tag: tag.name == "span"
            and tag.get("class")
            and any("MuiTypography-avenir_16_700" in cls for cls in tag.get("class", []))
            and "$" in tag.get_text(" ", strip=True)
        )
        if price_el:
            m = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)", price_el.get_text(" ", strip=True))
            if m:
                try:
                    return float(m.group(1).replace(",", "")), card_url
                except ValueError:
                    pass
    return None, None


def _browser_debug_capture(url: str) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"error": f"Playwright import failed: {exc}"}
    out_dir = Path(__file__).resolve().parent.parent / "tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    html_path = out_dir / f"pokedata-debug-{stamp}.html"
    shot_path = out_dir / f"pokedata-debug-{stamp}.png"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(4000)
            html = page.content()
            html_path.write_text(html)
            page.screenshot(path=str(shot_path), full_page=True)
            browser.close()
    except Exception as exc:
        return {"error": f"Playwright capture failed: {exc}"}
    return {
        "html_path": str(html_path),
        "screenshot_path": str(shot_path),
    }


def scrape_market_price(card_query: str, *, debug_browser: bool = False) -> dict[str, Any]:
    cq = card_query.strip()
    if not cq:
        return {"market_price": None, "product_url": None, "error": "Empty query"}
    search_url = f"https://www.pokedata.io/cards?q={quote_plus(cq)}"
    headers = {
        "User-Agent": _pick_user_agent(cq),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    debug: dict[str, Any] = {"pokedata_search_url": search_url}
    if debug_browser:
        debug["pokedata_browser"] = _browser_debug_capture(search_url)
    try:
        r = requests.get(search_url, headers=headers, timeout=30)
        r.raise_for_status()
    except requests.RequestException as exc:
        return {"market_price": None, "product_url": None, "error": f"Request failed: {exc}", "debug": debug}
    soup = BeautifulSoup(r.text, "html.parser")
    tbody = soup.find("tbody", class_=re.compile(r"MuiTableBody-root"))
    if not tbody:
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
        return {"market_price": None, "product_url": search_url, "error": "No results found on pokedata.io", "debug": debug}
    price_els = tbody.find_all(class_=re.compile(r"avenir_24_700"))
    if len(price_els) < 2:
        return {"market_price": None, "product_url": search_url, "error": "Could not find market price in results", "debug": debug}
    market_raw = price_els[1].get_text(strip=True)
    match = re.search(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)", market_raw)
    if not match:
        return {"market_price": None, "product_url": search_url, "error": f"Could not parse price from: {market_raw}", "debug": debug}
    try:
        price = float(match.group(1).replace(",", ""))
    except ValueError:
        return {"market_price": None, "product_url": search_url, "error": f"Float conversion failed for: {market_raw}", "debug": debug}
    return {"market_price": price, "product_url": search_url, "error": None, "debug": debug}
