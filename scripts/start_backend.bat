@echo off
REM start_backend.bat — Start database and API server

echo.
echo GeoChallenge Backend
echo =======================

cd /d "%~dp0.."

REM Start database
echo.
echo Starting database...
docker-compose up -d

REM Wait for database to be ready
echo.
echo Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Activate virtual environment if it exists
if exist "..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Install dependencies if needed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start API server
echo.
echo Starting API server...
echo    Web App:  http://localhost:8000
echo    API docs: http://localhost:8000/docs
echo.
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
