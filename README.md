# Pokémon eBay Deal Finder

A web application that monitors eBay listings for Pokémon cards, sends Discord alerts for new deals, and compares prices against PokeDATA market data.

## Features

- **Automated Monitoring:** Polls eBay every 5 minutes for new listings based on your search criteria.
- **Deal Detection:** Compares "Buy It Now" listings against PokeDATA market prices and alerts you if it's a deal.
- **Discord Alerts:** Sends rich embed notifications to your specific Discord channel.
- **Manual Overrides:** Set your own manual market prices for specific cards.
- **Structured Search:** Easily search by Pokémon name, set, and card number.
- **Auction Tracking:** Never miss a new auction listing.
- **Ungraded Only:** Filter for raw cards (Condition 4000).

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy (SQLite), APScheduler, BeautifulSoup4
- **Frontend:** React (Vite), CSS3
- **External APIs:** eBay Finding API, Discord (Bot), PokeDATA (Scraping)

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js & npm
- eBay App ID (Finding API)
- Discord Bot Token & Channel ID

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables (see `.env.example`):
   ```bash
   cp ../.env.example ../.env
   # Edit ../.env with your keys
   ```

## Automatic .env Loading

The backend now automatically loads `.env` files via `python-dotenv`. On Railway, environment variables are injected directly by the platform, which takes precedence over the `.env` file.

5. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev -- --host 127.0.0.1
   ```
   *Note: Using `--host 127.0.0.1` ensures consistent origin matching with the default backend configuration.*

## Environment Variables

| Variable | Description |
|---|---|
| `JWT_SECRET` | Secret key for signing auth tokens |
| `EBAY_APP_ID` | Your eBay Production App ID |
| `DISCORD_BOT_TOKEN` | Your Discord Bot token |
| `DATABASE_URL` | SQLite path (default: `sqlite:///./dealfinder.db`) |
| `FRONTEND_URL` | URL of your frontend (default: `http://localhost:5173`) |
| `TZ` | Timezone for the scheduler (default: `America/Los_Angeles`) |

## Database Management

The application uses SQLAlchemy's `create_all` to initialize the database on startup. 
If you need to reset the database (e.g., after schema changes), simply delete the `dealfinder.db` file in the `backend` directory.

## Testing

Use the **Test Panel** in the application settings to verify your integrations:
- **Discord:** Sends a test message to your channel.
- **eBay:** Polls eBay for one of your searches and returns raw results.
- **PokeDATA:** Tests the price scraper for a specific query.

## Scheduler Jobs

- **Polling:** Every 5 minutes, the app checks for new eBay listings.
- **Market Refresh:** Every night at midnight PST, the app updates the `price_cache` from PokeDATA.