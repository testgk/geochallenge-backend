# GeoChallenge Backend

PostgreSQL database, entities, repositories and scoring service for the GeoChallenge Globe App.

## Structure

```
geochallenge-backend/
    db/
        connection.py          # PostgreSQL connection pool
        init/                  # SQL migration scripts
        models/                # Low-level DB models (User)
        repositories/          # Repository pattern (GameSession, Score)
    entities/
        base.py                # Abstract base entity
        user.py                # UserEntity
        game_session.py        # GameSessionEntity
        score.py               # ScoreEntity
    services/
        scoring_service.py     # High-level scoring API
    docker-compose.yml         # PostgreSQL container
    requirements.txt
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the database
docker-compose up -d

# 3. Copy .env.example -> .env and fill in credentials
cp .env.example .env
```

## Environment Variables

| Variable              | Default              | Description              |
|-----------------------|----------------------|--------------------------|
| `DB_HOST`             | `localhost`          | PostgreSQL host          |
| `DB_PORT`             | `5432`               | PostgreSQL port          |
| `DB_NAME`             | `geochallenge_db`    | Database name            |
| `DB_USER`             | `geochallenge`       | Database user            |
| `DB_PASSWORD`         | `geochallenge_secret`| Database password        |
| `DB_MIN_CONNECTIONS`  | `1`                  | Connection pool minimum  |
| `DB_MAX_CONNECTIONS`  | `10`                 | Connection pool maximum  |

