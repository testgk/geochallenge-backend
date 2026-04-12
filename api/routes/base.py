"""
Base class for challenge-type-specific API routers.
Subclasses set `challenge_type` and `type_label` to get a fully-wired router.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import logging

from api.models import (
    ChallengeResponse,
    ChallengeListResponse,
    CityChallengeResponse,
    CityChallengeListResponse,
    CountryChallengeResponse,
    CountryChallengeListResponse,
    GuessRequest,
    GuessResultResponse,
    ScoringZone,
    ScoringZonesResponse,
    DifficultyEnum,
)
from entities.challenge import ChallengeType, CountryChallenge
from services.challenges_service import get_challenges_service, get_threshold_km


class BaseChallengeRouter:
    """
    Shared route logic for all challenge types.
    Subclasses declare `challenge_type` and `type_label`; all routes are
    automatically scoped to that type.
    """

    challenge_type: ChallengeType
    type_label:     str

    def __init__( self ):
        self.router = APIRouter()
        self.logger = logging.getLogger( self.__class__.__module__ )
        self._register_routes()

    def _register_routes( self ):
        r = self.router
        r.add_api_route( "/",                              self.list_challenges,  methods = [ "GET"  ], response_model = ChallengeListResponse  )
        r.add_api_route( "/random",                        self.get_random,       methods = [ "GET"  ], response_model = ChallengeResponse      )
        r.add_api_route( "/guess",                         self.submit_guess,     methods = [ "POST" ], response_model = GuessResultResponse    )
        r.add_api_route( "/{challenge_id}/scoring-zones",  self.get_scoring_zones, methods = [ "GET" ], response_model = ScoringZonesResponse   )
        r.add_api_route( "/{challenge_id}",                self.get_by_id,        methods = [ "GET"  ], response_model = ChallengeResponse      )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_response( self, c ):
        from api.models import CityChallengeResponse, CountryChallengeResponse
        if isinstance( c, CountryChallenge ):
            return CountryChallengeResponse(
                id             = c.id,
                location_name  = c.location_name,
                country        = c.country,
                continent      = c.continent,
                difficulty     = c.difficulty.value,
                hints          = c.hints,
                challenge_type = c.challenge_type.value,
                state_code     = c.state_code,
            )
        return CityChallengeResponse(
            id              = c.id,
            location_name   = c.location_name,
            latitude        = c.latitude,
            longitude       = c.longitude,
            country         = c.country,
            continent       = c.continent,
            difficulty      = c.difficulty.value,
            hints           = c.hints,
            max_distance_km = c.max_distance_km,
            challenge_type  = c.challenge_type.value,
        )

    def _not_found( self ) -> HTTPException:
        return HTTPException(
            status_code = 404,
            detail      = f"{ self.type_label.capitalize() } challenge not found",
        )

    # ------------------------------------------------------------------
    # Route handlers
    # ------------------------------------------------------------------

    async def list_challenges(
        self,
        difficulty: Optional[ DifficultyEnum ] = Query( default = None, description = "Filter by difficulty" ),
    ) -> ChallengeListResponse:
        service    = get_challenges_service()
        challenges = (
            service.get_challenges_by_difficulty( difficulty.value, self.challenge_type.value )
            if difficulty
            else service.get_all_challenges( self.challenge_type )
        )
        self.logger.debug( f"Returning { len( challenges ) } { self.type_label } challenges" )
        return ChallengeListResponse(
            challenges = [ self._to_response( c ) for c in challenges ],
            total      = len( challenges ),
        )

    async def get_random(
        self,
        difficulty: Optional[ DifficultyEnum ] = Query( default = None, description = "Filter by difficulty" ),
        exclude:    Optional[ str ]             = Query( default = None, description = "Comma-separated challenge IDs to exclude" ),
    ) -> ChallengeResponse:
        service     = get_challenges_service()
        exclude_ids = exclude.split( "," ) if exclude else []
        challenge   = service.get_random_challenge(
            difficulty     = difficulty.value if difficulty else None,
            exclude_ids    = exclude_ids,
            challenge_type = self.challenge_type.value,
        )
        if not challenge:
            self.logger.warning( f"No { self.type_label } challenges available" )
            raise HTTPException( status_code = 404, detail = f"No { self.type_label } challenges available" )
        self.logger.debug( f"Selected { self.type_label } challenge: { challenge.id }" )
        return self._to_response( challenge )

    async def get_by_id( self, challenge_id: str ) -> ChallengeResponse:
        service   = get_challenges_service()
        challenge = service.get_challenge_by_id( challenge_id )
        if not challenge or challenge.challenge_type != self.challenge_type:
            raise self._not_found()
        return self._to_response( challenge )

    async def submit_guess( self, request: GuessRequest ) -> GuessResultResponse:
        service   = get_challenges_service()
        result    = service.calculate_guess_result(
            challenge_id = request.challenge_id,
            guessed_lat  = request.guessed_lat,
            guessed_lng  = request.guessed_lng,
        )
        if not result:
            raise HTTPException( status_code = 404, detail = "Challenge not found" )
        challenge = service.get_challenge_by_id( request.challenge_id )
        if challenge.challenge_type != self.challenge_type:
            raise HTTPException(
                status_code = 400,
                detail      = f"This endpoint is for { self.type_label } challenges only",
            )
        return GuessResultResponse(
            challenge_id = result.challenge_id,
            guessed_lat  = result.guessed_lat,
            guessed_lng  = result.guessed_lng,
            actual_lat   = result.actual_lat,
            actual_lng   = result.actual_lng,
            distance_km  = result.distance_km,
            threshold_km = result.threshold_km,
            score        = result.score,
            scoring_zone = result.scoring_zone,
            is_correct   = result.is_correct,
        )

    async def get_scoring_zones( self, challenge_id: str ) -> ScoringZonesResponse:
        service   = get_challenges_service()
        challenge = service.get_challenge_by_id( challenge_id )
        if not challenge or challenge.challenge_type != self.challenge_type:
            raise self._not_found()
        zones = service.get_scoring_zones_for_challenge( challenge_id )
        if not zones:
            raise self._not_found()
        threshold = get_threshold_km( challenge.country, challenge.difficulty )
        return ScoringZonesResponse(
            challenge_id = challenge_id,
            threshold_km = threshold,
            zones        = [ ScoringZone( **z ) for z in zones ],
        )