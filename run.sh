#!/bin/bash
clear
echo "========================================================================"
echo "          🟢 MATRIX ORACLE NEURAL INTERFACE - LINUX CONSOLE 🟢"
echo "========================================================================"
echo "  [1] Launch Workspace Services (Backend + Frontend + Browser redirect)"
echo "  [2] Run Backend Unit Test Suite (In-Memory execution)"
echo "  [3] Clean Python cache directories (__pycache__ and *.pyc)"
echo "  [4] Exit"
echo "========================================================================"
read -p "Select a transmission channel [1-4]: " choice

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

case $choice in
    1)
        chmod +x "$DIR/start_project.sh"
        "$DIR/start_project.sh"
        ;;
    2)
        chmod +x "$DIR/run_tests.sh"
        "$DIR/run_tests.sh"
        ;;
    3)
        echo "[System Status] Purging pycache directories..."
        find "$DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find "$DIR" -type f -name "*.pyc" -delete 2>/dev/null
        echo "[System Status] Cleanup completed."
        ;;
    4)
        echo "Exiting Zion..."
        exit 0
        ;;
    *)
        echo "Invalid channel selected."
        exit 1
        ;;
esac
