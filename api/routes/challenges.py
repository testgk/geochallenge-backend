"""
Challenges API routes.
Provides endpoints for getting and interacting with geographic challenges.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from api.models import (
    ChallengeResponse,
    ChallengeListResponse,
    ChallengeTypeEnum,
    GuessRequest,
    GuessResultResponse,
    ScoringZone,
    ScoringZonesResponse,
    DifficultyEnum,
)
from entities.challenge import StateChallenge
from services.challenges_service import get_challenges_service, get_threshold_km

router = APIRouter()

import logging

logger = logging.getLogger(__name__)

def _challenge_to_response( c ) -> ChallengeResponse:
    """Convert any Challenge subclass to ChallengeResponse."""
    return ChallengeResponse(
        id = c.id,
        location_name = c.location_name,
        latitude = c.latitude,
        longitude = c.longitude,
        country = c.country,
        continent = c.continent,
        difficulty = c.difficulty.value,
        hints = c.hints,
        max_distance_km = c.max_distance_km,
        challenge_type = c.challenge_type.value,
        state_code = c.state_code if isinstance( c, StateChallenge ) else None,
    )


@router.get( "/", response_model = ChallengeListResponse )
async def list_challenges(
    difficulty: Optional[ DifficultyEnum ] = Query( default = None, description = "Filter by difficulty" ),
    challenge_type: Optional[ ChallengeTypeEnum ] = Query( default = None, description = "Filter by challenge type" ),
):
    """
    Get all available challenges.
    Optionally filter by difficulty level and/or challenge type.
    """
    service = get_challenges_service()

    if difficulty:
        challenges = service.get_challenges_by_difficulty( difficulty.value )
    else:
        challenges = service.get_all_challenges()

    if challenge_type:
        challenges = [ c for c in challenges if c.challenge_type.value == challenge_type.value ]

    return ChallengeListResponse(
        challenges = [ _challenge_to_response( c ) for c in challenges ],
        total = len( challenges )
    )


@router.get( "/random", response_model = ChallengeResponse )
async def get_random_challenge(
    difficulty: Optional[ DifficultyEnum ] = Query( default = None, description = "Filter by difficulty" ),
    challenge_type: Optional[ ChallengeTypeEnum ] = Query( default = None, description = "Filter by challenge type" ),
    exclude: Optional[ str ] = Query( default = None, description = "Comma-separated challenge IDs to exclude" ),
):
    """
    Get a random challenge.
    Optionally filter by difficulty, challenge type, and exclude specific challenges.
    """
    service = get_challenges_service()

    exclude_ids = exclude.split( "," ) if exclude else []
    difficulty_str = difficulty.value if difficulty else None
    challenge_type_str = challenge_type.value if challenge_type else None

    challenge = service.get_random_challenge(
        difficulty = difficulty_str,
        exclude_ids = exclude_ids,
        challenge_type = challenge_type_str,
    )

    if not challenge:
        raise HTTPException( status_code = 404, detail = "No challenges available" )

    return _challenge_to_response( challenge )


@router.get( "/{challenge_id}", response_model = ChallengeResponse )
async def get_challenge( challenge_id: str ):
    """Get a specific challenge by ID."""
    service = get_challenges_service()

    challenge = service.get_challenge_by_id( challenge_id )

    if not challenge:
        raise HTTPException( status_code = 404, detail = "Challenge not found" )

    return _challenge_to_response( challenge )


@router.post( "/guess", response_model = GuessResultResponse )
async def submit_guess( request: GuessRequest ):
    """
    Submit a guess for a challenge.
    Returns distance, score (0-100), and scoring zone.
    """
    service = get_challenges_service()

    result = service.calculate_guess_result(
        challenge_id = request.challenge_id,
        guessed_lat = request.guessed_lat,
        guessed_lng = request.guessed_lng
    )

    print( result )

    if not result:
        raise HTTPException( status_code = 404, detail = "Challenge not found" )

    guessResult = GuessResultResponse(
        challenge_id = result.challenge_id,
        guessed_lat = result.guessed_lat,
        guessed_lng = result.guessed_lng,
        actual_lat = result.actual_lat,
        actual_lng = result.actual_lng,
        distance_km = result.distance_km,
        threshold_km = result.threshold_km,
        score = result.score,
        scoring_zone = result.scoring_zone,
        is_correct = result.is_correct
    )
    print( guessResult )
    return guessResult


@router.get( "/{challenge_id}/scoring-zones", response_model = ScoringZonesResponse )
async def get_scoring_zones( challenge_id: str ):
    """Get scoring zone boundaries for a challenge (for drawing rings)."""
    service = get_challenges_service()

    zones = service.get_scoring_zones_for_challenge( challenge_id )
    if not zones:
        raise HTTPException( status_code = 404, detail = "Challenge not found" )

    challenge = service.get_challenge_by_id( challenge_id )
    threshold = get_threshold_km( challenge.country, challenge.difficulty )

    return ScoringZonesResponse(
        challenge_id = challenge_id,
        threshold_km = threshold,
        zones = [ ScoringZone( **z ) for z in zones ]
    )