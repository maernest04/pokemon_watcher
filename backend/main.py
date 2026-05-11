import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import alerts as alerts_router
from routers import auth as auth_router
from routers import searches as searches_router
from routers import test as test_router
from routers import users as users_router
from scheduler import create_scheduler


# Ensure tables are created (especially for Vercel functions)
import models
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

_origins = [
    os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/"),
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(searches_router.router)
app.include_router(alerts_router.router)
app.include_router(test_router.router)


@app.get("/api/health")
def health():
    return {"ok": True}
