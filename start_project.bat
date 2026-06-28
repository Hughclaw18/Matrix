@echo off
title 🟢 Matrix Oracle - Launcher
echo ========================================================
echo   MATRIX ORACLE NEURAL INTERFACE - WORKSPACE LAUNCHER
echo ========================================================
echo.

:: 1. Launch FastAPI Backend
echo [System Status] Starting FastAPI Uvicorn engine...
start "Matrix Backend REST API" cmd /k "cd /d %~dp0redpill-backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"

:: 2. Launch Vite React Frontend
echo [System Status] Starting Vite React server...
start "Matrix Operator Console Interface" cmd /k "cd /d %~dp0redpill-interface && npm run dev"

:: 3. Launch browser (Vite default port 3000)
timeout /t 3 > nul
echo [System Status] Connection established. Redirecting to console...
start http://localhost:3000

echo.
echo ========================================================
echo   System running. Press any key to stop all channels...
echo ========================================================
pause > nul
