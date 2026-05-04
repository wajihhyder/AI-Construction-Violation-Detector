from fastapi import APIRouter, Query

from services.geocoding_service import reverse_geocode_district

router = APIRouter(prefix="/api/geocoding", tags=["geocoding"])


@router.get("/reverse")
@router.get("/lookup")
async def reverse(lat: float = Query(...), lng: float = Query(...)):
    """GPS → district + town (Karachi admin map) with optional Geoapify fallback. Same as `/lookup`."""
    return await reverse_geocode_district(lat, lng)
