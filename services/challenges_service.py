"""
Challenges service for managing geographic challenges.
Single source of truth for game logic - used by ALL interfaces (web, desktop, mobile).
"""

import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from entities.challenge import Challenge, ChallengeType, DifficultyLevel
from db.repositories.challenge_repository import ChallengeRepository
from db.repositories.country_challenge_repository import CountryChallengeRepository
from db.repositories.country_repository import CountryRepository
from db.repositories.difficulty_level_repository import DifficultyLevelRepository
from services.boundary_service import get_boundary_service
from services.scoring_utils import (
    SCORING_ZONES,
    get_scoring_zones_config,
    haversine_distance,
)


# Caches - loaded from database on first access
_country_areas_cache: Optional[ Dict[ str, float ] ] = None
_difficulty_levels_cache: Optional[ Dict[ str, Dict ] ] = None


def _get_country_areas() -> Dict[ str, float ]:
    global _country_areas_cache
    if _country_areas_cache is None:
        try:
            repo = CountryRepository()
            _country_areas_cache = repo.get_all_areas()
            print( f"Loaded {len( _country_areas_cache )} country areas from database" )
        except Exception as e:
            print( f"Warning: Could not load country areas from database: {e}" )
            _country_areas_cache = {}
    return _country_areas_cache


def _get_difficulty_levels() -> Dict[ str, Dict ]:
    global _difficulty_levels_cache
    if _difficulty_levels_cache is None:
        try:
            repo = DifficultyLevelRepository()
            _difficulty_levels_cache = repo.get_all_as_dict()
            print( f"Loaded {len( _difficulty_levels_cache )} difficulty levels from database" )
        except Exception as e:
            print( f"Warning: Could not load difficulty levels from database: {e}" )
            _difficulty_levels_cache = {
                'easy':   { 'threshold_multiplier': 2.0,  'max_distance_km': 10000 },
                'medium': { 'threshold_multiplier': 1.4,  'max_distance_km': 5000  },
                'hard':   { 'threshold_multiplier': 1.0,  'max_distance_km': 2500  },
                'expert': { 'threshold_multiplier': 0.65, 'max_distance_km': 1000  },
            }
    return _difficulty_levels_cache


def get_threshold_km( country: str, difficulty: DifficultyLevel ) -> float:
    """Convenience wrapper — kept for API route compatibility."""
    from entities.challenge import CityChallenge, DifficultyLevel as DL
    dummy = object.__new__( CityChallenge )
    dummy.country    = country
    dummy.difficulty = difficulty
    return dummy.get_threshold_km( _get_country_areas(), _get_difficulty_levels() )


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class GuessResult:
    """Result of a guess submission."""
    challenge_id: str
    guessed_lat:  float
    guessed_lng:  float
    actual_lat:   Optional[ float ]
    actual_lng:   Optional[ float ]
    distance_km:  float
    threshold_km: float
    score:        int
    scoring_zone: str
    is_correct:   bool


@dataclass
class ChallengeStore:
    """
    In-memory store for a single challenge type.
    Each ChallengeType gets its own store so lookups never scan across types.
    """
    all:           List[ Challenge ]
    by_id:         Dict[ str, Challenge ]
    by_difficulty: Dict[ DifficultyLevel, List[ Challenge ] ]


def _build_store( challenges: List[ Challenge ] ) -> ChallengeStore:
    by_difficulty: Dict[ DifficultyLevel, List[ Challenge ] ] = { lvl: [] for lvl in DifficultyLevel }
    for c in challenges:
        by_difficulty[ c.difficulty ].append( c )
    return ChallengeStore(
        all           = challenges,
        by_id         = { c.id: c for c in challenges },
        by_difficulty = by_difficulty,
    )


# =============================================================================
# Service
# =============================================================================

class ChallengesService:
    """
    Service for managing challenges and calculating results.

    Challenges are split into per-type ChallengeStores at startup.
    All reads go directly to the correct store — no cross-type scanning.
    Scoring behaviour is fully delegated to each Challenge subclass.
    """

    def __init__( self ):
        self._stores:    Dict[ ChallengeType, ChallengeStore ] = self._load_stores()
        self._all_by_id: Dict[ str, Challenge ]                = {
            c.id: c
            for store in self._stores.values()
            for c in store.all
        }

    # ------------------------------------------------------------------
    # Loading

    def _load_stores( self ) -> Dict[ ChallengeType, ChallengeStore ]:
        sources = {
            ChallengeType.CITY:    ( ChallengeRepository(),        'get_by_type', ChallengeType.CITY ),
            ChallengeType.COUNTRY: ( CountryChallengeRepository(), 'get_all',     None               ),
        }
        stores = {}
        for ct, ( repo, method, arg ) in sources.items():
            try:
                challenges = getattr( repo, method )( arg ) if arg else getattr( repo, method )()
                print( f"Loaded {len( challenges )} {ct.value} challenges" )
            except Exception as e:
                print( f"Warning: Could not load {ct.value} challenges: {e}" )
                challenges = []
            stores[ ct ] = _build_store( challenges )
        return stores

    def _repo_for( self, challenge_type: ChallengeType ):
        """Return the repository that owns the given challenge type's table."""
        if challenge_type == ChallengeType.COUNTRY:
            return CountryChallengeRepository()
        return ChallengeRepository()

    # ------------------------------------------------------------------
    # Reads

    def get_all_challenges( self, challenge_type: Optional[ ChallengeType ] = None ) -> List[ Challenge ]:
        if challenge_type:
            return self._stores[ challenge_type ].all
        return [ c for store in self._stores.values() for c in store.all ]

    def get_challenge_by_id( self, challenge_id: str ) -> Optional[ Challenge ]:
        return self._all_by_id.get( challenge_id )

    def get_challenges_by_difficulty(
        self,
        difficulty:     str,
        challenge_type: Optional[ str ] = None,
    ) -> List[ Challenge ]:
        try:
            level = DifficultyLevel( difficulty.lower() )
        except ValueError:
            return []

        if challenge_type:
            try:
                store = self._stores[ ChallengeType( challenge_type.lower() ) ]
                return store.by_difficulty.get( level, [] )
            except ( ValueError, KeyError ):
                return []

        return [ c for store in self._stores.values() for c in store.by_difficulty.get( level, [] ) ]

    def get_random_challenge(
        self,
        difficulty:     Optional[ str ] = None,
        exclude_ids:    Optional[ List[ str ] ] = None,
        challenge_type: Optional[ str ] = None,
    ) -> Optional[ Challenge ]:
        exclude_ids = exclude_ids or []

        candidates = self.get_challenges_by_difficulty( difficulty, challenge_type ) \
            if difficulty and difficulty.lower() != 'random' \
            else self.get_all_challenges(
                ChallengeType( challenge_type.lower() ) if challenge_type else None
            )

        available = [ c for c in candidates if c.id not in exclude_ids ]
        return random.choice( available ) if available else None

    # ------------------------------------------------------------------
    # Scoring

    def calculate_guess_result(
        self,
        challenge_id: str,
        guessed_lat:  float,
        guessed_lng:  float,
    ) -> Optional[ GuessResult ]:
        """
        Score a guess.
        Scoring logic lives in the Challenge subclass — no branching on challenge_type here.
        """
        challenge = self.get_challenge_by_id( challenge_id )
        if not challenge:
            return None

        distance_km      = (
            haversine_distance( guessed_lat, guessed_lng, challenge.latitude, challenge.longitude )
            if challenge.latitude is not None and challenge.longitude is not None
            else 0.0
        )
        boundary_service = get_boundary_service()
        is_in_region     = challenge.is_correct_location( boundary_service, guessed_lat, guessed_lng )
        threshold_km     = challenge.get_threshold_km( _get_country_areas(), _get_difficulty_levels() )
        scoring          = challenge.score_guess( is_in_region, distance_km, threshold_km )

        return GuessResult(
            challenge_id = challenge_id,
            guessed_lat  = guessed_lat,
            guessed_lng  = guessed_lng,
            actual_lat   = challenge.latitude,
            actual_lng   = challenge.longitude,
            distance_km  = round( distance_km, 2 ),
            threshold_km = scoring.threshold_km,
            score        = scoring.score,
            scoring_zone = scoring.scoring_zone,
            is_correct   = scoring.is_correct,
        )

    def get_scoring_zones_for_challenge( self, challenge_id: str ) -> Optional[ List[ Dict ] ]:
        """Get scoring zone data for visual ring display (city challenges only)."""
        challenge = self.get_challenge_by_id( challenge_id )
        if not challenge:
            return None

        threshold = challenge.get_threshold_km( _get_country_areas(), _get_difficulty_levels() )

        return [
            {
                "inner_fraction": zone[ "inner" ],
                "outer_fraction": zone[ "outer" ],
                "color":          zone[ "color" ],
                "label":          zone[ "label" ],
                "inner_km":       threshold * zone[ "inner" ],
                "outer_km":       threshold * zone[ "outer" ],
            }
            for zone in SCORING_ZONES
        ]

    # ------------------------------------------------------------------
    # Writes

    def create_challenge( self, data: Dict[ str, Any ] ) -> Challenge:
        """
        Persist a new challenge and add it to the correct store.
        If `id` is absent, one is auto-generated from location_name + country.
        """
        if not data.get( 'id' ):
            data[ 'id' ] = (
                f"{ data[ 'location_name' ] }_{ data[ 'country' ] }"
                .lower()
                .replace( ' ', '_' )
            )

        ct   = ChallengeType( data.get( 'challenge_type', ChallengeType.CITY.value ) )
        repo = self._repo_for( ct )
        created = repo.insert( data )
        self._add_to_store( created )
        return created

    def update_challenge( self, challenge_id: str, fields: Dict[ str, Any ] ) -> Optional[ Challenge ]:
        """
        Persist field updates and refresh the correct store.
        `fields` values must already be plain strings (no enum instances).
        """
        existing = self._all_by_id.get( challenge_id )
        ct       = existing.challenge_type if existing else ChallengeType.CITY
        repo     = self._repo_for( ct )
        updated  = repo.update( challenge_id, fields )
        if updated:
            self._replace_in_store( challenge_id, updated )
        return updated

    # ------------------------------------------------------------------
    # Store helpers

    def _add_to_store( self, challenge: Challenge ) -> None:
        store = self._stores[ challenge.challenge_type ]
        store.all.append( challenge )
        store.by_id[ challenge.id ] = challenge
        store.by_difficulty[ challenge.difficulty ].append( challenge )
        self._all_by_id[ challenge.id ] = challenge

    def _replace_in_store( self, challenge_id: str, updated: Challenge ) -> None:
        old   = self._all_by_id.get( challenge_id )
        store = self._stores[ updated.challenge_type ]
        store.all           = [ updated if c.id == challenge_id else c for c in store.all ]
        store.by_id[ challenge_id ] = updated
        # Rebuild difficulty index for this store only
        store.by_difficulty = _build_store( store.all ).by_difficulty
        # If the type changed, remove from old store too
        if old and old.challenge_type != updated.challenge_type:
            old_store = self._stores[ old.challenge_type ]
            old_store.all           = [ c for c in old_store.all if c.id != challenge_id ]
            old_store.by_id.pop( challenge_id, None )
            old_store.by_difficulty = _build_store( old_store.all ).by_difficulty
        self._all_by_id[ challenge_id ] = updated


# Singleton instance
_challenges_service: Optional[ ChallengesService ] = None


def get_challenges_service() -> ChallengesService:
    global _challenges_service
    if _challenges_service is None:
        _challenges_service = ChallengesService()
    return _challenges_service
