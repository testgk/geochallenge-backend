"""
Challenges service for managing geographic challenges.
Single source of truth for game logic - used by ALL interfaces (web, desktop, mobile).
"""

import math
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from entities.challenge import Challenge, DifficultyLevel
from db.repositories.challenge_repository import ChallengeRepository
from db.repositories.country_repository import CountryRepository
from db.repositories.difficulty_level_repository import DifficultyLevelRepository
from services.boundary_service import get_boundary_service


# Caches - loaded from database on first access
_country_areas_cache: Optional[Dict[str, float]] = None
_difficulty_levels_cache: Optional[Dict[str, Dict]] = None

# =============================================================================
# SCORING ZONE CONFIGURATION - Single source of truth for ALL interfaces
# =============================================================================
# Both backend scoring and visual display (web, desktop) derive from this.
# Bigger score = thinner ring zone.
# Score is fixed per zone, not based on exact distance within zone.

SCORING_ZONES = [
    {"inner": 0.00, "outer": 0.10, "color": "green",  "label": "Perfect", "score": 100},  # Best
    {"inner": 0.10, "outer": 0.30, "color": "yellow", "label": "Great",   "score": 75},   # Good
    {"inner": 0.30, "outer": 0.60, "color": "orange", "label": "Good",    "score": 50},   # OK
    {"inner": 0.60, "outer": 1.00, "color": "red",    "label": "Close",   "score": 25},   # Worst
]


def get_scoring_zones_config() -> List[Dict[str, Any]]:
    """
    Get the scoring zone configuration.
    This is THE single source of truth for zone boundaries.
    """
    return SCORING_ZONES


# =============================================================================
# CORE SCORING LOGIC - Used by ALL interfaces
# =============================================================================

def calculate_score(distance_km: float, threshold_km: float) -> int:
    """
    THE scoring function. Takes distance and threshold, returns score 0-100.
    Score is based on which ZONE you land in, not exact distance.
    All distances within the same zone get the same score.
    """
    if distance_km > threshold_km:
        return 0
    if distance_km <= 0:
        return 100
    
    # Find which zone the distance falls into
    fraction = distance_km / threshold_km
    for zone in SCORING_ZONES:
        if zone["inner"] <= fraction < zone["outer"]:
            return zone["score"]
    
    return 0  # Outside all zones


def get_scoring_zone(distance_km: float, threshold_km: float) -> str:
    """Determine which scoring zone a distance falls into."""
    if distance_km > threshold_km:
        return "miss"
    
    fraction = distance_km / threshold_km
    for zone in SCORING_ZONES:
        if zone["inner"] <= fraction < zone["outer"]:
            return zone["color"]
    return "red"  # Edge case at exactly threshold


def _get_country_areas() -> Dict[str, float]:
    """
    Get country areas from database cache, loading on first access.
    Falls back to default value if database not available.
    """
    global _country_areas_cache
    if _country_areas_cache is None:
        try:
            repo = CountryRepository()
            _country_areas_cache = repo.get_all_areas()
            print(f"Loaded {len(_country_areas_cache)} country areas from database")
        except Exception as e:
            print(f"Warning: Could not load country areas from database: {e}")
            _country_areas_cache = {}
    return _country_areas_cache


def _get_difficulty_levels() -> Dict[str, Dict]:
    """
    Get difficulty level configs from database cache, loading on first access.
    Falls back to default values if database not available.
    """
    global _difficulty_levels_cache
    if _difficulty_levels_cache is None:
        try:
            repo = DifficultyLevelRepository()
            _difficulty_levels_cache = repo.get_all_as_dict()
            print(f"Loaded {len(_difficulty_levels_cache)} difficulty levels from database")
        except Exception as e:
            print(f"Warning: Could not load difficulty levels from database: {e}")
            # Fallback defaults
            _difficulty_levels_cache = {
                'easy': {'threshold_multiplier': 2.0, 'max_distance_km': 10000},
                'medium': {'threshold_multiplier': 1.4, 'max_distance_km': 5000},
                'hard': {'threshold_multiplier': 1.0, 'max_distance_km': 2500},
                'expert': {'threshold_multiplier': 0.65, 'max_distance_km': 1000},
            }
    return _difficulty_levels_cache


def get_threshold_km(country: str, difficulty: DifficultyLevel) -> float:
    """
    Calculate threshold based on country size and difficulty.
    Larger countries = larger threshold = more forgiving.
    """
    BASE_THRESHOLD_KM = 600.0   # Minimum threshold - increased for easier scoring
    MAX_THRESHOLD_KM = 1100.0   # Maximum threshold cap - increased for easier scoring
    
    difficulty_levels = _get_difficulty_levels()
    difficulty_config = difficulty_levels.get(difficulty.value, {})
    multiplier = difficulty_config.get('threshold_multiplier', 1.0)
    
    country_areas = _get_country_areas()
    area_km2 = country_areas.get(country, 500_000)
    country_km = math.sqrt(area_km2) * multiplier
    
    return min(MAX_THRESHOLD_KM, max(BASE_THRESHOLD_KM, country_km))


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km."""
    EARTH_RADIUS_KM = 6371
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class GuessResult:
    """Result of a guess submission."""
    challenge_id: str
    guessed_lat: float
    guessed_lng: float
    actual_lat: float
    actual_lng: float
    distance_km: float
    threshold_km: float
    score: int  # 0-100
    scoring_zone: str
    is_correct: bool


class ChallengesService:
    """
    Service for managing challenges and calculating results.
    All scoring uses the core functions above.
    Loads challenge data from database on initialization.
    """
    
    def __init__(self):
        self._challenges = self._load_challenges_from_db()
        self._challenges_by_id = {c.id: c for c in self._challenges}
        self._challenges_by_difficulty = self._group_by_difficulty()
    
    def _load_challenges_from_db(self) -> List[Challenge]:
        """Load challenges from database."""
        try:
            repo = ChallengeRepository()
            challenges = repo.get_all()
            print(f"Loaded {len(challenges)} challenges from database")
            return challenges
        except Exception as e:
            print(f"Warning: Could not load challenges from database: {e}")
            return []
    
    def get_all_challenges(self) -> List[Challenge]:
        return self._challenges
    
    def get_challenge_by_id(self, challenge_id: str) -> Optional[Challenge]:
        return self._challenges_by_id.get(challenge_id)
    
    def get_challenges_by_difficulty(self, difficulty: str) -> List[Challenge]:
        try:
            level = DifficultyLevel(difficulty.lower())
            return self._challenges_by_difficulty.get(level, [])
        except ValueError:
            return []
    
    def get_random_challenge(
        self, 
        difficulty: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[Challenge]:
        exclude_ids = exclude_ids or []
        
        if difficulty and difficulty.lower() != 'random':
            challenges = self.get_challenges_by_difficulty(difficulty)
        else:
            challenges = self._challenges
        
        available = [c for c in challenges if c.id not in exclude_ids]
        return random.choice(available) if available else None
    
    def calculate_guess_result(
        self,
        challenge_id: str,
        guessed_lat: float,
        guessed_lng: float
    ) -> Optional[GuessResult]:
        """Calculate result using the core scoring functions."""
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            return None
        
        # Calculate distance
        distance_km = haversine_distance(
            guessed_lat, guessed_lng,
            challenge.latitude, challenge.longitude
        )
        
        # Get threshold for this country/difficulty
        threshold_km = get_threshold_km(challenge.country, challenge.difficulty)
        
        # Check if the guessed point is within the country's boundaries
        boundary_service = get_boundary_service()
        is_in_country = boundary_service.is_point_in_country(
            lat=guessed_lat,
            lng=guessed_lng,
            country_name=challenge.country
        )
        
        # Calculate score - 0 if outside country boundaries
        if is_in_country:
            score = calculate_score(distance_km, threshold_km)
        else:
            score = 0
        
        # Get scoring zone
        zone = get_scoring_zone(distance_km, threshold_km)
        
        return GuessResult(
            challenge_id=challenge_id,
            guessed_lat=guessed_lat,
            guessed_lng=guessed_lng,
            actual_lat=challenge.latitude,
            actual_lng=challenge.longitude,
            distance_km=round(distance_km, 2),
            threshold_km=round(threshold_km, 2),
            score=score,
            scoring_zone=zone if is_in_country else "outside",
            is_correct=(distance_km <= threshold_km and is_in_country)
        )
    
    def get_scoring_zones_for_challenge(self, challenge_id: str) -> Optional[List[Dict]]:
        """Get scoring zone data for visual ring display."""
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            return None
        
        threshold = get_threshold_km(challenge.country, challenge.difficulty)
        
        return [
            {
                "inner_fraction": zone["inner"],
                "outer_fraction": zone["outer"],
                "color": zone["color"],
                "label": zone["label"],
                "inner_km": threshold * zone["inner"],
                "outer_km": threshold * zone["outer"],
            }
            for zone in SCORING_ZONES
        ]
    
    def _group_by_difficulty(self) -> Dict[DifficultyLevel, List[Challenge]]:
        """Group challenges by difficulty level."""
        grouped = {level: [] for level in DifficultyLevel}
        for challenge in self._challenges:
            grouped[challenge.difficulty].append(challenge)
        return grouped


# Singleton instance
_challenges_service: Optional[ChallengesService] = None


def get_challenges_service() -> ChallengesService:
    """Get the singleton challenges service instance."""
    global _challenges_service
    if _challenges_service is None:
        _challenges_service = ChallengesService()
    return _challenges_service
