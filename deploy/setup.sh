#!/usr/bin/env bash
# =============================================================================
# GeoChallenge — full database setup / migration
#
# Usage (pick one):
#
#   # With a single DATABASE_URL:
#   DATABASE_URL=postgresql://user:pass@host/db bash deploy/setup.sh
#
#   # With individual variables:
#   DB_HOST=... DB_PORT=5432 DB_NAME=... DB_USER=... DB_PASSWORD=... \
#       bash deploy/setup.sh
#
#   # With no arguments — reads from .env in the project root:
#   bash deploy/setup.sh
#
# Idempotent: safe to run multiple times against the same database.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# ── Load .env if present and variables not already set ──────────────────────
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a; source "$PROJECT_ROOT/.env"; set +a
fi

# ── Build connection string ──────────────────────────────────────────────────
if [ -n "${DATABASE_URL:-}" ]; then
    PSQL="psql $DATABASE_URL"
    export PGPASSWORD=""          # psql parses password from URL
else
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-geochallenge_dev}"
    DB_USER="${DB_USER:-geochallenge}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    export PGPASSWORD="$DB_PASSWORD"
    PSQL="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
fi

# ── Step 1: schema + seed migrations ────────────────────────────────────────
echo "[1/3] Running migrations..."
$PSQL -v ON_ERROR_STOP=0 -f "$SCRIPT_DIR/migrate.sql" 2>&1 \
    | grep -v "^NOTICE:" \
    | grep -v "^$" \
    || true
echo "      Done."

# ── Step 2: country boundary data ───────────────────────────────────────────
echo "[2/3] Loading country boundaries..."
cd "$PROJECT_ROOT"
if [ -n "${DATABASE_URL:-}" ]; then
    DATABASE_URL="$DATABASE_URL" python3 scripts/load_boundaries.py
else
    DB_HOST="$DB_HOST" DB_PORT="$DB_PORT" DB_NAME="$DB_NAME" \
    DB_USER="$DB_USER" DB_PASSWORD="$DB_PASSWORD" \
        python3 scripts/load_boundaries.py
fi
echo "      Done."

# ── Step 3: verify ───────────────────────────────────────────────────────────
echo "[3/3] Verifying..."
$PSQL -t -c "
SELECT '  ' || rpad(table_name, 26) || count::text AS line FROM (
    SELECT 'challenges'          AS table_name, COUNT(*) AS count FROM challenges
    UNION ALL SELECT 'country_challenges',      COUNT(*) FROM country_challenges
    UNION ALL SELECT 'country_boundaries',      COUNT(*) FROM country_boundaries
    UNION ALL SELECT 'countries',               COUNT(*) FROM countries
    UNION ALL SELECT 'difficulty_levels',       COUNT(*) FROM difficulty_levels
) t ORDER BY table_name;
"

echo ""
echo "Setup complete."
