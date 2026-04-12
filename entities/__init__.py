"""
Database entities package.
Contains domain entities that map to database tables.
"""

from .game_session import GameSessionEntity, GameMode, GameStatus
from .score import ScoreEntity
from .challenge import CityChallenge,Challenge,CountryChallenge,ChallengeType,DifficultyLevel
from .base import BaseEntity

__all__ = [
    'BaseEntity',
    'GameSessionEntity',
    'ScoreEntity',
    'ChallengeType',
    'Challenge',
    'CountryChallenge',
    'CityChallenge',
    'DifficultyLevel',
    'GameStatus',
    'GameMode'
]
