"""
Challenge entity for geographic challenges.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any


class DifficultyLevel(Enum):
    """Challenge difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class Challenge:
    """
    Geographic challenge entity.
    """
    id: str
    location_name: str
    latitude: float
    longitude: float
    country: str
    continent: str
    difficulty: DifficultyLevel
    hints: List[str]
    max_distance_km: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'location_name': self.location_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'country': self.country,
            'continent': self.continent,
            'difficulty': self.difficulty.value,
            'hints': self.hints,
            'max_distance_km': self.max_distance_km
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Challenge':
        return cls(
            id=data['id'],
            location_name=data['location_name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            country=data['country'],
            continent=data['continent'],
            difficulty=DifficultyLevel(data['difficulty']),
            hints=data.get('hints', []),
            max_distance_km=data.get('max_distance_km', 1000)
        )
