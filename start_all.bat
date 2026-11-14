@echo off
title Multi-Agent Stock Research Analyst - Launcher
echo ========================================================
echo Launching Multi-Agent Stock Research Analyst Workspace...
echo ========================================================

start "Backend Server" cmd /c "%~dp0start_backend.bat"
timeout /t 2 >nul
start "Frontend Server" cmd /c "%~dp0start_frontend.bat"
timeout /t 3 >nul

echo Opening browser at http://localhost:5173 ...
start http://localhost:5173
echo Workspace is running!
