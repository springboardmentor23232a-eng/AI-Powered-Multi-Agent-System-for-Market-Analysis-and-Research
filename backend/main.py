from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models  # needed so the User table is registered before create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Research Analyst API")
from auth import router as auth_router
app.include_router(auth_router)
from watchlists import router as watchlists_router
app.include_router(watchlists_router)
from workspace import router as workspace_router
app.include_router(workspace_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,   # required later for the HTTP-only cookie
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
