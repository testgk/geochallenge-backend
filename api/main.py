"""
FastAPI application entry point.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import game, scores, challenges, boundaries
from services.challenges_service import get_scoring_zones_config

app = FastAPI(
    title="GeoChallenge API",
    description="Backend API for the GeoChallenge geography guessing game",
    version="1.0.0",
)

# Path to web frontend
WEB_DIR = Path(__file__).parent.parent.parent / "geochallenge-frontend" / "web"

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game.router, prefix="/api/game", tags=["Game"])
app.include_router(scores.router, prefix="/api/scores", tags=["Scores"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["Challenges"])
app.include_router(boundaries.router, prefix="/api/boundaries", tags=["Boundaries"])

# Mount static files for web frontend
if WEB_DIR.exists():
    app.mount("/css", StaticFiles(directory=WEB_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=WEB_DIR / "js"), name="js")
    app.mount("/data", StaticFiles(directory=WEB_DIR / "data"), name="data")


@app.get("/")
async def root():
    """Serve the web frontend."""
    if WEB_DIR.exists():
        return FileResponse(WEB_DIR / "index.html")
    return {"status": "ok", "service": "GeoChallenge API"}


@app.get("/api/scoring/zones")
async def get_scoring_zones():
    """
    Get scoring zone configuration.
    This is THE single source of truth for zone boundaries.
    All interfaces (web, desktop) must use these values.
    """
    return {
        "zones": get_scoring_zones_config(),
        "description": "Zone boundaries as fraction of threshold. inner/outer define the ring bounds."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
