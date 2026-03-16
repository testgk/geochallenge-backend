"""
Country repository for database operations.
"""

from typing import Optional, List, Dict

from db.connection import get_db_connection


class CountryRepository:
    """Repository for Country database operations."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get_all(self) -> List[Dict]:
        """Get all countries."""
        query = """
            SELECT id, name, area_km2, continent
            FROM countries
            ORDER BY name
        """
        return self.db.execute(query)
    
    def get_all_areas(self) -> Dict[str, float]:
        """Get all country areas as a dictionary (name -> area_km2)."""
        query = """
            SELECT name, area_km2
            FROM countries
        """
        results = self.db.execute(query)
        return {row['name']: float(row['area_km2']) for row in results}
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get a country by name."""
        query = """
            SELECT id, name, area_km2, continent
            FROM countries
            WHERE name = %s
        """
        return self.db.execute_one(query, (name,))
    
    def get_area(self, country_name: str) -> Optional[float]:
        """Get the area of a country by name."""
        query = """
            SELECT area_km2
            FROM countries
            WHERE name = %s
        """
        result = self.db.execute_one(query, (country_name,))
        return float(result['area_km2']) if result else None
