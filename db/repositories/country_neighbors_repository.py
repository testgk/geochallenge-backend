"""
Repository for country neighbor relationships.
"""

from typing import List
from ..connection import get_db_connection


class CountryNeighborsRepository:

    def __init__( self ):
        self.db = get_db_connection()

    def get_neighbors( self, challenge_id: str ) -> List[ str ]:
        """Return neighbor country names for a given country challenge id."""
        rows = self.db.execute(
            "SELECT neighbor_name FROM country_neighbors WHERE country_id = %s ORDER BY neighbor_name",
            ( challenge_id, )
        )
        return [ row[ "neighbor_name" ] for row in rows ]
