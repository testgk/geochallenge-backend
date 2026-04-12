#!/usr/bin/env python3
"""
Script to load state/province boundary data from Natural Earth GeoJSON into the database.
Downloads the 10m resolution admin-1 states/provinces dataset and populates the
state_boundaries table.

Usage:
    python scripts/load_state_boundaries.py

    # With custom database URL:
    DATABASE_URL=postgresql://user:pass@host/db python scripts/load_state_boundaries.py

    # Filter to a single country (ISO alpha-2):
    COUNTRY_FILTER=US python scripts/load_state_boundaries.py
"""

import json
import os
import sys
import urllib.request
import ssl

sys.path.insert( 0, os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) ) )

import psycopg2
from psycopg2.extras import Json


GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
    "/master/geojson/ne_10m_admin_1_states_provinces.geojson"
)


def get_db_connection():
    database_url = os.environ.get( "DATABASE_URL" )
    if database_url:
        return psycopg2.connect( database_url )
    return psycopg2.connect(
        host     = os.environ.get( "DB_HOST",     "localhost" ),
        port     = os.environ.get( "DB_PORT",     "5432" ),
        database = os.environ.get( "DB_NAME",     "geochallenge_dev" ),
        user     = os.environ.get( "DB_USER",     "geochallenge" ),
        password = os.environ.get( "DB_PASSWORD", "geochallenge_secret" ),
    )


def download_geojson():
    print( f"Downloading GeoJSON from {GEOJSON_URL}..." )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    try:
        with urllib.request.urlopen( GEOJSON_URL, context = ctx, timeout = 120 ) as response:
            return json.loads( response.read().decode( "utf-8" ) )
    except Exception as e:
        print( f"Error downloading GeoJSON: {e}" )
        return None


def calculate_bbox( geometry ):
    coords = []

    def extract( obj ):
        if isinstance( obj, list ):
            if len( obj ) >= 2 and isinstance( obj[ 0 ], ( int, float ) ):
                coords.append( obj[ :2 ] )
            else:
                for item in obj:
                    extract( item )

    extract( geometry.get( "coordinates", [] ) )
    if not coords:
        return None
    lngs = [ c[ 0 ] for c in coords ]
    lats = [ c[ 1 ] for c in coords ]
    return [ min( lngs ), min( lats ), max( lngs ), max( lats ) ]


def load_boundaries( geojson_data, country_filter = None ):
    conn   = get_db_connection()
    cursor = conn.cursor()

    features = geojson_data.get( "features", [] )
    print( f"Processing {len( features )} state/province features..." )

    loaded  = 0
    skipped = 0

    for feature in features:
        props    = feature.get( "properties", {} ) or {}
        geometry = feature.get( "geometry" )

        if not geometry:
            skipped += 1
            continue

        # ISO 3166-2 code  e.g. "US-CA"
        iso_3166_2 = ( props.get( "iso_3166_2" ) or "" ).strip()
        # country alpha-2  e.g. "US"
        country_code = (
            props.get( "iso_a2" ) or
            props.get( "adm0_a2" ) or
            ""
        ).strip()
        state_name = (
            props.get( "name" ) or
            props.get( "NAME" ) or
            props.get( "gn_name" ) or
            ""
        ).strip()

        # Skip rows without a proper ISO 3166-2 code
        if not iso_3166_2 or iso_3166_2 == "-99" or "-" not in iso_3166_2:
            skipped += 1
            continue

        if country_filter and country_code.upper() != country_filter.upper():
            skipped += 1
            continue

        bbox = calculate_bbox( geometry )

        try:
            cursor.execute(
                """
                INSERT INTO state_boundaries ( state_code, state_name, country_code, geometry, bbox )
                VALUES ( %s, %s, %s, %s, %s )
                ON CONFLICT ( state_code ) DO UPDATE
                    SET state_name   = EXCLUDED.state_name,
                        country_code = EXCLUDED.country_code,
                        geometry     = EXCLUDED.geometry,
                        bbox         = EXCLUDED.bbox
                """,
                (
                    iso_3166_2,
                    state_name,
                    country_code,
                    Json( geometry ),
                    Json( bbox ) if bbox else None,
                )
            )
            loaded += 1
        except Exception as e:
            print( f"Error loading {iso_3166_2} ({state_name}): {e}" )
            skipped += 1

    conn.commit()
    cursor.close()
    conn.close()

    print( f"Loaded {loaded} states/provinces, skipped {skipped}" )
    return loaded


def main():
    country_filter = os.environ.get( "COUNTRY_FILTER" )
    if country_filter:
        print( f"Filtering to country: {country_filter}" )

    geojson_data = download_geojson()
    if not geojson_data:
        print( "Failed to download GeoJSON data" )
        sys.exit( 1 )

    loaded = load_boundaries( geojson_data, country_filter )
    if loaded == 0:
        print( "No boundaries were loaded" )
        sys.exit( 1 )
    print( f"Successfully loaded {loaded} state/province boundaries" )


if __name__ == "__main__":
    main()
