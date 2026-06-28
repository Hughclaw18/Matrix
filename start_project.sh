#!/bin/bash
echo "========================================================"
echo "  MATRIX ORACLE NEURAL INTERFACE - WORKSPACE LAUNCHER"
echo "========================================================"
echo

# Get script root directory path
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# 1. Start FastAPI Backend in background
echo "[System Status] Starting FastAPI Uvicorn engine..."
cd "$DIR/redpill-backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# 2. Start Vite React Frontend in background
echo "[System Status] Starting Vite React server..."
cd "$DIR/redpill-interface"
npm run dev &
FRONTEND_PID=$!

# Kill child background tasks on interrupt exit
cleanup() {
    echo -e "\n[System Status] Closing transmission channels..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

# 3. Open browser redirect
sleep 3
echo "[System Status] Connection established. Redirecting to console..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v gnome-open > /dev/null; then
    gnome-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
fi

echo
echo "========================================================"
echo "  System running. Press CTRL+C to stop all channels..."
echo "========================================================"
wait
