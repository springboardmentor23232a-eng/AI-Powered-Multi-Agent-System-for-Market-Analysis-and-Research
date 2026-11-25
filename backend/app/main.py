from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, preferences, stocks, watchlist, research, market

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Agent Stock Research Analyst")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(preferences.router)
app.include_router(stocks.router)
app.include_router(watchlist.router)
app.include_router(research.router)
app.include_router(market.router)


@app.get("/")
def root():
    return {"message": "Stock Research Analyst API is running. See /docs"}


@app.get("/health")
def health():
    return {"status": "ok"}