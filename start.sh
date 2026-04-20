#!/bin/bash
cd /Users/mayanksewatkar/GitHub/covenantlab

# Kill anything on these ports
lsof -ti:8000,8501 | xargs kill -9 2>/dev/null

# Load API key
export $(cat .env | xargs)

# Start API from inside api/ directory
cd api && /Users/mayanksewatkar/GitHub/covenantlab/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &
echo "API starting at http://localhost:8000"
cd ..

sleep 2

# Start Streamlit
/Users/mayanksewatkar/GitHub/covenantlab/.venv/bin/streamlit run /Users/mayanksewatkar/GitHub/covenantlab/frontend/app.py --server.port 8501 &
echo "UI at http://localhost:8501"

echo ""
echo "Both servers running. Press Ctrl+C to stop."
wait
