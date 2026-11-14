@echo off
title Multi-Agent Stock Research Analyst - Backend API
echo ===================================================
echo Starting FastAPI Backend Server on port 8000...
echo ===================================================
cd /d "%~dp0backend"
python run_backend.py
pause
