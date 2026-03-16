"""
Challenge repository for database operations.
"""

from typing import Optional, List, Dict

from db.connection import get_db_connection
from entities.challenge import Challenge, DifficultyLevel


class ChallengeRepository:
    """Repository for Challenge database operations."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get_all(self) -> List[Challenge]:
        """Get all challenges with their hints."""
        query = """
            SELECT c.id, c.location_name, c.latitude, c.longitude, 
                   c.country, c.continent, c.difficulty, c.max_distance_km,
                   COALESCE(
                       array_agg(h.hint_text ORDER BY h.hint_order) 
                       FILTER (WHERE h.hint_text IS NOT NULL), 
                       ARRAY[]::text[]
                   ) as hints
            FROM challenges c
            LEFT JOIN challenge_hints h ON c.id = h.challenge_id
            GROUP BY c.id, c.location_name, c.latitude, c.longitude, 
                     c.country, c.continent, c.difficulty, c.max_distance_km
            ORDER BY c.location_name
        """
        results = self.db.execute(query)
        return [self._row_to_entity(row) for row in results]
    
    def get_by_id(self, challenge_id: str) -> Optional[Challenge]:
        """Get a challenge by ID."""
        query = """
            SELECT c.id, c.location_name, c.latitude, c.longitude, 
                   c.country, c.continent, c.difficulty, c.max_distance_km,
                   COALESCE(
                       array_agg(h.hint_text ORDER BY h.hint_order) 
                       FILTER (WHERE h.hint_text IS NOT NULL), 
                       ARRAY[]::text[]
                   ) as hints
            FROM challenges c
            LEFT JOIN challenge_hints h ON c.id = h.challenge_id
            WHERE c.id = %s
            GROUP BY c.id, c.location_name, c.latitude, c.longitude, 
                     c.country, c.continent, c.difficulty, c.max_distance_km
        """
        result = self.db.execute_one(query, (challenge_id,))
        return self._row_to_entity(result) if result else None
    
    def get_by_difficulty(self, difficulty: DifficultyLevel) -> List[Challenge]:
        """Get all challenges for a specific difficulty level."""
        query = """
            SELECT c.id, c.location_name, c.latitude, c.longitude, 
                   c.country, c.continent, c.difficulty, c.max_distance_km,
                   COALESCE(
                       array_agg(h.hint_text ORDER BY h.hint_order) 
                       FILTER (WHERE h.hint_text IS NOT NULL), 
                       ARRAY[]::text[]
                   ) as hints
            FROM challenges c
            LEFT JOIN challenge_hints h ON c.id = h.challenge_id
            WHERE c.difficulty = %s
            GROUP BY c.id, c.location_name, c.latitude, c.longitude, 
                     c.country, c.continent, c.difficulty, c.max_distance_km
            ORDER BY c.location_name
        """
        results = self.db.execute(query, (difficulty.value,))
        return [self._row_to_entity(row) for row in results]
    
    def _row_to_entity(self, row: Dict) -> Challenge:
        """Convert a database row to a Challenge entity."""
        return Challenge(
            id=row['id'],
            location_name=row['location_name'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            country=row['country'],
            continent=row['continent'],
            difficulty=DifficultyLevel(row['difficulty']),
            hints=list(row['hints']) if row['hints'] else [],
            max_distance_km=float(row['max_distance_km'])
        )
