# GeoChallenge Backend Documentation

Documentation for the GeoChallenge backend API and database.

## 📚 Available Documentation

**[IDE_IMPORT_FIX.md](./IDE_IMPORT_FIX.md)**
- Troubleshooting guide for IDE import errors
- How to fix false positive import warnings
- IDE configuration for Python imports
- Verification that imports work correctly

## 📖 Main Backend Documentation

The main backend README is located at:
- [../README.md](../README.md) - Backend structure, setup, and environment variables

## 🧪 Testing & Scripts

Scripts are located in `../scripts/`:

**[verify_imports.py](../scripts/verify_imports.py)**
- Comprehensive import verification
- Tests all service and route imports
- Useful for debugging

**[test_boundaries.py](../scripts/test_boundaries.py)**
- Full test suite for boundaries API
- Tests all endpoints with mocked database
- Ensures API functionality

## 🔍 Quick Reference

### API Structure

```
geochallenge-backend/
├── api/
│   ├── main.py              # FastAPI application
│   ├── models.py            # API request/response models
│   └── routes/
│       ├── boundaries.py    # Country boundary endpoints
│       ├── challenges.py    # Challenge endpoints
│       ├── game.py          # Game session endpoints
│       └── scores.py        # Score endpoints
├── db/
│   ├── connection.py        # Database connection management
│   ├── models/              # Database models
│   └── repositories/        # Data access layer
├── services/
│   ├── boundary_service.py  # Boundary checking logic
│   ├── challenges_service.py # Challenge management
│   └── scoring_service.py   # Scoring logic
└── entities/
    ├── game_session.py      # Game session entity
    ├── score.py             # Score entity
    └── user.py              # User entity
```

### Common Issues

#### Import Errors in IDE

If your IDE shows import errors but code runs fine:
1. Read [IDE_IMPORT_FIX.md](./IDE_IMPORT_FIX.md)
2. Run `python3 scripts/verify_imports.py` to verify
3. Restart your IDE/language server

#### Database Connection Issues

1. Check environment variables:
   ```bash
   echo $DB_HOST
   echo $DB_PORT
   ```

2. Test connection:
   ```bash
   python3 ../scripts/test_remote_connection.py
   ```

3. Start local database:
   ```bash
   docker-compose up -d
   ```

#### API Testing

```bash
# Start API server
uvicorn api.main:app --reload

# Test in browser
open http://localhost:8000/docs

# Run tests
source .venv/bin/activate
python scripts/test_boundaries.py
```

## 🌐 API Endpoints

### Boundaries API (`/api/boundaries`)
- `POST /check-point` - Check if point is in country
- `GET /country/{name}` - Get country boundary GeoJSON
- `POST /countries` - Get multiple country boundaries

### Challenges API (`/api/challenges`)
- `GET /` - List all challenges
- `GET /{id}` - Get specific challenge
- `POST /guess` - Submit a guess

### Game API (`/api/game`)
- `POST /start` - Start new game session
- `POST /submit-round` - Submit round result
- `POST /end` - End game session

### Scores API (`/api/scores`)
- `GET /leaderboard` - Get top scores
- `GET /user/{username}` - Get user scores
- `POST /` - Submit new score

## 🔧 Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start local database
docker-compose up -d

# Run API server
uvicorn api.main:app --reload
```

### Testing

```bash
# Verify imports
python3 scripts/verify_imports.py

# Test boundaries API
python scripts/test_boundaries.py

# Test database connection
python3 ../scripts/test_remote_connection.py
```

## 📁 Related Documentation

- [Root Documentation](../../docs/) - Database configuration guides
- [Frontend Documentation](../../geochallenge-frontend/docs/) - Desktop app database setup
- [Scripts Documentation](../../scripts/README.md) - Utility scripts

## 🆘 Need Help?

- **Import Errors:** [IDE_IMPORT_FIX.md](./IDE_IMPORT_FIX.md)
- **Database Setup:** [../../docs/DESKTOP_APP_DATABASE_CONFIG.md](../../docs/DESKTOP_APP_DATABASE_CONFIG.md)
- **API Issues:** Check `api/main.py` and route files
- **Testing:** Run scripts in `../scripts/`
