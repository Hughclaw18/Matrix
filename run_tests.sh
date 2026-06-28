#!/bin/bash
echo "========================================================"
echo "  MATRIX ORACLE NEURAL INTERFACE - TEST SUITE RUNNER"
echo "========================================================"
echo

# Set testing flag to force in-memory SQLite and Qdrant execution
export TESTING=True
export PYTHONPATH=$(pwd)/redpill-backend

cd redpill-backend

echo "[System Status] Running pytest suite..."
echo.
python3 -m pytest -v tests/test_backend.py

echo
echo "========================================================"
echo "  Tests completed."
echo "========================================================"
