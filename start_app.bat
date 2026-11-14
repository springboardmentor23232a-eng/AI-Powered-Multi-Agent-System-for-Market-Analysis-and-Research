@echo off
title Multi-Agent Stock Research Analyst
echo ========================================================
echo Starting Multi-Agent Stock Research Analyst Application
echo ========================================================
echo.

echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Stock Research Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Starting React Frontend on http://localhost:5173 ...
start "Stock Research Frontend" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

timeout /t 3 /nobreak >nul

echo [3/3] Opening Application in your default Browser...
start http://localhost:5173

echo.
echo ========================================================
echo Application is successfully running!
echo Frontend URL : http://localhost:5173
echo Backend Docs : http://127.0.0.1:8000/docs
echo ========================================================
echo.
pause

