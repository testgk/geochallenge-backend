#!/usr/bin/env bash
# stop_db.sh — stop the GeoChallenge PostgreSQL container

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

CONTAINER="geochallenge_postgres"

echo "🐘 GeoChallenge Database"
echo "========================"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ℹ️  Container '${CONTAINER}' is not running."
    exit 0
fi

if command -v docker-compose &>/dev/null; then
    COMPOSE="docker-compose"
else
    COMPOSE="docker compose"
fi

echo "🛑 Stopping PostgreSQL container..."
$COMPOSE down
echo "✅ Database stopped."

