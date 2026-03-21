"""
Database entities package.
Contains domain entities that map to database tables.
"""

from entities.base import BaseEntity
from entities.game_session import GameSessionEntity
from entities.score import ScoreEntity

__all__ = [
    'BaseEntity',
    'GameSessionEntity',
    'ScoreEntity'
]
