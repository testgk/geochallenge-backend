#!/usr/bin/env bash
# start_backend.sh — Start database and API server

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "GeoChallenge Backend"
echo "======================="

# Start database
echo ""
echo "Starting database..."
"$SCRIPT_DIR/start_db.sh"

# Wait for database to be ready
echo ""
echo "Waiting for database to be ready..."
sleep 3

# Activate virtual environment if it exists
if [ -f "../.venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "../.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start API server
echo ""
echo "Starting API server..."
echo "   Web App:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
