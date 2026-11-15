

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.authentication import router as auth_router
from routes.watchlist import router as watchlist_router
from routes.market_data import router as market_data_router
from routes.research import router as research_router
from routes.preferences import router as preferences_router
from database import Base, engine
import models

app = FastAPI(
    title="Stock Research Analyst API",
    description="Authentication API for the AI-powered stock research application",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
app.include_router(auth_router)
app.include_router(watchlist_router)
app.include_router(market_data_router)
app.include_router(research_router)
app.include_router(preferences_router)

@app.get("/")
def home():
    return {"message": "Stock Research Analyst API is running!"}

