"""
Boundaries API routes.
Provides endpoints for country boundary checking and retrieval.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.boundary_service import get_boundary_service

router = APIRouter()


class PointCheckRequest(BaseModel):
    """Request to check if a point is within a country."""
    lat: float
    lng: float
    country_name: str


class PointCheckResponse(BaseModel):
    """Response for point-in-country check."""
    is_inside: bool
    country_name: str


class BoundaryResponse(BaseModel):
    """Response containing country boundary GeoJSON."""
    type: str = "Feature"
    properties: dict
    geometry: dict


@router.post("/check-point", response_model=PointCheckResponse)
async def check_point_in_country(request: PointCheckRequest):
    """
    Check if a point (lat, lng) is within a country's boundaries.
    Returns is_inside=True if the point is within the country borders.
    """
    service = get_boundary_service()
    is_inside = service.is_point_in_country(
        lat=request.lat,
        lng=request.lng,
        country_name=request.country_name
    )
    return PointCheckResponse(
        is_inside=is_inside,
        country_name=request.country_name
    )


@router.get("/country/{country_name}")
async def get_country_boundary(country_name: str):
    """
    Get the GeoJSON boundary for a country.
    Used by frontend to display country borders on the globe.
    """
    service = get_boundary_service()
    boundary = service.get_country_boundary(country_name)
    
    if not boundary:
        raise HTTPException(
            status_code=404,
            detail=f"Boundary not found for country: {country_name}"
        )
    
    return boundary


class MultipleBoundariesRequest(BaseModel):
    """Request for multiple country boundaries."""
    country_names: List[str]


@router.post("/countries")
async def get_multiple_boundaries(request: MultipleBoundariesRequest):
    """
    Get boundaries for multiple countries at once.
    Useful for preloading boundaries for all challenge countries.
    """
    service = get_boundary_service()
    boundaries = service.get_all_boundaries_for_countries(request.country_names)
    return {"boundaries": boundaries}
