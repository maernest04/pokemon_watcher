# Deployment Guide

This project is designed to be easily deployed on **Railway**.

## Required Environment Variables

Ensure the following variables are set in your Railway dashboard:

- `JWT_SECRET`: A long random string for securing authentication.
- `EBAY_APP_ID`: Your production App ID from the eBay Developer Portal.
- `DISCORD_BOT_TOKEN`: Your Discord Bot token.
- `DATABASE_URL`: `sqlite:////app/dealfinder.db` (Note the path to the volume).
- `FRONTEND_URL`: The public URL of your frontend service.
- `TZ`: `America/Los_Angeles` (or your preferred timezone for the nightly scrape).

## Railway Configuration

The project includes a `railway.toml` (if not present, create one) to define the backend and frontend services.

### SQLite Persistence

To persist your database across deployments:
1. Go to your Railway project.
2. Add a **Volume**.
3. Mount the volume at `/app/` in your backend service.
4. Ensure `DATABASE_URL` points to `/app/dealfinder.db`.

### Frontend Deployment

The frontend should be built and served. If you are using Railway's static hosting:
- Build Command: `npm run build`
- Output Directory: `dist`

If serving via the FastAPI backend as static files (standard for this MVP), ensure the backend is configured to mount the `dist` directory.

## Automatic .env Loading

The backend now automatically loads `.env` files via `python-dotenv`. On Railway, environment variables are injected directly by the platform, which takes precedence over the `.env` file.

## Migrations

This project does not yet use Alembic. Schema additions require a database reset or manual SQL migrations.
To reset:
1. Delete the `dealfinder.db` file.
2. Restart the backend service.
