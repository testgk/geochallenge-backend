"""
Challenge entity for geographic challenges.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any


class DifficultyLevel( Enum ):
    """Challenge difficulty levels."""
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"
    EXPERT = "expert"


class ChallengeType( Enum ):
    """Types of geographic challenges."""
    CITY  = "city"
    STATE = "state"


@dataclass
class Challenge:
    """
    Abstract base geographic challenge entity.
    Use CityChallenge or StateChallenge instead of instantiating directly.
    """
    id: str
    location_name: str
    latitude: float
    longitude: float
    country: str
    continent: str
    difficulty: DifficultyLevel
    hints: List[ str ]
    max_distance_km: float
    challenge_type: ChallengeType = ChallengeType.CITY

    # ------------------------------------------------------------------
    # Overridden by subclasses — no type-dispatch if/else needed in service

    def get_threshold_km( self, country_areas: Dict[ str, float ], difficulty_config: Dict[ str, Dict ] ) -> float:
        """Return the scoring threshold in km. Overridden by CityChallenge."""
        return 0.0

    def score_guess( self, is_in_country: bool, distance_km: float, threshold_km: float ):
        """Score a guess and return a ScoringResult. Overridden by subclasses."""
        raise NotImplementedError

    # ------------------------------------------------------------------

    def to_dict( self ) -> Dict[ str, Any ]:
        return {
            'id':             self.id,
            'location_name':  self.location_name,
            'latitude':       self.latitude,
            'longitude':      self.longitude,
            'country':        self.country,
            'continent':      self.continent,
            'difficulty':     self.difficulty.value,
            'hints':          self.hints,
            'max_distance_km': self.max_distance_km,
            'challenge_type': self.challenge_type.value,
        }

    @classmethod
    def from_dict( cls, data: Dict[ str, Any ] ) -> 'Challenge':
        """Factory — returns CityChallenge or StateChallenge based on challenge_type."""
        challenge_type = ChallengeType( data.get( 'challenge_type', 'city' ) )
        if challenge_type == ChallengeType.STATE:
            return StateChallenge.from_dict( data )
        return CityChallenge.from_dict( data )


@dataclass
class CityChallenge( Challenge ):
    """Challenge to locate a city on the map."""

    _BASE_THRESHOLD_KM = 600.0
    _MAX_THRESHOLD_KM  = 1100.0

    def __post_init__( self ):
        self.challenge_type = ChallengeType.CITY

    def get_threshold_km( self, country_areas: Dict[ str, float ], difficulty_config: Dict[ str, Dict ] ) -> float:
        multiplier = difficulty_config.get( self.difficulty.value, {} ).get( 'threshold_multiplier', 1.0 )
        area_km2   = country_areas.get( self.country, 500_000 )
        country_km = math.sqrt( area_km2 ) * multiplier
        return min( self._MAX_THRESHOLD_KM, max( self._BASE_THRESHOLD_KM, country_km ) )

    def score_guess( self, is_in_country: bool, distance_km: float, threshold_km: float ):
        from services.scoring_utils import ScoringResult, calculate_score, get_scoring_zone
        score = calculate_score( distance_km, threshold_km, is_in_country, self.difficulty.value )
        zone  = get_scoring_zone( distance_km, threshold_km ) if is_in_country else "outside"
        return ScoringResult(
            score        = score,
            scoring_zone = zone,
            threshold_km = threshold_km,
            is_correct   = distance_km <= threshold_km and is_in_country,
        )

    def to_dict( self ) -> Dict[ str, Any ]:
        return super().to_dict()

    @classmethod
    def from_dict( cls, data: Dict[ str, Any ] ) -> 'CityChallenge':
        return cls(
            id              = data[ 'id' ],
            location_name   = data[ 'location_name' ],
            latitude        = data[ 'latitude' ],
            longitude       = data[ 'longitude' ],
            country         = data[ 'country' ],
            continent       = data[ 'continent' ],
            difficulty      = DifficultyLevel( data[ 'difficulty' ] ),
            hints           = data.get( 'hints', [] ),
            max_distance_km = data.get( 'max_distance_km', 1000 ),
        )


@dataclass
class StateChallenge( Challenge ):
    """Challenge to locate a state/country on the map by clicking inside its boundary."""
    state_code: str = ''

    def __post_init__( self ):
        self.challenge_type = ChallengeType.STATE

    def score_guess( self, is_in_country: bool, distance_km: float, threshold_km: float ):
        from services.scoring_utils import ScoringResult
        score = 100 if is_in_country else 0
        zone  = "inside" if is_in_country else "outside"
        return ScoringResult(
            score        = score,
            scoring_zone = zone,
            threshold_km = 0.0,
            is_correct   = is_in_country,
        )

    def to_dict( self ) -> Dict[ str, Any ]:
        d = super().to_dict()
        d[ 'state_code' ] = self.state_code
        return d

    @classmethod
    def from_dict( cls, data: Dict[ str, Any ] ) -> 'StateChallenge':
        return cls(
            id              = data[ 'id' ],
            location_name   = data[ 'location_name' ],
            latitude        = data[ 'latitude' ],
            longitude       = data[ 'longitude' ],
            country         = data[ 'country' ],
            continent       = data[ 'continent' ],
            difficulty      = DifficultyLevel( data[ 'difficulty' ] ),
            hints           = data.get( 'hints', [] ),
            max_distance_km = data.get( 'max_distance_km', 1000 ),
            state_code      = data.get( 'state_code', '' ),
        )
