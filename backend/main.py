from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    import models

    _ = models
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"ok": True}
