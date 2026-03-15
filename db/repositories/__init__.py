"""Database repositories package."""

from db.repositories.game_session_repository import GameSessionRepository
from db.repositories.score_repository import ScoreRepository

__all__ = ['GameSessionRepository', 'ScoreRepository']
