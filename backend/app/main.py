from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI

from .database import Base, engine
from .deps import csrf_guard
from .routers import auth, preferences, research, watchlist


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="ORIONNEX", lifespan=lifespan, dependencies=[Depends(csrf_guard)])

api = APIRouter(prefix="/api")
for r in (auth.router, preferences.router, watchlist.router, research.router):
    api.include_router(r)
app.include_router(api)
