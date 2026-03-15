#!/usr/bin/env bash
# start_db.sh — start the GeoChallenge PostgreSQL container

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

CONTAINER="geochallenge_postgres"

echo "🐘 GeoChallenge Database"
echo "========================"

# Check Docker is available
if ! command -v docker &>/dev/null; then
    echo "❌ Docker is not installed or not in PATH."
    exit 1
fi

# Check docker-compose / docker compose
if command -v docker-compose &>/dev/null; then
    COMPOSE="docker-compose"
elif docker compose version &>/dev/null 2>&1; then
    COMPOSE="docker compose"
else
    echo "❌ docker-compose is not installed."
    exit 1
fi

# If container is already running, just report status
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "✅ Container '${CONTAINER}' is already running."
    docker ps --filter "name=${CONTAINER}" --format "   Host port : {{.Ports}}"
    exit 0
fi

echo "🚀 Starting PostgreSQL container..."
$COMPOSE up -d

# Wait for healthy status (up to 30 s)
echo "⏳ Waiting for database to be ready..."
RETRIES=30
until docker exec "$CONTAINER" pg_isready -U geochallenge -d geochallenge_db -q 2>/dev/null; do
    RETRIES=$(( RETRIES - 1 ))
    if [ "$RETRIES" -le 0 ]; then
        echo "❌ Database did not become ready in time."
        $COMPOSE logs postgres
        exit 1
    fi
    sleep 1
done

echo "✅ Database is ready!"
echo "   Host     : localhost"
echo "   Port     : 5432"
echo "   Database : geochallenge_db"
echo "   User     : geochallenge"
echo ""
echo "To stop:  ./stop_db.sh   (or: docker-compose down)"

