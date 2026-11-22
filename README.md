# AI-Powered Multi-Agent System for Market Analysis and Research

## Project Overview

The AI-Powered Multi-Agent System for Market Analysis and Research is a web-based stock research platform designed to help users explore stock market information and organize their investment research.

The application combines a React frontend with a FastAPI backend and integrates financial market data to provide stock information, company details, financial data, market status, watchlists, and research workspace functionality.

## Features

- **User Authentication:** User registration and login functionality, including Google authentication.
- **Stock Market Data:** Retrieve stock information and historical price data.
- **Company Research:** View company profiles, stock information, and financial details.
- **Market Information:** Access market status and related market information.
- **Watchlists:** Create and manage saved stocks and watchlists.
- **Research Workspace:** Organize stock research activities.
- **Data Provenance:** Record information about external data retrieval operations.

## Technology Stack

### Frontend
- React
- JavaScript
- Vite
- Tailwind CSS
- Axios
- React Router

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- yfinance
- Pandas

### Database
- SQLAlchemy-compatible database configured through an environment variable.

## Project Structure

```text
AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── company.py
│   ├── database.py
│   ├── market_data.py
│   ├── markets.py
│   ├── models.py
│   ├── provenance.py
│   ├── schemas.py
│   ├── security.py
│   ├── watchlists.py
│   └── workspace.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── requirements.txt
