#!/usr/bin/env python3
"""
Script to load country boundary data from Natural Earth GeoJSON into the database.
Downloads the 50m resolution countries dataset and populates the country_boundaries table.

Usage:
    python scripts/load_boundaries.py
    
    # With custom database URL:
    DATABASE_URL=postgresql://user:pass@host/db python scripts/load_boundaries.py
"""

import json
import os
import sys
import urllib.request
import ssl

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import Json


# Natural Earth 50m countries GeoJSON URL
GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"


def get_db_connection():
    """Get database connection from environment or default."""
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        return psycopg2.connect(database_url)
    
    # Default local development connection
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        database=os.environ.get("DB_NAME", "geochallenge"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres")
    )


def download_geojson():
    """Download Natural Earth GeoJSON data."""
    print(f"Downloading GeoJSON from {GEOJSON_URL}...")
    
    # Disable SSL verification (some environments have certificate issues)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(GEOJSON_URL, context=ctx, timeout=60) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"Error downloading GeoJSON: {e}")
        return None


def calculate_bbox(geometry):
    """Calculate bounding box from geometry coordinates."""
    coords = []
    
    def extract_coords(obj):
        if isinstance(obj, list):
            if len(obj) >= 2 and isinstance(obj[0], (int, float)):
                coords.append(obj[:2])
            else:
                for item in obj:
                    extract_coords(item)
    
    extract_coords(geometry.get("coordinates", []))
    
    if not coords:
        return None
    
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    
    return [min(lngs), min(lats), max(lngs), max(lats)]


def load_boundaries(geojson_data):
    """Load boundary data into database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    features = geojson_data.get("features", [])
    print(f"Processing {len(features)} country features...")
    
    loaded = 0
    skipped = 0
    
    for feature in features:
        props = feature.get("properties", {})
        geometry = feature.get("geometry")
        
        if not geometry:
            skipped += 1
            continue
        
        # Get country identifiers - Natural Earth uses various property names
        country_name = (
            props.get("NAME") or 
            props.get("ADMIN") or 
            props.get("SOVEREIGNT") or
            props.get("name") or
            ""
        )
        country_code = (
            props.get("ISO_A3") or 
            props.get("ADM0_A3") or
            props.get("SOV_A3") or
            ""
        )
        
        if not country_name:
            skipped += 1
            continue
        
        # Some codes are -99 for territories, use name-based code
        if country_code == "-99" or not country_code:
            country_code = country_name[:3].upper()
        
        bbox = calculate_bbox(geometry)
        
        try:
            cursor.execute(
                """
                INSERT INTO country_boundaries (country_code, country_name, geometry, bbox)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (country_code) DO UPDATE
                SET country_name = EXCLUDED.country_name,
                    geometry = EXCLUDED.geometry,
                    bbox = EXCLUDED.bbox
                """,
                (country_code, country_name, Json(geometry), Json(bbox) if bbox else None)
            )
            loaded += 1
        except Exception as e:
            print(f"Error loading {country_name}: {e}")
            skipped += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Loaded {loaded} countries, skipped {skipped}")
    return loaded


def main():
    """Main entry point."""
    # Download GeoJSON
    geojson_data = download_geojson()
    if not geojson_data:
        print("Failed to download GeoJSON data")
        sys.exit(1)
    
    # Load into database
    loaded = load_boundaries(geojson_data)
    
    if loaded > 0:
        print(f"Successfully loaded {loaded} country boundaries")
    else:
        print("No boundaries were loaded")
        sys.exit(1)


if __name__ == "__main__":
    main()
