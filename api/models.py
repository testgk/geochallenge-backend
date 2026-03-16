"""
Pydantic models for API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


# ============== Enums ==============

class GameModeEnum(str, Enum):
    """Available game modes."""
    CLASSIC = "classic"
    TIME_ATTACK = "time_attack"
    CHALLENGE = "challenge"
    MULTIPLAYER = "multiplayer"


class GameStatusEnum(str, Enum):
    """Game session status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DifficultyEnum(str, Enum):
    """Game difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class LeaderboardPeriodEnum(str, Enum):
    """Leaderboard time periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    ALL_TIME = "all_time"


# ============== Game Session Models ==============

class StartGameRequest(BaseModel):
    """Request to start a new game session."""
    user_id: int = Field(..., description="ID of the player")
    game_mode: GameModeEnum = Field(default=GameModeEnum.CLASSIC, description="Game mode")
    difficulty: DifficultyEnum = Field(default=DifficultyEnum.MEDIUM, description="Difficulty level")
    total_rounds: int = Field(default=5, ge=1, le=20, description="Number of rounds")


class SubmitRoundRequest(BaseModel):
    """Request to submit a round result."""
    distance_error_km: float = Field(..., ge=0, description="Distance from correct location in km")
    response_time_seconds: float = Field(..., ge=0, description="Time taken to answer in seconds")


class RoundResultResponse(BaseModel):
    """Response for a submitted round."""
    round_number: int
    distance_error_km: float
    response_time_seconds: float
    points_earned: int
    accuracy_percent: float
    total_score: int


class GameSessionResponse(BaseModel):
    """Response for game session data."""
    id: int
    user_id: int
    game_mode: str
    status: str
    score: int
    rounds_played: int
    total_rounds: int
    total_distance_error: float
    avg_response_time: float
    difficulty: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class GameResultResponse(BaseModel):
    """Response for completed game result."""
    session_id: int
    user_id: int
    final_score: int
    rounds_played: int
    total_distance_error: float
    avg_response_time: float
    accuracy: float
    grade: str
    is_personal_best: bool
    rank: Optional[int] = None


# ============== Score/Leaderboard Models ==============

class LeaderboardEntry(BaseModel):
    """A single entry in the leaderboard."""
    rank: int
    user_id: int
    username: Optional[str] = None
    display_name: Optional[str] = None
    points: int
    accuracy: float
    game_mode: str
    achieved_at: Optional[datetime] = None


class LeaderboardResponse(BaseModel):
    """Leaderboard response with entries."""
    game_mode: str
    period: str
    entries: List[LeaderboardEntry]
    total_entries: int


class UserStatsResponse(BaseModel):
    """User statistics response."""
    user_id: int
    games_played: int
    total_score: int
    best_score: int
    avg_score: float
    avg_accuracy: float
    best_rank: Optional[int] = None


class ScoreEntryResponse(BaseModel):
    """Response for a single score entry."""
    id: int
    user_id: int
    game_session_id: Optional[int] = None
    points: int
    game_mode: str
    difficulty: str
    accuracy: float
    avg_time_per_round: float
    rank: Optional[int] = None
    achieved_at: Optional[datetime] = None


# ============== Challenge Models ==============

class ChallengeResponse(BaseModel):
    """Response for a single challenge."""
    id: str
    location_name: str
    latitude: float
    longitude: float
    country: str
    continent: str
    difficulty: str
    hints: List[str]
    max_distance_km: float


class ChallengeListResponse(BaseModel):
    """List of challenges response."""
    challenges: List[ChallengeResponse]
    total: int


class GuessRequest(BaseModel):
    """Request to submit a guess for a challenge."""
    challenge_id: str = Field(..., description="ID of the challenge")
    guessed_lat: float = Field(..., ge=-90, le=90, description="Guessed latitude")
    guessed_lng: float = Field(..., ge=-180, le=180, description="Guessed longitude")


class GuessResultResponse(BaseModel):
    """Response for a guess submission."""
    challenge_id: str
    guessed_lat: float
    guessed_lng: float
    actual_lat: float
    actual_lng: float
    distance_km: float
    threshold_km: float
    score: int  # 0-100, THE score
    scoring_zone: str
    is_correct: bool


class ScoringZone(BaseModel):
    """A scoring zone for ring display."""
    inner_fraction: float
    outer_fraction: float
    color: str
    inner_km: float
    outer_km: float


class ScoringZonesResponse(BaseModel):
    """Scoring zones for a challenge."""
    challenge_id: str
    threshold_km: float
    zones: List[ScoringZone]


# ============== Common Response Models ==============

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
