"""
Challenges service for managing geographic challenges.
Single source of truth for game logic - used by ALL interfaces (web, desktop, mobile).
"""

import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from entities.challenge import Challenge, ChallengeType, DifficultyLevel
from db.repositories.challenge_repository import ChallengeRepository
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
    actual_lat:   float
    actual_lng:   float
    distance_km:  float
    threshold_km: float
    score:        int
    scoring_zone: str
    is_correct:   bool


class ChallengesService:
    """
    Service for managing challenges and calculating results.
    Scoring behaviour is fully delegated to each Challenge subclass —
    no type-dispatch branching here.
    """

    def __init__( self ):
        self._challenges             = self._load_challenges_from_db()
        self._challenges_by_id       = { c.id: c for c in self._challenges }
        self._challenges_by_difficulty = self._group_by_difficulty()

    def _load_challenges_from_db( self ) -> List[ Challenge ]:
        try:
            repo       = ChallengeRepository()
            challenges = repo.get_all()
            print( f"Loaded {len( challenges )} challenges from database" )
            return challenges
        except Exception as e:
            print( f"Warning: Could not load challenges from database: {e}" )
            return []

    def get_all_challenges( self ) -> List[ Challenge ]:
        return self._challenges

    def get_challenge_by_id( self, challenge_id: str ) -> Optional[ Challenge ]:
        return self._challenges_by_id.get( challenge_id )

    def get_challenges_by_difficulty( self, difficulty: str ) -> List[ Challenge ]:
        try:
            level = DifficultyLevel( difficulty.lower() )
            return self._challenges_by_difficulty.get( level, [] )
        except ValueError:
            return []

    def get_random_challenge(
        self,
        difficulty:     Optional[ str ] = None,
        exclude_ids:    Optional[ List[ str ] ] = None,
        challenge_type: Optional[ str ] = None,
    ) -> Optional[ Challenge ]:
        exclude_ids = exclude_ids or []

        if difficulty and difficulty.lower() != 'random':
            challenges = self.get_challenges_by_difficulty( difficulty )
        else:
            challenges = self._challenges

        if challenge_type:
            try:
                ct         = ChallengeType( challenge_type.lower() )
                print(f"ct: {ct}")
                challenges = [ c for c in challenges if c.challenge_type == ct ]
            except ValueError:
                pass

        print( f"challenges: { challenges }")
        available = [ c for c in challenges if c.id not in exclude_ids ]
        return random.choice( available ) if available else None

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

        distance_km = haversine_distance(
            guessed_lat, guessed_lng,
            challenge.latitude, challenge.longitude
        )

        boundary_service = get_boundary_service()
        is_in_country    = boundary_service.is_point_in_country(
            lat          = guessed_lat,
            lng          = guessed_lng,
            country_name = challenge.country,
        )

        threshold_km = challenge.get_threshold_km( _get_country_areas(), _get_difficulty_levels() )
        scoring      = challenge.score_guess( is_in_country, distance_km, threshold_km )

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

    def _group_by_difficulty( self ) -> Dict[ DifficultyLevel, List[ Challenge ] ]:
        grouped = { level: [] for level in DifficultyLevel }
        for challenge in self._challenges:
            grouped[ challenge.difficulty ].append( challenge )
        return grouped


# Singleton instance
_challenges_service: Optional[ ChallengesService ] = None


def get_challenges_service() -> ChallengesService:
    global _challenges_service
    if _challenges_service is None:
        _challenges_service = ChallengesService()
    return _challenges_service
