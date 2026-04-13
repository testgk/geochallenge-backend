#!/usr/bin/env bash
# =============================================================================
# GeoChallenge — full database setup for a fresh deployment
#
# Usage:
#   DB_HOST=<host> DB_PORT=5432 DB_NAME=<db> DB_USER=<user> DB_PASSWORD=<pass> \
#       bash deploy/setup.sh
#
# All variables default to the values in .env when run from the project root.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Load .env if present and variables not already set
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-geochallenge_dev}"
DB_USER="${DB_USER:-geochallenge}"
DB_PASSWORD="${DB_PASSWORD:-}"

export PGPASSWORD="$DB_PASSWORD"
PSQL="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"

echo "[1/3] Running schema + seed migrations..."
$PSQL -f "$SCRIPT_DIR/migrate.sql"
echo "      Done."

echo "[2/3] Loading country boundaries (downloads ~3 MB from Natural Earth)..."
cd "$PROJECT_ROOT"
python3 scripts/load_boundaries.py
echo "      Done."

echo "[3/3] Verifying row counts..."
$PSQL -c "
SELECT 'challenges'         AS table_name, COUNT(*) FROM challenges
UNION ALL
SELECT 'country_challenges',               COUNT(*) FROM country_challenges
UNION ALL
SELECT 'country_boundaries',               COUNT(*) FROM country_boundaries
UNION ALL
SELECT 'countries',                        COUNT(*) FROM countries
UNION ALL
SELECT 'difficulty_levels',                COUNT(*) FROM difficulty_levels
ORDER BY table_name;
"

echo ""
echo "Setup complete. Start the backend with:"
echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000"
