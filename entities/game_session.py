"""
Game session entity for tracking individual game instances.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from entities.base import BaseEntity


class GameStatus(Enum):
    """Game session status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GameMode(Enum):
    """Available game modes."""
    CLASSIC = "classic"
    TIME_ATTACK = "time_attack"
    CHALLENGE = "challenge"
    MULTIPLAYER = "multiplayer"


@dataclass
class GameSessionEntity(BaseEntity):
    """
    Game session entity representing a single game instance.
    Maps to the 'game_sessions' table in the database.
    """
    user_id: int = 0
    game_mode: GameMode = GameMode.CLASSIC
    status: GameStatus = GameStatus.PENDING
    score: int = 0
    rounds_played: int = 0
    total_rounds: int = 5
    total_distance_error: float = 0.0
    avg_response_time: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    difficulty: str = "medium"

    @classmethod
    def table_name(cls) -> str:
        return "game_sessions"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_mode': self.game_mode.value,
            'status': self.status.value,
            'score': self.score,
            'rounds_played': self.rounds_played,
            'total_rounds': self.total_rounds,
            'total_distance_error': self.total_distance_error,
            'avg_response_time': self.avg_response_time,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'difficulty': self.difficulty,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSessionEntity':
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            game_mode=GameMode(data.get('game_mode', 'classic')),
            status=GameStatus(data.get('status', 'pending')),
            score=data.get('score', 0),
            rounds_played=data.get('rounds_played', 0),
            total_rounds=data.get('total_rounds', 5),
            total_distance_error=data.get('total_distance_error', 0.0),
            avg_response_time=data.get('avg_response_time', 0.0),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            difficulty=data.get('difficulty', 'medium'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def is_active(self) -> bool:
        """Check if game session is currently active."""
        return self.status in (GameStatus.PENDING, GameStatus.IN_PROGRESS)

    def is_finished(self) -> bool:
        """Check if game session has ended."""
        return self.status in (GameStatus.COMPLETED, GameStatus.ABANDONED)

    def calculate_accuracy(self) -> float:
        """Calculate accuracy percentage based on distance errors."""
        if self.rounds_played == 0:
            return 0.0
        # Lower distance error = higher accuracy
        avg_error = self.total_distance_error / self.rounds_played
        # Assume max acceptable error is 5000 km
        accuracy = max(0, 100 - (avg_error / 50))
        return round(accuracy, 2)

    def __repr__(self) -> str:
        return f"GameSessionEntity(id={self.id}, user_id={self.user_id}, mode={self.game_mode.value}, score={self.score})"
