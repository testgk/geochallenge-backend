"""
Repository for country neighbor relationships.
"""

from typing import List, Optional
from ..connection import get_db_connection


class CountryNeighborsRepository:

    def __init__( self ):
        self.db = get_db_connection()

    def get_neighbors( self, challenge_id: str ) -> List[ str ]:
        """Return up to 6 neighbor names for a country challenge, omitting nulls."""
        row = self.db.execute_one(
            "SELECT neighbor_1, neighbor_2, neighbor_3, neighbor_4, neighbor_5, neighbor_6 "
            "FROM country_neighbors WHERE country_id = %s",
            ( challenge_id, )
        )
        if not row:
            return []
        return [
            row[ col ]
            for col in ( "neighbor_1", "neighbor_2", "neighbor_3", "neighbor_4", "neighbor_5", "neighbor_6" )
            if row[ col ] is not None
        ]
