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


class ChallengeTypeEnum( str, Enum ):
    """Challenge types."""
    CITY    = "city"
    COUNTRY = "country"


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

class CityChallengeResponse(BaseModel):
    """Response for a single city challenge."""
    id: str
    location_name: str
    latitude: float
    longitude: float
    country: str
    continent: str
    difficulty: str
    hints: List[ str ]
    max_distance_km: float
    challenge_type: str = "city"


class CountryChallengeResponse(BaseModel):
    """Response for a single country challenge."""
    id: str
    location_name: str
    country: str
    continent: str
    difficulty: str
    hints: List[ str ]
    challenge_type: str = "country"
    state_code: Optional[ str ] = None


# Generic response used by the mixed /api/challenges endpoints
class ChallengeResponse(BaseModel):
    """Response for a single challenge (any type)."""
    id: str
    location_name: str
    country: str
    continent: str
    difficulty: str
    hints: List[ str ]
    challenge_type: str              = "city"
    latitude:        Optional[ float ] = None
    longitude:       Optional[ float ] = None
    max_distance_km: Optional[ float ] = None
    state_code:      Optional[ str ]   = None


class CityChallengeListResponse(BaseModel):
    """List of city challenges."""
    challenges: List[ CityChallengeResponse ]
    total: int


class CountryChallengeListResponse(BaseModel):
    """List of country challenges."""
    challenges: List[ CountryChallengeResponse ]
    total: int


class ChallengeListResponse(BaseModel):
    """List of challenges (any type)."""
    challenges: List[ ChallengeResponse ]
    total: int


class CreateChallengeRequest( BaseModel ):
    """Request to create a new challenge."""
    id:              Optional[ str ]             = Field( default = None, description = "Custom ID (auto-generated from location+country if omitted)" )
    location_name:   str                         = Field( ..., description = "Display name of the location" )
    country:         str
    continent:       str
    difficulty:      DifficultyEnum
    challenge_type:  ChallengeTypeEnum           = ChallengeTypeEnum.CITY
    latitude:        Optional[ float ]           = Field( default = None, ge = -90,  le = 90  )
    longitude:       Optional[ float ]           = Field( default = None, ge = -180, le = 180 )
    max_distance_km: Optional[ float ]           = Field( default = None, gt = 0 )
    state_code:      Optional[ str ]             = None
    hints:           List[ str ]                 = Field( default_factory = list )


class UpdateChallengeRequest( BaseModel ):
    """Request to update an existing challenge."""
    location_name:   Optional[ str ]             = None
    latitude:        Optional[ float ]            = Field( default = None, ge = -90,  le = 90  )
    longitude:       Optional[ float ]            = Field( default = None, ge = -180, le = 180 )
    country:         Optional[ str ]             = None
    continent:       Optional[ str ]             = None
    difficulty:      Optional[ DifficultyEnum ]  = None
    max_distance_km: Optional[ float ]            = Field( default = None, gt = 0 )
    challenge_type:  Optional[ ChallengeTypeEnum ] = None
    state_code:      Optional[ str ]             = None
    hints:           Optional[ List[ str ] ]      = None


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
    actual_lat: Optional[ float ] = None
    actual_lng: Optional[ float ] = None
    distance_km: float
    threshold_km: float
    score: int  # 0-100, THE score
    scoring_zone: str
    is_correct: bool

    def __str__( self ) -> str:
        result  = "correct" if self.is_correct else "wrong"
        actual  = f"({self.actual_lat:.4f}, {self.actual_lng:.4f})" if self.actual_lat is not None else "n/a"
        return (
            f"GuessResult[ {self.challenge_id} | {result} | "
            f"score={self.score} | dist={self.distance_km:.1f}km / {self.threshold_km:.1f}km | "
            f"zone={self.scoring_zone} | "
            f"guessed=({self.guessed_lat:.4f}, {self.guessed_lng:.4f}) "
            f"actual={actual} ]"
        )


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
