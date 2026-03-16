"""
Boundary service for checking if a point is within a country's borders.
Uses ray casting algorithm for point-in-polygon testing.
"""

from typing import Optional, List, Tuple, Dict, Any
from db.connection import get_db_connection


class BoundaryService:
    """Service for country boundary checking."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def is_point_in_country(self, lat: float, lng: float, country_name: str) -> bool:
        """
        Check if a point (lat, lng) is within a country's boundaries.
        
        Args:
            lat: Latitude of the point
            lng: Longitude of the point
            country_name: Name of the country to check against
            
        Returns:
            True if point is within country boundaries, False otherwise
        """
        geometry = self._get_country_geometry(country_name)
        if not geometry:
            # If no boundary data, assume valid (fallback to distance-only scoring)
            return True
        
        return self._point_in_geometry(lng, lat, geometry)
    
    def _get_country_geometry(self, country_name: str) -> Optional[Dict[str, Any]]:
        """Get the GeoJSON geometry for a country."""
        # Try exact match first
        row = self.db.execute_one(
            "SELECT geometry FROM country_boundaries WHERE LOWER(country_name) = LOWER(%s)",
            (country_name,)
        )
        if row:
            return row['geometry']
        
        # Try partial match
        row = self.db.execute_one(
            "SELECT geometry FROM country_boundaries WHERE LOWER(country_name) LIKE LOWER(%s)",
            (f"%{country_name}%",)
        )
        return row['geometry'] if row else None
    
    def get_country_boundary(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the full GeoJSON boundary for a country (for frontend display).
        
        Returns:
            GeoJSON Feature with geometry and properties
        """
        # Try exact match first
        row = self.db.execute_one(
            """SELECT country_name, country_code, geometry, bbox 
               FROM country_boundaries 
               WHERE LOWER(country_name) = LOWER(%s)""",
            (country_name,)
        )
        if not row:
            # Try partial match
            row = self.db.execute_one(
                """SELECT country_name, country_code, geometry, bbox 
                   FROM country_boundaries 
                   WHERE LOWER(country_name) LIKE LOWER(%s)""",
                (f"%{country_name}%",)
            )
        
        if row:
            return {
                "type": "Feature",
                "properties": {
                    "name": row['country_name'],
                    "code": row['country_code'],
                    "bbox": row['bbox']
                },
                "geometry": row['geometry']
            }
        return None
    
    def _point_in_geometry(self, x: float, y: float, geometry: Dict[str, Any]) -> bool:
        """
        Check if point (x=lng, y=lat) is inside a GeoJSON geometry.
        Handles both Polygon and MultiPolygon types.
        """
        geom_type = geometry.get("type", "")
        coords = geometry.get("coordinates", [])
        
        if geom_type == "Polygon":
            return self._point_in_polygon(x, y, coords)
        elif geom_type == "MultiPolygon":
            return self._point_in_multipolygon(x, y, coords)
        
        return False
    
    def _point_in_polygon(self, x: float, y: float, coords: List) -> bool:
        """
        Check if point is inside a polygon using ray casting algorithm.
        
        coords format: [exterior_ring, hole1, hole2, ...]
        Each ring is a list of [lng, lat] coordinates.
        """
        if not coords:
            return False
        
        # Check exterior ring
        exterior = coords[0]
        if not self._point_in_ring(x, y, exterior):
            return False
        
        # Check if point is in any hole (interior rings)
        for hole in coords[1:]:
            if self._point_in_ring(x, y, hole):
                return False
        
        return True
    
    def _point_in_multipolygon(self, x: float, y: float, coords: List) -> bool:
        """Check if point is inside any polygon of a MultiPolygon."""
        for polygon_coords in coords:
            if self._point_in_polygon(x, y, polygon_coords):
                return True
        return False
    
    def _point_in_ring(self, x: float, y: float, ring: List[List[float]]) -> bool:
        """
        Ray casting algorithm: cast a ray from point to the right,
        count how many times it crosses the polygon boundary.
        Odd = inside, Even = outside.
        """
        n = len(ring)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            
            # Check if the ray crosses this edge
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    def get_all_boundaries_for_countries(self, country_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get boundaries for multiple countries at once.
        Used to preload boundaries for all challenge countries.
        """
        result = {}
        for name in country_names:
            boundary = self.get_country_boundary(name)
            if boundary:
                result[name] = boundary
        return result


# Singleton instance
_boundary_service: Optional[BoundaryService] = None


def get_boundary_service() -> BoundaryService:
    """Get or create the boundary service singleton."""
    global _boundary_service
    if _boundary_service is None:
        _boundary_service = BoundaryService()
    return _boundary_service
