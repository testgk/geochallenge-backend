"""
Score repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from db.connection import get_db_connection
from entities.score import ScoreEntity, ScoreType


class ScoreRepository:
    """Repository for Score database operations."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create(self, user_id: int, points: int, game_mode: str = "classic",
               difficulty: str = "medium", accuracy: float = 0.0,
               avg_time_per_round: float = 0.0, game_session_id: int = None,
               score_type: ScoreType = ScoreType.GAME_SCORE) -> ScoreEntity:
        """Create a new score entry."""
        query = """
            INSERT INTO scores (user_id, game_session_id, score_type, points, 
                               game_mode, difficulty, accuracy, avg_time_per_round, achieved_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        result = self.db.execute_one(query, (
            user_id, game_session_id, score_type.value, points,
            game_mode, difficulty, accuracy, avg_time_per_round, datetime.now()
        ))
        return self._row_to_entity(result)
    
    def get_by_id(self, score_id: int) -> Optional[ScoreEntity]:
        """Get a score by ID."""
        query = "SELECT * FROM scores WHERE id = %s"
        result = self.db.execute_one(query, (score_id,))
        return self._row_to_entity(result) if result else None
    
    def get_user_scores(self, user_id: int, limit: int = 50) -> List[ScoreEntity]:
        """Get all scores for a user."""
        query = """
            SELECT * FROM scores 
            WHERE user_id = %s 
            ORDER BY achieved_at DESC 
            LIMIT %s
        """
        results = self.db.execute(query, (user_id, limit))
        return [self._row_to_entity(row) for row in results]
    
    def get_user_best_score(self, user_id: int, game_mode: str = None) -> Optional[ScoreEntity]:
        """Get the user's best score, optionally filtered by game mode."""
        if game_mode:
            query = """
                SELECT * FROM scores 
                WHERE user_id = %s AND game_mode = %s
                ORDER BY points DESC 
                LIMIT 1
            """
            result = self.db.execute_one(query, (user_id, game_mode))
        else:
            query = """
                SELECT * FROM scores 
                WHERE user_id = %s 
                ORDER BY points DESC 
                LIMIT 1
            """
            result = self.db.execute_one(query, (user_id,))
        return self._row_to_entity(result) if result else None
    
    def get_leaderboard(self, game_mode: str = "classic", difficulty: str = None,
                        limit: int = 100) -> List[dict]:
        """
        Get leaderboard with user information.
        Returns list of dicts with score and username.
        """
        if difficulty:
            query = """
                SELECT s.*, u.username, u.display_name
                FROM scores s
                JOIN users u ON s.user_id = u.id
                WHERE s.game_mode = %s AND s.difficulty = %s
                ORDER BY s.points DESC
                LIMIT %s
            """
            results = self.db.execute(query, (game_mode, difficulty, limit))
        else:
            query = """
                SELECT s.*, u.username, u.display_name
                FROM scores s
                JOIN users u ON s.user_id = u.id
                WHERE s.game_mode = %s
                ORDER BY s.points DESC
                LIMIT %s
            """
            results = self.db.execute(query, (game_mode, limit))
        
        leaderboard = []
        for i, row in enumerate(results, 1):
            entry = self._row_to_entity(row)
            leaderboard.append({
                'rank': i,
                'score': entry,
                'username': row['username'],
                'display_name': row.get('display_name') or row['username']
            })
        return leaderboard
    
    def get_daily_leaderboard(self, game_mode: str = "classic", limit: int = 50) -> List[dict]:
        """Get today's leaderboard."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT s.*, u.username, u.display_name
            FROM scores s
            JOIN users u ON s.user_id = u.id
            WHERE s.game_mode = %s AND s.achieved_at >= %s
            ORDER BY s.points DESC
            LIMIT %s
        """
        results = self.db.execute(query, (game_mode, today, limit))
        
        leaderboard = []
        for i, row in enumerate(results, 1):
            entry = self._row_to_entity(row)
            leaderboard.append({
                'rank': i,
                'score': entry,
                'username': row['username'],
                'display_name': row.get('display_name') or row['username']
            })
        return leaderboard
    
    def get_weekly_leaderboard(self, game_mode: str = "classic", limit: int = 50) -> List[dict]:
        """Get this week's leaderboard."""
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT s.*, u.username, u.display_name
            FROM scores s
            JOIN users u ON s.user_id = u.id
            WHERE s.game_mode = %s AND s.achieved_at >= %s
            ORDER BY s.points DESC
            LIMIT %s
        """
        results = self.db.execute(query, (game_mode, week_start, limit))
        
        leaderboard = []
        for i, row in enumerate(results, 1):
            entry = self._row_to_entity(row)
            leaderboard.append({
                'rank': i,
                'score': entry,
                'username': row['username'],
                'display_name': row.get('display_name') or row['username']
            })
        return leaderboard
    
    def get_user_rank(self, user_id: int, game_mode: str = "classic") -> Optional[int]:
        """Get the user's rank on the leaderboard."""
        # Get user's best score
        best = self.get_user_best_score(user_id, game_mode)
        if not best:
            return None
        
        # Count how many scores are higher
        query = """
            SELECT COUNT(DISTINCT user_id) + 1 as rank
            FROM scores
            WHERE game_mode = %s AND points > %s
        """
        result = self.db.execute_one(query, (game_mode, best.points))
        return result['rank'] if result else None
    
    def delete_user_scores(self, user_id: int) -> bool:
        """Delete all scores for a user."""
        query = "DELETE FROM scores WHERE user_id = %s"
        self.db.execute(query, (user_id,))
        return True
    
    @staticmethod
    def _row_to_entity(row: dict) -> ScoreEntity:
        """Convert a database row to a ScoreEntity."""
        return ScoreEntity(
            id=row['id'],
            user_id=row['user_id'],
            game_session_id=row.get('game_session_id'),
            score_type=ScoreType(row['score_type']),
            points=row['points'],
            game_mode=row['game_mode'],
            difficulty=row['difficulty'],
            accuracy=row['accuracy'],
            avg_time_per_round=row['avg_time_per_round'],
            rank=row.get('rank'),
            achieved_at=row['achieved_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
