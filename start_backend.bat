@echo off
echo Starting FastAPI Backend Server on http://127.0.0.1:8000 ...
call .\venv\Scripts\activate.bat
python backend\run.py
pause

