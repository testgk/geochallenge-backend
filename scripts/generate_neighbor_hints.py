#!/usr/bin/env python3
"""
Generate neighbor relationships and hints for country challenges.

For each country in country_challenges:
  1. Find all countries whose boundaries touch or overlap (using shapely).
  2. Insert into country_neighbors table.
  3. Replace existing hints with one hint per neighbor:
       "One of my neighbors is <neighbor_name>"

Usage:
    python scripts/generate_neighbor_hints.py

    # Against a remote DB:
    DATABASE_URL=postgresql://... python scripts/generate_neighbor_hints.py
"""

import json
import os
import sys
import random

sys.path.insert( 0, os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) ) )

import psycopg2
import psycopg2.extras
from shapely.geometry import shape
from shapely.validation import make_valid


def get_db_connection():
    url = os.environ.get( "DATABASE_URL" )
    if url:
        if "sslmode" not in url:
            url += "?sslmode=prefer"
        return psycopg2.connect( url )
    return psycopg2.connect(
        host     = os.environ.get( "DB_HOST",     "localhost" ),
        port     = os.environ.get( "DB_PORT",     "5432" ),
        database = os.environ.get( "DB_NAME",     "geochallenge_dev" ),
        user     = os.environ.get( "DB_USER",     "geochallenge" ),
        password = os.environ.get( "DB_PASSWORD", "" ),
    )


# Map from countries.name → country_boundaries.country_name for known mismatches
_NAME_ALIASES = {
    "United States":  "United States of America",
    "Czech Republic": "Czechia",
    "Bosnia":         "Bosnia and Herz.",
    "East Timor":     "Timor-Leste",
    "UAE":            "United Arab Emirates",
}


def load_boundaries( conn ):
    """Load all country boundaries as shapely geometries keyed by country_name."""
    with conn.cursor( cursor_factory = psycopg2.extras.RealDictCursor ) as cur:
        cur.execute( "SELECT country_name, geometry FROM country_boundaries" )
        rows = cur.fetchall()

    boundaries = {}
    for row in rows:
        try:
            geom = make_valid( shape( row[ "geometry" ] ) )
            boundaries[ row[ "country_name" ] ] = geom
        except Exception as e:
            print( f"  Warning: could not parse geometry for {row['country_name']}: {e}" )
    print( f"Loaded {len( boundaries )} boundary geometries" )
    return boundaries


def resolve_boundary_name( country_name, boundaries ):
    """Return the key in `boundaries` that corresponds to `country_name`, or None."""
    if country_name in boundaries:
        return country_name
    alias = _NAME_ALIASES.get( country_name )
    if alias and alias in boundaries:
        return alias
    return None


def load_country_challenges( conn ):
    """Return list of (id, country) for all country challenges."""
    with conn.cursor( cursor_factory = psycopg2.extras.RealDictCursor ) as cur:
        cur.execute( "SELECT id, country FROM country_challenges ORDER BY country" )
        return cur.fetchall()


def find_neighbors( country_name, boundaries, tolerance = 0.1 ):
    """
    Return list of country names that share a border with country_name.
    Uses a small buffer so countries that nearly-touch are included.
    """
    resolved = resolve_boundary_name( country_name, boundaries )
    if resolved is None:
        return []
    geom = boundaries[ resolved ]

    buffered = geom.buffer( tolerance )
    neighbors = []
    for other_name, other_geom in boundaries.items():
        if other_name == country_name:
            continue
        try:
            if buffered.intersects( other_geom ):
                neighbors.append( other_name )
        except Exception:
            pass
    return neighbors


def save_neighbors_and_hints( conn, challenge_id, country_name, neighbors ):
    """Insert neighbors and replace hints for a country challenge."""
    with conn.cursor() as cur:
        # Clear existing neighbors and hints for this challenge
        cur.execute( "DELETE FROM country_neighbors WHERE country_id = %s", ( challenge_id, ) )
        cur.execute( "DELETE FROM country_challenge_hints WHERE challenge_id = %s", ( challenge_id, ) )

        for neighbor in neighbors:
            cur.execute(
                """
                INSERT INTO country_neighbors ( country_id, neighbor_name )
                VALUES ( %s, %s )
                ON CONFLICT ( country_id, neighbor_name ) DO NOTHING
                """,
                ( challenge_id, neighbor )
            )

        # Create one hint per neighbor: "One of my neighbors is <name>"
        shuffled = list( neighbors )
        random.shuffle( shuffled )
        for i, neighbor in enumerate( shuffled ):
            cur.execute(
                """
                INSERT INTO country_challenge_hints ( challenge_id, hint_text, hint_order )
                VALUES ( %s, %s, %s )
                """,
                ( challenge_id, f"One of my neighbors is {neighbor}", i )
            )


def main():
    conn = get_db_connection()
    conn.autocommit = False

    print( "Loading boundaries..." )
    boundaries = load_boundaries( conn )

    print( "Loading country challenges..." )
    challenges = load_country_challenges( conn )
    print( f"Processing {len( challenges )} challenges..." )

    no_boundary  = []
    no_neighbors = []
    total_hints  = 0

    for ch in challenges:
        challenge_id  = ch[ "id" ]
        country_name  = ch[ "country" ]
        neighbors     = find_neighbors( country_name, boundaries )

        if resolve_boundary_name( country_name, boundaries ) is None:
            no_boundary.append( country_name )
            continue

        if not neighbors:
            no_neighbors.append( country_name )
            save_neighbors_and_hints( conn, challenge_id, country_name, [] )
            continue

        save_neighbors_and_hints( conn, challenge_id, country_name, neighbors )
        total_hints += len( neighbors )
        print( f"  {country_name}: {len( neighbors )} neighbors" )

    conn.commit()
    conn.close()

    print( f"\nDone." )
    print( f"  Total hints inserted : {total_hints}" )
    if no_boundary:
        print( f"  No boundary data     : {', '.join( no_boundary )}" )
    if no_neighbors:
        print( f"  No neighbors found   : {', '.join( no_neighbors )}" )


if __name__ == "__main__":
    main()
