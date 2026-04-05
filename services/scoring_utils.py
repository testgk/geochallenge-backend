"""
Pure scoring utility functions.
Used by challenge entities and the challenges service.
No database access — pure calculation only.
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Any


# =============================================================================
# SCORING ZONE CONFIGURATION
# =============================================================================

SCORING_ZONES = [
    { "inner": 0.00, "outer": 0.10, "color": "green",  "label": "Perfect", "score": 100 },
    { "inner": 0.10, "outer": 0.30, "color": "yellow", "label": "Great",   "score": 75  },
    { "inner": 0.30, "outer": 0.60, "color": "orange", "label": "Good",    "score": 50  },
    { "inner": 0.60, "outer": 1.00, "color": "red",    "label": "Close",   "score": 25  },
]


def get_scoring_zones_config() -> List[ Dict[ str, Any ] ]:
    return SCORING_ZONES


# =============================================================================
# SCORING CONSTANTS
# =============================================================================

INSIDE_COUNTRY_BONUS = 10

DIFFICULTY_MULTIPLIERS = {
    'easy':   1.0,
    'medium': 1.2,
    'hard':   1.5,
    'expert': 2.0,
}


# =============================================================================
# PURE FUNCTIONS
# =============================================================================

def haversine_distance( lat1: float, lon1: float, lat2: float, lon2: float ) -> float:
    """Great-circle distance between two points in km."""
    EARTH_RADIUS_KM = 6371

    lat1_rad = math.radians( lat1 )
    lat2_rad = math.radians( lat2 )
    delta_lat = math.radians( lat2 - lat1 )
    delta_lon = math.radians( lon2 - lon1 )

    a = ( math.sin( delta_lat / 2 ) ** 2 +
          math.cos( lat1_rad ) * math.cos( lat2_rad ) *
          math.sin( delta_lon / 2 ) ** 2 )
    c = 2 * math.atan2( math.sqrt( a ), math.sqrt( 1 - a ) )

    return EARTH_RADIUS_KM * c


def calculate_score( distance_km: float, threshold_km: float,
                     is_in_country: bool = True, difficulty: str = 'medium' ) -> int:
    """Distance-based score 0-100+bonus for city challenges."""
    if not is_in_country:
        return 0

    multiplier = DIFFICULTY_MULTIPLIERS.get( difficulty.lower(), 1.0 )

    if distance_km > threshold_km:
        return int( INSIDE_COUNTRY_BONUS * multiplier )

    if distance_km <= 0:
        return int( ( 100 + INSIDE_COUNTRY_BONUS ) * multiplier )

    fraction   = distance_km / threshold_km
    base_score = int( 100 * math.exp( -3 * fraction ) )
    return int( ( base_score + INSIDE_COUNTRY_BONUS ) * multiplier )


def get_scoring_zone( distance_km: float, threshold_km: float ) -> str:
    """Return the colour-zone name for a given distance."""
    if distance_km > threshold_km:
        return "miss"
    fraction = distance_km / threshold_km
    for zone in SCORING_ZONES:
        if zone[ "inner" ] <= fraction < zone[ "outer" ]:
            return zone[ "color" ]
    return "red"


# =============================================================================
# RESULT DATACLASS
# =============================================================================

@dataclass
class ScoringResult:
    """Outcome of scoring a single guess, returned by challenge.score_guess()."""
    score:        int
    scoring_zone: str
    threshold_km: float
    is_correct:   bool
