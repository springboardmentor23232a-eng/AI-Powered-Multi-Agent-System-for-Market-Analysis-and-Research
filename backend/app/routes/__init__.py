from app.routes.auth import router as auth_router
from app.routes.stocks import router as stocks_router
from app.routes.research import router as research_router
from app.routes.watchlist import router as watchlist_router
from app.routes.preference import router as preference_router

__all__ = [
    "auth_router",
    "stocks_router",
    "research_router",
    "watchlist_router",
    "preference_router",
]
