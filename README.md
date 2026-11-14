# EquityLens – AI-Powered Multi-Agent Stock Research Analyst

An intelligent stock research platform designed to simplify equity analysis through financial data, market insights, and AI-assisted research workflows.

## Overview

EquityLens is a web-based stock research application that enables users to search companies, monitor stocks, manage personalized watchlists, configure research preferences, and maintain research history.

The platform is designed to evolve into a multi-agent research system capable of producing comprehensive stock analysis reports.

## Features

### Module 1 – User Management & Stock Research Interface

- User registration and authentication
- Email/password login
- Google Sign-In
- Secure JWT-based authentication
- User-specific watchlists
- Stock search by company name or ticker
- Research task creation
- Research history tracking
- Persistent user preferences
- Personalized dashboard
- Market selection and analysis period configuration

## Technology Stack

### Frontend
- React
- Vite
- JavaScript
- CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- JWT Authentication

### Database
- PostgreSQL

### Authentication
- JWT
- Google Identity Services

## Project Structure

```text
Multi_Agent_Stock_Research_Analyst/
│
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
│
├── docker-compose.yml
├── run_backend.bat
├── .gitignore
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.10+
- Node.js and npm
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone -b Cellcia https://github.com/springboardmentor23232a-eng/AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research.git
cd AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables using `.env.example` as reference.

Start the backend:

```bash
python -m uvicorn app.main:app --reload
```

Backend API:

http://localhost:8000

API Documentation:

http://localhost:8000/docs

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Configure frontend environment variables using `.env.example`.

Start frontend:

```bash
npm run dev
```

Frontend application:

http://localhost:5173

## Security

- Password hashing
- JWT-based authentication
- User-specific data access
- Environment-based configuration
- Sensitive environment files excluded from version control

## Development Status

- Module 1: User Management, Watchlist, Preferences, Dashboard, and Research History – Completed
- Module 2: Multi-Agent Stock Research and Analysis Engine – Planned / In Development

## Contributors

Developed as part of the AI-Powered Multi-Agent System for Market Analysis and Research project.

## License

Refer to the LICENSE file.
