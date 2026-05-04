# Pokémon eBay Deal Finder — Full Project Spec
> Ready to paste into Cursor. Written for an AI coding assistant to implement end-to-end.

---

## Project Overview

A web application that monitors eBay listings for Pokémon cards, sends Discord alerts for new deals, compares prices against TCGPlayer market data, and optionally scores card centering from listing photos. Up to ~5 friends share one deployment, each with their own login, dashboard, and Discord channel for alerts.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async-native, great ecosystem for scraping + scheduling |
| Frontend | React + Vite | Component-based, supports rich animations |
| Database | SQLite + SQLAlchemy ORM | Zero-config, file-based, perfect for small shared apps |
| Task Scheduler | APScheduler (AsyncIOScheduler) | In-process cron jobs, no Redis/Celery needed |
| eBay Integration | eBay Finding API (official) | `ebaysdk` Python library |
| Price Data | Direct TCGPlayer scrape | Staggered nightly at 12:00 AM PST, one card/minute |
| Discord Alerts | discord.py (bot) | Webhook per user channel |
| Deployment | Railway | Free $5/month credit, always-on, easy deploys |
| Auth | JWT tokens + bcrypt password hashing | Simple, stateless, no OAuth complexity |

---

## Architecture

```
pokemon-deal-finder/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── scheduler.py             # APScheduler setup (polling + nightly price job)
│   ├── database.py              # SQLAlchemy engine + session
│   ├── models.py                # ORM models
│   ├── auth.py                  # JWT + bcrypt helpers
│   ├── routers/
│   │   ├── auth.py              # /api/auth/* endpoints
│   │   ├── searches.py          # /api/searches/* endpoints
│   │   ├── users.py             # /api/users/* endpoints
│   │   └── test.py              # /api/test/* endpoints (ping Discord, eBay, etc.)
│   ├── services/
│   │   ├── ebay.py              # eBay Finding API polling logic
│   │   ├── discord_bot.py       # Bot init + send_alert() helper
│   │   ├── tcgplayer.py         # TCGPlayer scraper + price cache
│   │   └── centering.py         # Card centering scorer (Phase 2)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx    # Per-user search query manager
│   │   │   └── Settings.jsx     # Discord channel ID, notification prefs
│   │   ├── components/
│   │   │   ├── SearchCard.jsx   # One search query widget
│   │   │   ├── ListingAlert.jsx # Recent alert display
│   │   │   └── TestPanel.jsx    # Endpoint test buttons
│   │   └── api.js               # Axios wrapper for backend calls
│   └── vite.config.js
├── .env.example
├── railway.toml
└── README.md
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| username | TEXT UNIQUE | |
| password_hash | TEXT | bcrypt |
| discord_channel_id | TEXT | User's channel in shared server |
| created_at | DATETIME | |

### `search_queries`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK → users | |
| query_string | TEXT | Raw eBay search string |
| is_graded | BOOLEAN | Filter: graded cards only |
| character_name | TEXT NULLABLE | Optional filter |
| min_price | FLOAT NULLABLE | |
| max_price | FLOAT NULLABLE | |
| deal_threshold | FLOAT NULLABLE | e.g. 0.10 = alert if 10% below market. NULL = alert on all new listings |
| is_active | BOOLEAN | Toggle on/off |
| created_at | DATETIME | |

### `seen_listings`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| search_query_id | INTEGER FK | |
| ebay_item_id | TEXT | eBay listing ID |
| first_seen_at | DATETIME | |

### `price_cache`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| card_query | TEXT UNIQUE | Normalized search string used to look up TCGPlayer |
| market_price | FLOAT NULLABLE | Most recent scraped price |
| last_updated | DATETIME | Set at midnight PST run |

---

## Backend — Key Logic

### 1. eBay Polling (every 5 minutes)

```
For each active search_query across all users:
  Call eBay Finding API: findItemsByKeywords
    - keywords: query_string
    - sortOrder: StartTimeNewest
    - itemFilter: Price (min/max if set), Condition (if is_graded → Graded)
    - outputSelector: SellerInfo, PictureURLSuperSize

  For each returned listing:
    If ebay_item_id NOT in seen_listings for this search_query:
      Insert into seen_listings

      Fetch cached price from price_cache WHERE card_query = normalized(query_string)

      Build alert:
        - Title, price, URL, image URL
        - If market_price exists:
            pct_diff = (market_price - listing_price) / market_price
            If deal_threshold is NULL OR pct_diff >= deal_threshold:
              Send Discord alert
        - If no market_price cached yet:
            Send alert anyway, note "Market price not yet cached"
```

**eBay API notes:**
- Use `ebaysdk` Python package
- Store `EBAY_APP_ID` in `.env`
- For graded filter: use `itemFilter` `Condition` with value `"3000"` (Graded)
- Wrap all API calls in try/except, log failures, do not crash the scheduler

---

### 2. Nightly TCGPlayer Price Scrape (12:00 AM PST)

```
Collect all unique card_query values from:
  - All active search_queries (normalized query strings)

For each card_query (with 60-second delay between each):
  Google search: f"site:tcgplayer.com {card_query}"
  Take the first result URL
  Scrape TCGPlayer product page:
    - Find market price in page HTML (look for "Market Price" label + adjacent $ value)
  Update price_cache SET market_price = X, last_updated = now()
```

**Scraping notes:**
- Use `requests` + `BeautifulSoup`
- Rotate user-agent headers to avoid blocks
- If scrape fails for a card, log and leave existing cache value intact
- For the Google step, use `googlesearch-python` library (no API key, scrapes quietly)
- Timezone: `pytz` — schedule in PST, convert to UTC for APScheduler

---

### 3. Discord Bot

- Use `discord.py` with a single bot token stored in `.env`
- Bot joins the shared server
- `send_alert(channel_id, listing)` function sends an embed:

```
📦 New Listing Found!
[Card name / query]
💰 Price: $XX.XX
📊 Market Price: $XX.XX (X% below market)  ← or "Market price not yet available"
🔗 [View on eBay]
🖼️ [Thumbnail image from listing]
```

- One Discord bot token shared across the app; each user provides their own `discord_channel_id` in Settings

---

### 4. Auth Flow

- `POST /api/auth/register` — username + password → hash with bcrypt → store in DB
- `POST /api/auth/login` — verify hash → return JWT (24hr expiry)
- All protected routes require `Authorization: Bearer <token>` header
- JWT secret stored in `.env`
- No email, no OAuth, no password reset for MVP

---

### 5. Test Endpoints (`/api/test/`)

| Endpoint | What it does |
|---|---|
| `POST /api/test/discord` | Sends a test embed message to the user's configured Discord channel |
| `POST /api/test/ebay` | Runs one poll cycle for a given search_query_id and returns raw results |
| `POST /api/test/tcgplayer` | Scrapes TCGPlayer for a given query and returns price result |

All return `{ success: bool, message: str, data: ... }` for easy display in the UI.

---

## Frontend — Pages & Components

### Design Direction
- **Theme:** Pokémon-inspired pixel art dashboard
- **Palette:** Deep navy background (`#0a0e1a`), electric yellow accent (`#FFD700`), Pokéball red (`#CC0000`), soft white text
- **Typography:** Pixel/retro display font (Press Start 2P from Google Fonts) for headings, clean readable font (Nunito) for body
- **Style:** Pixel borders, card tiles with subtle glow on hover, scanline texture overlay, smooth CSS transitions (no janky animations)
- **Layout:** Sidebar nav, main content area, card grid for search queries

---

### Pages

#### `/login`
- Username + password fields
- "Login" button
- No registration from UI — admin creates accounts (or expose register endpoint optionally)

#### `/dashboard` (protected)
- Grid of **SearchCard** components, one per active search query
- "Add New Search" button → modal form:
  - Search query string (text input)
  - Is graded? (toggle)
  - Character name (optional text)
  - Min / Max price (number inputs)
  - Deal threshold (dropdown: "All new listings", "5% below market", "10% below market", "15% below market", "Custom %" with input)
  - Active toggle
- Each SearchCard shows:
  - Query string
  - Filter summary pills (graded, price range, threshold)
  - Active/paused toggle
  - Last alert timestamp
  - Edit + Delete buttons
- Recent alerts feed (last 20 alerts across all queries, reverse chronological)

#### `/settings` (protected)
- Discord Channel ID input (with save button)
- **Test Panel** section:
  - "Send Test Discord Message" button
  - "Ping eBay API" button (tests credentials)
  - "Test TCGPlayer Scrape" button (input field for a query to test)
  - Each button shows a status result inline (✅ success / ❌ error + message)
- Change password form

---

## Environment Variables (`.env`)

```
# eBay
EBAY_APP_ID=

# Discord
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=

# Auth
JWT_SECRET=

# App
TZ=America/Los_Angeles
DATABASE_URL=sqlite:///./dealfinder.db
FRONTEND_URL=http://localhost:5173
```

---

## Deployment (Railway)

- **Backend service:** Python, runs `uvicorn main:app --host 0.0.0.0 --port 8000`
- **Frontend service:** Node build → static serve via Railway's static site support or a simple Express static server
- SQLite file persists on Railway's volume (add a volume mount to `/app/dealfinder.db`)
- Set all `.env` values as Railway environment variables
- `railway.toml` defines both services

---

## Phase 2 — Card Centering Checker (Post-MVP)

**Do not implement in initial build. Stub the service file only.**

### How it will work:
1. When a new listing alert is found, fetch the first image URL from the eBay listing
2. Download image → run through OpenCV centering analysis:
   - Detect card borders using edge detection (Canny)
   - Measure left/right and top/bottom border pixel widths
   - Calculate centering ratio
3. Score output:
   - 50/50 or 55/45 → "Centering: ✅ 10/10 (PSA 10 eligible)"
   - 60/40 or less → "Centering: ⚠️ 9/10"
4. Include score in Discord alert embed
5. Flag cards with bad angles/distance as "Centering: ❓ Image not suitable for analysis"

**Caveats to handle:**
- Card not close-up enough → skip analysis
- Card angled → skip analysis
- Holographic glare obscuring borders → skip analysis
- Always label result as an estimate, not a guarantee

**Libraries needed (Phase 2 only):**
- `opencv-python`
- `Pillow`
- `numpy`

---

## MVP Checklist (for Cursor)

- [ ] SQLite DB + all models created on startup
- [ ] Auth: register, login, JWT middleware
- [ ] eBay polling scheduler (5 min interval)
- [ ] Seen listings deduplication
- [ ] Discord bot sends formatted alert embeds
- [ ] Per-user channel routing
- [ ] TCGPlayer nightly scrape (12 AM PST, 60s stagger)
- [ ] Price cache used in alert embeds
- [ ] Deal threshold filtering
- [ ] CRUD for search queries (per user)
- [ ] Settings page: Discord channel ID save
- [ ] Test panel: Discord, eBay, TCGPlayer buttons
- [ ] React frontend with Pokémon pixel art theme
- [ ] Railway deployment config
- [ ] `.env.example` with all required keys
- [ ] `README.md` with setup instructions for friends
- [ ] Phase 2 centering service stubbed but not implemented