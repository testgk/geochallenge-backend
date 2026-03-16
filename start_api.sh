#!/usr/bin/env bash
# start_api.sh — Start only the API server (assumes database is running)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 GeoChallenge API Server"
echo "=========================="

# Activate virtual environment if it exists
if [ -f "../.venv/bin/activate" ]; then
    source "../.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "   Web App:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
