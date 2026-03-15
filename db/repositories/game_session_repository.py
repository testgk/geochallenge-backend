"""
Game session repository for database operations.
"""

from datetime import datetime
from typing import Optional, List

from db.connection import get_db_connection
from entities.game_session import GameSessionEntity, GameStatus, GameMode


class GameSessionRepository:
    """Repository for GameSession database operations."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create(self, user_id: int, game_mode: GameMode = GameMode.CLASSIC, 
               difficulty: str = "medium", total_rounds: int = 5) -> GameSessionEntity:
        """Create a new game session."""
        query = """
            INSERT INTO game_sessions (user_id, game_mode, status, difficulty, total_rounds, started_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        result = self.db.execute_one(query, (
            user_id, 
            game_mode.value, 
            GameStatus.IN_PROGRESS.value,
            difficulty,
            total_rounds,
            datetime.now()
        ))
        return self._row_to_entity(result)
    
    def get_by_id(self, session_id: int) -> Optional[GameSessionEntity]:
        """Get a game session by ID."""
        query = "SELECT * FROM game_sessions WHERE id = %s"
        result = self.db.execute_one(query, (session_id,))
        return self._row_to_entity(result) if result else None
    
    def get_active_session(self, user_id: int) -> Optional[GameSessionEntity]:
        """Get the active game session for a user."""
        query = """
            SELECT * FROM game_sessions 
            WHERE user_id = %s AND status IN ('pending', 'in_progress')
            ORDER BY created_at DESC LIMIT 1
        """
        result = self.db.execute_one(query, (user_id,))
        return self._row_to_entity(result) if result else None
    
    def get_user_sessions(self, user_id: int, limit: int = 20) -> List[GameSessionEntity]:
        """Get recent game sessions for a user."""
        query = """
            SELECT * FROM game_sessions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        results = self.db.execute(query, (user_id, limit))
        return [self._row_to_entity(row) for row in results]
    
    def update_progress(self, session_id: int, score: int, rounds_played: int,
                        distance_error: float, response_time: float) -> Optional[GameSessionEntity]:
        """Update game session progress after a round."""
        # Get current session to calculate new totals
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        new_total_error = session.total_distance_error + distance_error
        # Calculate running average response time
        total_time = session.avg_response_time * session.rounds_played + response_time
        new_avg_time = total_time / (session.rounds_played + 1) if session.rounds_played >= 0 else response_time
        
        query = """
            UPDATE game_sessions 
            SET score = %s, 
                rounds_played = %s, 
                total_distance_error = %s,
                avg_response_time = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
        """
        result = self.db.execute_one(query, (
            score, rounds_played, new_total_error, new_avg_time, session_id
        ))
        return self._row_to_entity(result) if result else None
    
    def complete_session(self, session_id: int, final_score: int) -> Optional[GameSessionEntity]:
        """Mark a game session as completed."""
        query = """
            UPDATE game_sessions 
            SET status = %s, 
                score = %s,
                completed_at = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
        """
        result = self.db.execute_one(query, (
            GameStatus.COMPLETED.value,
            final_score,
            datetime.now(),
            session_id
        ))
        return self._row_to_entity(result) if result else None
    
    def abandon_session(self, session_id: int) -> Optional[GameSessionEntity]:
        """Mark a game session as abandoned."""
        query = """
            UPDATE game_sessions 
            SET status = %s, 
                completed_at = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
        """
        result = self.db.execute_one(query, (
            GameStatus.ABANDONED.value,
            datetime.now(),
            session_id
        ))
        return self._row_to_entity(result) if result else None
    
    def get_high_scores(self, game_mode: GameMode = None, limit: int = 10) -> List[GameSessionEntity]:
        """Get top completed game sessions by score."""
        if game_mode:
            query = """
                SELECT * FROM game_sessions 
                WHERE status = 'completed' AND game_mode = %s
                ORDER BY score DESC 
                LIMIT %s
            """
            results = self.db.execute(query, (game_mode.value, limit))
        else:
            query = """
                SELECT * FROM game_sessions 
                WHERE status = 'completed'
                ORDER BY score DESC 
                LIMIT %s
            """
            results = self.db.execute(query, (limit,))
        return [self._row_to_entity(row) for row in results]
    
    @staticmethod
    def _row_to_entity(row: dict) -> GameSessionEntity:
        """Convert a database row to a GameSessionEntity."""
        return GameSessionEntity(
            id=row['id'],
            user_id=row['user_id'],
            game_mode=GameMode(row['game_mode']),
            status=GameStatus(row['status']),
            score=row['score'],
            rounds_played=row['rounds_played'],
            total_rounds=row['total_rounds'],
            total_distance_error=row['total_distance_error'],
            avg_response_time=row['avg_response_time'],
            difficulty=row['difficulty'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
