"""
Score entity for leaderboard and player statistics.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from entities.base import BaseEntity


class ScoreType(Enum):
    """Type of score entry."""
    GAME_SCORE = "game_score"
    DAILY_BEST = "daily_best"
    WEEKLY_BEST = "weekly_best"
    ALL_TIME = "all_time"


@dataclass
class ScoreEntity(BaseEntity):
    """
    Score entity for tracking player scores and leaderboards.
    Maps to the 'scores' table in the database.
    """
    user_id: int = 0
    game_session_id: Optional[int] = None
    score_type: ScoreType = ScoreType.GAME_SCORE
    points: int = 0
    game_mode: str = "classic"
    difficulty: str = "medium"
    accuracy: float = 0.0
    avg_time_per_round: float = 0.0
    rank: Optional[int] = None
    achieved_at: Optional[datetime] = None

    @classmethod
    def table_name(cls) -> str:
        return "scores"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_session_id': self.game_session_id,
            'score_type': self.score_type.value,
            'points': self.points,
            'game_mode': self.game_mode,
            'difficulty': self.difficulty,
            'accuracy': self.accuracy,
            'avg_time_per_round': self.avg_time_per_round,
            'rank': self.rank,
            'achieved_at': self.achieved_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoreEntity':
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            game_session_id=data.get('game_session_id'),
            score_type=ScoreType(data.get('score_type', 'game_score')),
            points=data.get('points', 0),
            game_mode=data.get('game_mode', 'classic'),
            difficulty=data.get('difficulty', 'medium'),
            accuracy=data.get('accuracy', 0.0),
            avg_time_per_round=data.get('avg_time_per_round', 0.0),
            rank=data.get('rank'),
            achieved_at=data.get('achieved_at'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def is_high_score(self, threshold: int = 1000) -> bool:
        """Check if this is considered a high score."""
        return self.points >= threshold

    def get_grade(self) -> str:
        """Get letter grade based on accuracy."""
        if self.accuracy >= 95:
            return "S"
        elif self.accuracy >= 90:
            return "A"
        elif self.accuracy >= 80:
            return "B"
        elif self.accuracy >= 70:
            return "C"
        elif self.accuracy >= 60:
            return "D"
        else:
            return "F"

    def __repr__(self) -> str:
        return f"ScoreEntity(id={self.id}, user_id={self.user_id}, points={self.points}, grade={self.get_grade()})"
