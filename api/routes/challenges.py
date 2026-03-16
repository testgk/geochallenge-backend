"""
Challenges API routes.
Provides endpoints for getting and interacting with geographic challenges.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from api.models import (
    ChallengeResponse,
    ChallengeListResponse,
    GuessRequest,
    GuessResultResponse,
    DifficultyEnum,
)
from services.challenges_service import get_challenges_service

router = APIRouter()


@router.get("/", response_model=ChallengeListResponse)
async def list_challenges(
    difficulty: Optional[DifficultyEnum] = Query(default=None, description="Filter by difficulty")
):
    """
    Get all available challenges.
    Optionally filter by difficulty level.
    """
    service = get_challenges_service()
    
    if difficulty:
        challenges = service.get_challenges_by_difficulty(difficulty.value)
    else:
        challenges = service.get_all_challenges()
    
    return ChallengeListResponse(
        challenges=[
            ChallengeResponse(
                id=c.id,
                location_name=c.location_name,
                latitude=c.latitude,
                longitude=c.longitude,
                country=c.country,
                continent=c.continent,
                difficulty=c.difficulty.value,
                hints=c.hints,
                max_distance_km=c.max_distance_km
            )
            for c in challenges
        ],
        total=len(challenges)
    )


@router.get("/random", response_model=ChallengeResponse)
async def get_random_challenge(
    difficulty: Optional[DifficultyEnum] = Query(default=None, description="Filter by difficulty"),
    exclude: Optional[str] = Query(default=None, description="Comma-separated challenge IDs to exclude")
):
    """
    Get a random challenge.
    Optionally filter by difficulty and exclude specific challenges.
    """
    service = get_challenges_service()
    
    exclude_ids = exclude.split(",") if exclude else []
    difficulty_str = difficulty.value if difficulty else None
    
    challenge = service.get_random_challenge(
        difficulty=difficulty_str,
        exclude_ids=exclude_ids
    )
    
    if not challenge:
        raise HTTPException(status_code=404, detail="No challenges available")
    
    return ChallengeResponse(
        id=challenge.id,
        location_name=challenge.location_name,
        latitude=challenge.latitude,
        longitude=challenge.longitude,
        country=challenge.country,
        continent=challenge.continent,
        difficulty=challenge.difficulty.value,
        hints=challenge.hints,
        max_distance_km=challenge.max_distance_km
    )


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(challenge_id: str):
    """Get a specific challenge by ID."""
    service = get_challenges_service()
    
    challenge = service.get_challenge_by_id(challenge_id)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return ChallengeResponse(
        id=challenge.id,
        location_name=challenge.location_name,
        latitude=challenge.latitude,
        longitude=challenge.longitude,
        country=challenge.country,
        continent=challenge.continent,
        difficulty=challenge.difficulty.value,
        hints=challenge.hints,
        max_distance_km=challenge.max_distance_km
    )


@router.post("/guess", response_model=GuessResultResponse)
async def submit_guess(request: GuessRequest):
    """
    Submit a guess for a challenge.
    Returns distance, accuracy, and points earned.
    """
    service = get_challenges_service()
    
    result = service.calculate_guess_result(
        challenge_id=request.challenge_id,
        guessed_lat=request.guessed_lat,
        guessed_lng=request.guessed_lng
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return GuessResultResponse(
        challenge_id=result.challenge_id,
        guessed_lat=result.guessed_lat,
        guessed_lng=result.guessed_lng,
        actual_lat=result.actual_lat,
        actual_lng=result.actual_lng,
        distance_km=result.distance_km,
        accuracy_percent=result.accuracy_percent,
        points_earned=result.points_earned,
        max_points=result.max_points,
        is_correct=result.is_correct
    )
