@echo off
REM start_api.bat — Start only the API server (assumes database is running)

echo.
echo GeoChallenge API Server
echo ==========================

cd /d "%~dp0.."

REM Activate virtual environment if it exists
if exist "..\.venv\Scripts\activate.bat" (
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

echo.
echo    Web App:  http://localhost:8000
echo    API docs: http://localhost:8000/docs
echo.
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
