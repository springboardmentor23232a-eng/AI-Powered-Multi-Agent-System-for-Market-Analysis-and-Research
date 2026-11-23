# Multi-Agent Stock Research Analyst

Full-stack implementation of **Module 1 (User Authentication & Research Workspace)** integrated with **Yahoo Finance (`yfinance`)**, **LangGraph**, **Gemini (`google-genai`)**, **scikit-learn**, **Plotly**, **PostgreSQL / SQLite**, **Docker Compose**, **pytest**, and **Postman**.

## Tech Stack
- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic, SQLAlchemy, PostgreSQL (Docker) / SQLite (local), JWT (`python-jose`), `passlib[bcrypt]`
- **AI & Quant:** LangGraph, Gemini (`google-genai`), `yfinance`, `pandas`, `NumPy`, `scikit-learn` (`LinearRegression` trend + SMA-20/50 + RSI-14)
- **Frontend:** React.js (Vite), Tailwind CSS, Plotly (`react-plotly.js`)
- **DevOps & Testing:** Docker, Docker Compose, `pytest`, Postman, VS Code, Git, GitHub Actions

## Quick Start (Docker Compose)
1. Set your Gemini API key (optional — falls back to quantitative brief if omitted):
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```
2. Start PostgreSQL, FastAPI, and React:
   ```bash
   docker compose up --build
   ```
3. Open:
   - Frontend: `http://localhost:5173`
   - FastAPI Swagger Docs: `http://localhost:8000/docs`

## Local Development (Without Docker)
### Backend (SQLite by default)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Run tests:
```bash
cd backend
pytest -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Postman & Git Setup
- Import `postman/Stock_Research_Analyst.postman_collection.json` into Postman to test registration, login (auto-saves JWT), preferences, watchlist, and research endpoints.
- Initialize Git and push to GitHub:
  ```bash
  git init
  git add .
  git commit -m "Initial Module 1 + LangGraph/Gemini stock research platform"
  ```
