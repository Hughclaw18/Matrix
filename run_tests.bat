@echo off
title 🟢 Matrix Oracle - Backend Test Runner
echo ========================================================
echo   MATRIX ORACLE NEURAL INTERFACE - TEST SUITE RUNNER
echo ========================================================
echo.

:: Set testing flag to force in-memory SQLite and Qdrant execution
set TESTING=True
set PYTHONPATH=%~dp0redpill-backend

cd /d "%~dp0redpill-backend"

echo [System Status] Running pytest suite...
echo.
python -m pytest -v tests/test_backend.py

echo.
echo ========================================================
echo   Tests completed. Press any key to return to Zion...
echo ========================================================
pause > nul
