"""
Scoring service for game score management.
Provides high-level API for the game to manage scores.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime
import math

from db.connection import get_db_connection
from db.repositories.game_session_repository import GameSessionRepository
from db.repositories.score_repository import ScoreRepository
from entities.game_session import GameSessionEntity, GameMode, GameStatus
from entities.score import ScoreEntity, ScoreType


@dataclass
class RoundResult:
    """Result of a single game round."""
    round_number: int
    distance_error_km: float
    response_time_seconds: float
    points_earned: int
    accuracy_percent: float
    total_score: int
    

@dataclass
class GameResult:
    """Final result of a completed game."""
    session_id: int
    user_id: int
    final_score: int
    rounds_played: int
    total_distance_error: float
    avg_response_time: float
    accuracy: float
    grade: str
    is_personal_best: bool
    rank: Optional[int]


class ScoringService:
    """
    Service for managing game scoring.
    
    Usage:
        scoring = ScoringService()
        
        # Start a new game
        session = scoring.start_game(user_id=1, game_mode=GameMode.CLASSIC)
        
        # After each round
        result = scoring.submit_round(
            session_id=session.id,
            distance_error_km=150.5,
            response_time_seconds=8.3
        )
        
        # End the game
        final = scoring.end_game(session.id)
    """
    
    # Scoring constants
    MAX_POINTS_PER_ROUND = 5000
    PERFECT_DISTANCE_THRESHOLD = 10  # km - get max points within this distance
    MAX_DISTANCE_FOR_POINTS = 5000   # km - no points beyond this
    TIME_BONUS_THRESHOLD = 5         # seconds - bonus for quick answers
    TIME_BONUS_MAX = 500             # max bonus points for fast answer
    
    # Difficulty multipliers
    DIFFICULTY_MULTIPLIERS = {
        'easy': 0.8,
        'medium': 1.0,
        'hard': 1.3,
        'expert': 1.5
    }
    
    def __init__(self):
        self.db = get_db_connection()
        self.session_repo = GameSessionRepository()
        self.score_repo = ScoreRepository()
    
    def start_game(self, user_id: int, game_mode: GameMode = GameMode.CLASSIC,
                   difficulty: str = "medium", total_rounds: int = 5) -> GameSessionEntity:
        """
        Start a new game session.
        
        Args:
            user_id: ID of the player
            game_mode: Game mode to play
            difficulty: Difficulty level
            total_rounds: Number of rounds in the game
            
        Returns:
            New GameSessionEntity
        """
        # Check for existing active session
        active = self.session_repo.get_active_session(user_id)
        if active:
            # Abandon the old session
            self.session_repo.abandon_session(active.id)
        
        return self.session_repo.create(
            user_id=user_id,
            game_mode=game_mode,
            difficulty=difficulty,
            total_rounds=total_rounds
        )
    
    def submit_round(self, session_id: int, distance_error_km: float,
                     response_time_seconds: float) -> Optional[RoundResult]:
        """
        Submit a round result and calculate points.
        
        Args:
            session_id: Current game session ID
            distance_error_km: Distance from correct location in kilometers
            response_time_seconds: Time taken to answer in seconds
            
        Returns:
            RoundResult with points earned and updated totals
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or not session.is_active():
            return None
        
        # Calculate points for this round
        points, accuracy = self._calculate_round_score(
            distance_error_km, 
            response_time_seconds,
            session.difficulty
        )
        
        new_round = session.rounds_played + 1
        new_score = session.score + points
        
        # Update session progress
        updated_session = self.session_repo.update_progress(
            session_id=session_id,
            score=new_score,
            rounds_played=new_round,
            distance_error=distance_error_km,
            response_time=response_time_seconds
        )
        
        return RoundResult(
            round_number=new_round,
            distance_error_km=distance_error_km,
            response_time_seconds=response_time_seconds,
            points_earned=points,
            accuracy_percent=accuracy,
            total_score=new_score
        )
    
    def end_game(self, session_id: int) -> Optional[GameResult]:
        """
        End a game session and record the final score.
        
        Args:
            session_id: Game session to end
            
        Returns:
            GameResult with final stats and rankings
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            return None
        
        # Complete the session
        completed = self.session_repo.complete_session(session_id, session.score)
        if not completed:
            return None
        
        # Calculate final accuracy
        accuracy = self._calculate_accuracy(
            completed.total_distance_error,
            completed.rounds_played
        )
        
        # Record the score
        score_entry = self.score_repo.create(
            user_id=completed.user_id,
            points=completed.score,
            game_mode=completed.game_mode.value,
            difficulty=completed.difficulty,
            accuracy=accuracy,
            avg_time_per_round=completed.avg_response_time,
            game_session_id=session_id,
            score_type=ScoreType.GAME_SCORE
        )
        
        # Check if personal best
        is_personal_best = self._check_personal_best(
            completed.user_id,
            completed.score,
            completed.game_mode.value
        )
        
        # Update user stats
        self._update_user_stats(completed.user_id, completed.score)
        
        # Get rank
        rank = self.score_repo.get_user_rank(completed.user_id, completed.game_mode.value)
        
        return GameResult(
            session_id=session_id,
            user_id=completed.user_id,
            final_score=completed.score,
            rounds_played=completed.rounds_played,
            total_distance_error=completed.total_distance_error,
            avg_response_time=completed.avg_response_time,
            accuracy=accuracy,
            grade=self._calculate_grade(accuracy),
            is_personal_best=is_personal_best,
            rank=rank
        )
    
    def abandon_game(self, session_id: int) -> bool:
        """Abandon an active game session."""
        session = self.session_repo.get_by_id(session_id)
        if session and session.is_active():
            self.session_repo.abandon_session(session_id)
            return True
        return False
    
    def get_active_game(self, user_id: int) -> Optional[GameSessionEntity]:
        """Get the user's active game session if any."""
        return self.session_repo.get_active_session(user_id)
    
    def get_leaderboard(self, game_mode: str = "classic", 
                        period: str = "all_time", limit: int = 50) -> List[dict]:
        """
        Get leaderboard for a game mode.
        
        Args:
            game_mode: Game mode to get leaderboard for
            period: 'daily', 'weekly', or 'all_time'
            limit: Number of entries to return
        """
        if period == "daily":
            return self.score_repo.get_daily_leaderboard(game_mode, limit)
        elif period == "weekly":
            return self.score_repo.get_weekly_leaderboard(game_mode, limit)
        else:
            return self.score_repo.get_leaderboard(game_mode, limit=limit)
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get comprehensive stats for a user."""
        sessions = self.session_repo.get_user_sessions(user_id, limit=100)
        scores = self.score_repo.get_user_scores(user_id, limit=100)
        
        completed_sessions = [s for s in sessions if s.status == GameStatus.COMPLETED]
        
        if not completed_sessions:
            return {
                'games_played': 0,
                'total_score': 0,
                'best_score': 0,
                'avg_score': 0,
                'avg_accuracy': 0,
                'best_rank': None
            }
        
        total_score = sum(s.score for s in completed_sessions)
        best_score = max(s.score for s in completed_sessions)
        avg_score = total_score / len(completed_sessions)
        
        # Calculate average accuracy
        total_accuracy = sum(
            self._calculate_accuracy(s.total_distance_error, s.rounds_played)
            for s in completed_sessions
        )
        avg_accuracy = total_accuracy / len(completed_sessions)
        
        # Get best rank across all modes
        ranks = []
        for mode in GameMode:
            rank = self.score_repo.get_user_rank(user_id, mode.value)
            if rank:
                ranks.append(rank)
        
        return {
            'games_played': len(completed_sessions),
            'total_score': total_score,
            'best_score': best_score,
            'avg_score': round(avg_score, 1),
            'avg_accuracy': round(avg_accuracy, 1),
            'best_rank': min(ranks) if ranks else None
        }
    
    def _calculate_round_score(self, distance_km: float, time_seconds: float,
                                difficulty: str) -> Tuple[int, float]:
        """
        Calculate score for a single round.
        
        Returns:
            Tuple of (points, accuracy_percentage)
        """
        # Distance-based score (exponential decay)
        if distance_km <= self.PERFECT_DISTANCE_THRESHOLD:
            distance_score = self.MAX_POINTS_PER_ROUND
        elif distance_km >= self.MAX_DISTANCE_FOR_POINTS:
            distance_score = 0
        else:
            # Exponential decay formula
            decay_factor = -math.log(0.01) / self.MAX_DISTANCE_FOR_POINTS
            distance_score = int(self.MAX_POINTS_PER_ROUND * math.exp(-decay_factor * distance_km))
        
        # Time bonus for quick answers
        time_bonus = 0
        if time_seconds < self.TIME_BONUS_THRESHOLD:
            time_factor = 1 - (time_seconds / self.TIME_BONUS_THRESHOLD)
            time_bonus = int(self.TIME_BONUS_MAX * time_factor)
        
        # Apply difficulty multiplier
        multiplier = self.DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
        total_points = int((distance_score + time_bonus) * multiplier)
        
        # Calculate accuracy percentage
        accuracy = max(0, 100 - (distance_km / 50))  # 50km = 1% decrease
        accuracy = min(100, accuracy)
        
        return total_points, round(accuracy, 2)
    
    def _calculate_accuracy(self, total_distance_error: float, rounds_played: int) -> float:
        """Calculate overall accuracy percentage."""
        if rounds_played == 0:
            return 0.0
        avg_error = total_distance_error / rounds_played
        accuracy = max(0, 100 - (avg_error / 50))
        return round(min(100, accuracy), 2)
    
    def _calculate_grade(self, accuracy: float) -> str:
        """Calculate letter grade from accuracy."""
        if accuracy >= 95:
            return "S"
        elif accuracy >= 90:
            return "A"
        elif accuracy >= 80:
            return "B"
        elif accuracy >= 70:
            return "C"
        elif accuracy >= 60:
            return "D"
        return "F"
    
    def _check_personal_best(self, user_id: int, score: int, game_mode: str) -> bool:
        """Check if score is a personal best."""
        best = self.score_repo.get_user_best_score(user_id, game_mode)
        if not best:
            return True
        return score > best.points
    
    def _update_user_stats(self, user_id: int, score: int) -> None:
        """Update user's cumulative stats."""
        query = """
            UPDATE users 
            SET total_score = total_score + %s,
                games_played = games_played + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self.db.execute(query, (score, user_id))


# Singleton instance
_scoring_service: Optional[ScoringService] = None


def get_scoring_service() -> ScoringService:
    """Get the global scoring service instance."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
