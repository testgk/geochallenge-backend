"""
Country Challenges API routes.
"""

from typing import List
from fastapi import HTTPException
from pydantic import BaseModel

from entities.challenge import ChallengeType
from api.routes.base import BaseChallengeRouter
from db.repositories.country_neighbors_repository import CountryNeighborsRepository
from services.challenges_service import get_challenges_service


class NeighborsResponse( BaseModel ):
    challenge_id: str
    country:      str
    neighbors:    List[ str ]


class CountryChallengeRouter( BaseChallengeRouter ):
    challenge_type = ChallengeType.COUNTRY
    type_label     = "country"

    def _register_routes( self ):
        super()._register_routes()
        self.router.add_api_route(
            "/{challenge_id}/neighbors",
            self.get_neighbors,
            methods = [ "GET" ],
            response_model = NeighborsResponse,
        )

    async def get_neighbors( self, challenge_id: str ) -> NeighborsResponse:
        """Return the list of neighboring countries for a country challenge."""
        service   = get_challenges_service()
        challenge = service.get_challenge_by_id( challenge_id )
        if not challenge or challenge.challenge_type != self.challenge_type:
            raise self._not_found()
        repo      = CountryNeighborsRepository()
        neighbors = repo.get_neighbors( challenge_id )
        return NeighborsResponse(
            challenge_id = challenge_id,
            country      = challenge.country,
            neighbors    = neighbors,
        )


router = CountryChallengeRouter().router