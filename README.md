# 📈 MarketMind AI – AI-Powered Multi-Agent System for Market Analysis and Research

MarketMind AI is a web-based stock market analysis and research platform designed to help users explore stock market data, monitor stocks, analyze historical price movements, and organize their investment research.

The platform combines financial data, interactive visualizations, and AI-oriented research capabilities to provide a centralized stock research experience.

## ✨ Features

### 1. User Authentication

- User registration and login.
- JWT-based authentication.
- Password hashing for security.
- Google authentication integration.

### 2. Market Analysis

- Live stock price lookup using Yahoo Finance data.
- Search stocks using company names or ticker symbols.
- Support for NSE, BSE, NASDAQ, and NYSE.
- Historical stock price visualization.
- Stock comparison charts.
- Market gainers and losers.

### 3. Watchlist Management

- Search and save stocks.
- View saved stocks.
- Remove stocks from the watchlist.
- Monitor saved stock prices.

### 4. AI Research and Analysis

- Financial research functionality.
- Research task management.
- Research history.
- Analysis reports and PDF downloads.

### 5. User Preferences

- Select preferred stock exchange.
- Configure research periods.
- Save user preferences.

### 6. Dashboard

- Interactive dashboard.
- Market overview.
- Stock charts and visualizations.
- Light and dark mode.
- Account information.

## 🛠️ Technology Stack

| Component         | Technologies             |
| ----------------- | ------------------------ |
| Frontend          | React.js, Vite           |
| Styling           | CSS                      |
| Backend           | Python, FastAPI          |
| Database          | PostgreSQL               |
| Authentication    | JWT, bcrypt              |
| Financial Data    | Yahoo Finance (yfinance) |
| Charts            | Recharts                 |
| API Communication | Axios                    |
| Version Control   | Git and GitHub           |

## 📂 Project Structure

```text
MarketMind-AI/
│
├── backend/
│   ├── routes/
│   ├── services/
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── dashboard images/
│
└── .gitignore
```

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.x
- Node.js and npm
- PostgreSQL
- Git

### 1. Clone the Repository

```bash
git clone -b Debajit-Pramanick https://github.com/springboardmentor23232a-eng/AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research.git

cd AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research
```

### 2. Backend Setup

```bash
cd backend
```

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure your PostgreSQL database and backend environment variables according to `backend/config.py`.

Start the backend:

```bash
uvicorn main:app
```

Backend URL:

```text
http://127.0.0.1:8000/
```

API Documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Configure the frontend environment variables if required.

Start the development server:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173/
```

## 📸 Dashboard Screenshots

The project includes dashboard screenshots in the `dashboard images` directory.

These demonstrate the application's interface, market overview, stock charts, and other features.

## 📸 Application Screenshots

### 1. Stock Search

![Stock Comparison](./dashboard%20images/Screenshot%202026-11-15%20at%201.36.04%20PM.png)

### 2. Market Analysis

![Market Analysis](./dashboard%20images/Screenshot%202026-11-15%20at%201.30.38%20PM.png)

### 3. Stock Charts

![User Dashboard](./dashboard%20images/Screenshot%202026-11-15%20at%201.37.21%20PM.png)

### 4. Stock Comparison

![Dashboard Overview](./dashboard%20images/Screenshot%202026-11-15%20at%201.22.48%20PM.png)

### 5. User Preferences

![Market Movers](./dashboard%20images/Screenshot%202026-11-15%20at%201.36.35%20PM.png)

### 6. Watchlist

![Watchlist](./dashboard%20images/Screenshot%202026-11-15%20at%201.36.58%20PM.png)

### 7. User Dashboard

![Stock Charts](./dashboard%20images/Screenshot%202026-11-15%20at%201.35.36%20PM.png)
## 🔐 Security

- Password hashing.
- JWT-based authentication.
- Environment variables for sensitive configuration.
- Git ignore rules to prevent accidental uploading of secrets.

**Never commit `.env` files, database passwords, API keys, or JWT secrets.**

## 🚀 Future Enhancements

- Advanced AI-powered financial research agents.
- More comprehensive stock market prediction models.
- Portfolio tracking and performance analysis.
- Advanced financial indicators.
- Improved real-time market monitoring.
- More intelligent investment research recommendations.

## 👨‍💻 Author

**Debajit Pramanick**

GitHub: https://github.com/springboardmentor23232a-eng

---

_MarketMind AI – Bringing Market Data, Analysis, and Research Together._
