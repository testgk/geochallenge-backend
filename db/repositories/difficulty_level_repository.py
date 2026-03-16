"""
Difficulty level repository for database operations.
"""

from typing import Optional, List, Dict

from db.connection import get_db_connection


class DifficultyLevelRepository:
    """Repository for DifficultyLevel database operations."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get_all(self) -> List[Dict]:
        """Get all difficulty levels ordered by display_order."""
        query = """
            SELECT id, display_name, threshold_multiplier, max_distance_km, 
                   display_order, description
            FROM difficulty_levels
            ORDER BY display_order
        """
        return self.db.execute(query)
    
    def get_all_as_dict(self) -> Dict[str, Dict]:
        """Get all difficulty levels as a dictionary (id -> config)."""
        results = self.get_all()
        return {
            row['id']: {
                'display_name': row['display_name'],
                'threshold_multiplier': float(row['threshold_multiplier']),
                'max_distance_km': int(row['max_distance_km']),
                'display_order': row['display_order'],
                'description': row['description']
            }
            for row in results
        }
    
    def get_by_id(self, difficulty_id: str) -> Optional[Dict]:
        """Get a difficulty level by ID."""
        query = """
            SELECT id, display_name, threshold_multiplier, max_distance_km, 
                   display_order, description
            FROM difficulty_levels
            WHERE id = %s
        """
        return self.db.execute_one(query, (difficulty_id,))
    
    def get_multiplier(self, difficulty_id: str) -> Optional[float]:
        """Get the threshold multiplier for a difficulty level."""
        query = """
            SELECT threshold_multiplier
            FROM difficulty_levels
            WHERE id = %s
        """
        result = self.db.execute_one(query, (difficulty_id,))
        return float(result['threshold_multiplier']) if result else None
    
    def get_max_distance(self, difficulty_id: str) -> Optional[int]:
        """Get the max_distance_km for a difficulty level."""
        query = """
            SELECT max_distance_km
            FROM difficulty_levels
            WHERE id = %s
        """
        result = self.db.execute_one(query, (difficulty_id,))
        return int(result['max_distance_km']) if result else None
