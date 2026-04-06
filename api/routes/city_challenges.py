"""
City Challenges API routes.
Provides endpoints for city-type geographic challenges.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import logging

from api.models import (
    ChallengeResponse,
    ChallengeListResponse,
    GuessRequest,
    GuessResultResponse,
    ScoringZone,
    ScoringZonesResponse,
    DifficultyEnum,
)
from entities.challenge import ChallengeType, StateChallenge
from services.challenges_service import get_challenges_service, get_threshold_km

router = APIRouter()
logger = logging.getLogger( __name__ )


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
async def list_city_challenges(
    difficulty: Optional[ DifficultyEnum ] = Query( default = None, description = "Filter by difficulty" ),
):
    """
    Get all available city challenges.
    Optionally filter by difficulty level.
    """
    service = get_challenges_service()

    if difficulty:
        challenges = service.get_challenges_by_difficulty( difficulty.value )
    else:
        challenges = service.get_all_challenges()

    # Filter by city type
    challenges = [ c for c in challenges if c.challenge_type == ChallengeType.CITY ]

    logger.debug( f"Returning {len( challenges )} city challenges" )

    return ChallengeListResponse(
        challenges = [ _challenge_to_response( c ) for c in challenges ],
        total = len( challenges )
    )


@router.get( "/random", response_model = ChallengeResponse )
async def get_random_city_challenge(
    difficulty: Optional[ DifficultyEnum ] = Query( default = None, description = "Filter by difficulty" ),
    exclude: Optional[ str ] = Query( default = None, description = "Comma-separated challenge IDs to exclude" ),
):
    """
    Get a random city challenge.
    Optionally filter by difficulty and exclude specific challenges.
    """
    service = get_challenges_service()

    exclude_ids = exclude.split( "," ) if exclude else []
    difficulty_str = difficulty.value if difficulty else None

    logger.debug( f"Getting random city challenge: difficulty={difficulty_str}, exclude={exclude_ids}" )

    challenge = service.get_random_challenge(
        difficulty = difficulty_str,
        exclude_ids = exclude_ids,
        challenge_type = "city",
    )

    if not challenge:
        logger.warning( "No city challenges available" )
        raise HTTPException( status_code = 404, detail = "No city challenges available" )

    logger.debug( f"Selected city challenge: {challenge.id}" )
    return _challenge_to_response( challenge )


@router.get( "/{challenge_id}", response_model = ChallengeResponse )
async def get_city_challenge( challenge_id: str ):
    """Get a specific city challenge by ID."""
    service = get_challenges_service()

    challenge = service.get_challenge_by_id( challenge_id )

    if not challenge or challenge.challenge_type != ChallengeType.CITY:
        raise HTTPException( status_code = 404, detail = "City challenge not found" )

    return _challenge_to_response( challenge )


@router.post( "/guess", response_model = GuessResultResponse )
async def submit_city_guess( request: GuessRequest ):
    """
    Submit a guess for a city challenge.
    Returns distance, score (0-100), and scoring zone.
    """
    service = get_challenges_service()

    result = service.calculate_guess_result(
        challenge_id = request.challenge_id,
        guessed_lat = request.guessed_lat,
        guessed_lng = request.guessed_lng
    )

    if not result:
        raise HTTPException( status_code = 404, detail = "Challenge not found" )

    # Verify it's a city challenge
    challenge = service.get_challenge_by_id( request.challenge_id )
    if challenge.challenge_type != ChallengeType.CITY:
        raise HTTPException( status_code = 400, detail = "This endpoint is for city challenges only" )

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

    logger.debug( f"City guess result: {guessResult}" )
    return guessResult


@router.get( "/{challenge_id}/scoring-zones", response_model = ScoringZonesResponse )
async def get_city_scoring_zones( challenge_id: str ):
    """Get scoring zone boundaries for a city challenge (for drawing rings)."""
    service = get_challenges_service()

    zones = service.get_scoring_zones_for_challenge( challenge_id )
    if not zones:
        raise HTTPException( status_code = 404, detail = "City challenge not found" )

    challenge = service.get_challenge_by_id( challenge_id )
    if challenge.challenge_type != ChallengeType.CITY:
        raise HTTPException( status_code = 404, detail = "City challenge not found" )

    threshold = get_threshold_km( challenge.country, challenge.difficulty )

    return ScoringZonesResponse(
        challenge_id = challenge_id,
        threshold_km = threshold,
        zones = [ ScoringZone( **z ) for z in zones ]
    )

