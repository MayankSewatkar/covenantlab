#!/bin/bash
set -e

# Load env
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

echo "Starting CovenantLab..."

# Start FastAPI in background
cd api && uvicorn main:app --reload --port 8000 &
API_PID=$!
cd ..

sleep 2

# Start Streamlit
cd frontend && streamlit run app.py --server.port 8501 &
STREAMLIT_PID=$!
cd ..

echo ""
echo "CovenantLab running:"
echo "  API:      http://localhost:8000"
echo "  Frontend: http://localhost:8501"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $API_PID $STREAMLIT_PID 2>/dev/null" EXIT
wait
