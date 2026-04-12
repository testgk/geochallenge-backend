"""
Repository for country challenge database operations.
Reads from country_challenges / country_challenge_hints tables.
"""

from typing import Optional, List, Dict, Any
from entities.challenge import Challenge, ChallengeType, DifficultyLevel, CountryChallenge
from ..connection import get_db_connection

_SELECT = """
    SELECT cc.id, cc.location_name,
           cc.country, cc.continent, cc.difficulty,
           cc.state_code,
           COALESCE(
               array_agg( h.hint_text ORDER BY h.hint_order )
               FILTER ( WHERE h.hint_text IS NOT NULL ),
               ARRAY[]::text[]
           ) AS hints
    FROM country_challenges cc
    LEFT JOIN country_challenge_hints h ON cc.id = h.challenge_id
"""

_GROUP = """
    GROUP BY cc.id, cc.location_name,
             cc.country, cc.continent, cc.difficulty,
             cc.state_code
"""


class CountryChallengeRepository:
    """Repository for CountryChallenge database operations."""

    def __init__( self ):
        self.db = get_db_connection()

    def get_all( self ) -> List[ Challenge ]:
        """Get all country challenges with their hints."""
        query = f"{ _SELECT } { _GROUP } ORDER BY cc.location_name"
        results = self.db.execute( query )
        return [ self._row_to_entity( row ) for row in results ]

    def get_by_id( self, challenge_id: str ) -> Optional[ Challenge ]:
        """Get a country challenge by ID."""
        query = f"{ _SELECT } WHERE cc.id = %s { _GROUP }"
        result = self.db.execute_one( query, ( challenge_id, ) )
        return self._row_to_entity( result ) if result else None

    def get_by_difficulty( self, difficulty: DifficultyLevel ) -> List[ Challenge ]:
        """Get all country challenges for a difficulty level."""
        query = f"{ _SELECT } WHERE cc.difficulty = %s { _GROUP } ORDER BY cc.location_name"
        results = self.db.execute( query, ( difficulty.value, ) )
        return [ self._row_to_entity( row ) for row in results ]

    def insert( self, data: Dict[ str, Any ] ) -> Challenge:
        """Insert a new country challenge and its hints."""
        hints = data.pop( 'hints', [] )

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO country_challenges
                        ( id, location_name, country, continent, difficulty, state_code )
                    VALUES ( %s, %s, %s, %s, %s, %s )
                    """,
                    (
                        data[ 'id' ],
                        data[ 'location_name' ],
                        data[ 'country' ],
                        data[ 'continent' ],
                        data[ 'difficulty' ],
                        data.get( 'state_code' ),
                    )
                )
                for i, hint_text in enumerate( hints ):
                    cur.execute(
                        "INSERT INTO country_challenge_hints ( challenge_id, hint_text, hint_order ) VALUES ( %s, %s, %s )",
                        ( data[ 'id' ], hint_text, i )
                    )

        return self.get_by_id( data[ 'id' ] )

    def update( self, challenge_id: str, data: Dict[ str, Any ] ) -> Optional[ Challenge ]:
        """Update a country challenge's fields."""
        hints = data.pop( 'hints', None )

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                if data:
                    set_parts = [ f"{ col } = %s" for col in data.keys() ]
                    values    = list( data.values() ) + [ challenge_id ]
                    cur.execute(
                        f"UPDATE country_challenges SET { ', '.join( set_parts ) } WHERE id = %s",
                        tuple( values )
                    )
                if hints is not None:
                    cur.execute(
                        "DELETE FROM country_challenge_hints WHERE challenge_id = %s",
                        ( challenge_id, )
                    )
                    for i, hint_text in enumerate( hints ):
                        cur.execute(
                            "INSERT INTO country_challenge_hints ( challenge_id, hint_text, hint_order ) VALUES ( %s, %s, %s )",
                            ( challenge_id, hint_text, i )
                        )

        return self.get_by_id( challenge_id )

    def _row_to_entity( self, row: Dict ) -> CountryChallenge:
        return CountryChallenge(
            id            = row[ 'id' ],
            location_name = row[ 'location_name' ],
            country       = row[ 'country' ],
            continent     = row[ 'continent' ],
            difficulty    = DifficultyLevel( row[ 'difficulty' ] ),
            hints         = list( row[ 'hints' ] ) if row[ 'hints' ] else [],
            state_code    = row.get( 'state_code' ) or '',
        )
