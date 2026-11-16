@echo off
echo ========================================================
echo Starting SAI ANALYSIS — Multi-Agent Stock Research Analyst
echo ========================================================
echo.
start "FastAPI Backend (Port 8000)" cmd /k ".\venv\Scripts\activate.bat && python backend\run.py"
start "React Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"
echo Both servers launched in dedicated terminal windows!
echo - Frontend: http://localhost:5173
echo - Backend:  http://127.0.0.1:8000
echo - Swagger:  http://127.0.0.1:8000/docs
echo ========================================================
timeout /t 5

